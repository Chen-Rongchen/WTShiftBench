#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import json
import os
import re
import subprocess
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urljoin, urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class SupplementaryFile:
    scope: str
    accession: str
    url: str
    local_path: Path


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        for key, value in attrs:
            if key == "href" and value:
                self.hrefs.append(value)


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_config(config_path: Path) -> dict[str, Any]:
    return json.loads(config_path.read_text(encoding="utf-8"))


def accession_bucket(accession: str) -> str:
    match = re.fullmatch(r"([A-Z]+)(\d+)", accession)
    if not match:
        raise ValueError(f"无法解析 accession: {accession}")
    prefix, digits = match.groups()
    return f"{prefix}{digits[:-3]}nnn"


def apply_proxy_env(config: dict[str, Any], env: dict[str, str], *, use_proxy: bool) -> dict[str, str]:
    if not use_proxy:
        for key in ("https_proxy", "http_proxy", "all_proxy", "HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY"):
            env.pop(key, None)
        return env
    proxies = dict(config.get("proxies", {}))
    env.pop("all_proxy", None)
    env.pop("ALL_PROXY", None)
    keys = ["https_proxy", "http_proxy"]
    if bool(proxies.get("use_all_proxy", False)):
        keys.append("all_proxy")
    for key in keys:
        value = proxies.get(key)
        if value:
            env[key] = str(value)
            env[key.upper()] = str(value)
    return env


def run_curl(url: str, output_path: Path, config: dict[str, Any], *, resume: bool) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Convert FTP URLs to HTTPS as HTTP proxy cannot handle FTP protocol
    if url.startswith("ftp://"):
        url = "https://" + url[6:]
    download_cfg = dict(config.get("download", {}))
    command = [
        "curl",
        "-L",
        "--fail",
        "--retry",
        str(download_cfg.get("retry", 3)),
        "--connect-timeout",
        str(download_cfg.get("connect_timeout_seconds", 30)),
    ]
    if resume:
        command.extend(["-C", "-"])
    command.extend(["--output", str(output_path), url])
    download_cfg = dict(config.get("download", {}))
    try:
        subprocess.run(command, check=True, env=apply_proxy_env(config, dict(os.environ), use_proxy=True))
    except subprocess.CalledProcessError:
        if not download_cfg.get("fallback_without_proxy", True):
            raise
        print("[warn] proxy download failed; retry without proxy")
        subprocess.run(command, check=True, env=apply_proxy_env(config, dict(os.environ), use_proxy=False))


def read_text_url(url: str, cache_path: Path, config: dict[str, Any]) -> str:
    run_curl(url, cache_path, config, resume=False)
    return cache_path.read_text(encoding="utf-8", errors="replace")


def download_soft(series_accession: str, output_dir: Path, config: dict[str, Any]) -> Path:
    soft_url = str(
        config.get(
            "soft_url",
            (
                f"https://ftp.ncbi.nlm.nih.gov/geo/series/{accession_bucket(series_accession)}/"
                f"{series_accession}/soft/{series_accession}_family.soft.gz"
            ),
        )
    )
    soft_path = output_dir / "metadata" / f"{series_accession}_family.soft.gz"
    if not soft_path.exists():
        run_curl(soft_url, soft_path, config, resume=True)
    return soft_path


def parse_sample_supplementary(soft_path: Path, output_dir: Path) -> list[SupplementaryFile]:
    records: list[SupplementaryFile] = []
    current_gsm = ""
    with gzip.open(soft_path, "rt", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            if line.startswith("^SAMPLE = "):
                current_gsm = line.split("=", 1)[1].strip()
                continue
            if not current_gsm or not line.startswith("!Sample_supplementary_file"):
                continue
            url = line.split("=", 1)[1].strip()
            if not url or url.upper() == "NONE":
                continue
            filename = unquote(Path(urlparse(url).path).name)
            if not filename:
                continue
            records.append(
                SupplementaryFile(
                    scope="sample",
                    accession=current_gsm,
                    url=url,
                    local_path=output_dir / "samples" / current_gsm / filename,
                )
            )
    return records


def parse_series_supplementary(series_accession: str, output_dir: Path, config: dict[str, Any]) -> list[SupplementaryFile]:
    suppl_url = str(
        config.get(
            "series_suppl_url",
            f"https://ftp.ncbi.nlm.nih.gov/geo/series/{accession_bucket(series_accession)}/{series_accession}/suppl/",
        )
    )
    listing_path = output_dir / "metadata" / f"{series_accession}_series_suppl_listing.html"
    listing = read_text_url(suppl_url, listing_path, config)
    parser = LinkParser()
    parser.feed(listing)

    records: list[SupplementaryFile] = []
    for href in parser.hrefs:
        if href.startswith("?") or href.startswith("/") or href == "../":
            continue
        url = urljoin(suppl_url, href)
        filename = unquote(Path(urlparse(url).path).name)
        if not filename:
            continue
        records.append(
            SupplementaryFile(
                scope="series",
                accession=series_accession,
                url=url,
                local_path=output_dir / "series" / filename,
            )
        )
    return records


def parse_sample_directory(gsm_accession: str, output_dir: Path, config: dict[str, Any]) -> list[SupplementaryFile]:
    suppl_url = (
        f"https://ftp.ncbi.nlm.nih.gov/geo/samples/{accession_bucket(gsm_accession)}/"
        f"{gsm_accession}/suppl/"
    )
    listing_path = output_dir / "metadata" / f"{gsm_accession}_suppl_listing.html"
    listing = read_text_url(suppl_url, listing_path, config)
    parser = LinkParser()
    parser.feed(listing)

    records: list[SupplementaryFile] = []
    for href in parser.hrefs:
        if href.startswith("?") or href.startswith("/") or href == "../":
            continue
        url = urljoin(suppl_url, href)
        filename = unquote(Path(urlparse(url).path).name)
        if not filename:
            continue
        records.append(
            SupplementaryFile(
                scope="sample",
                accession=gsm_accession,
                url=url,
                local_path=output_dir / "samples" / gsm_accession / filename,
            )
        )
    return records


def dedupe_records(records: list[SupplementaryFile]) -> list[SupplementaryFile]:
    seen: set[str] = set()
    unique: list[SupplementaryFile] = []
    for record in records:
        if record.url in seen:
            continue
        seen.add(record.url)
        unique.append(record)
    return unique


def write_manifest(records: list[SupplementaryFile], manifest_path: Path) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["scope", "accession", "url", "local_path", "exists", "bytes"],
            delimiter="\t",
        )
        writer.writeheader()
        for record in records:
            exists = record.local_path.exists()
            writer.writerow(
                {
                    "scope": record.scope,
                    "accession": record.accession,
                    "url": record.url,
                    "local_path": str(record.local_path),
                    "exists": str(exists).lower(),
                    "bytes": record.local_path.stat().st_size if exists else "",
                }
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="下载 GEO series 下的 supplementary 文件。")
    parser.add_argument("--config", required=True, help="下载配置 JSON")
    parser.add_argument("--dry-run", action="store_true", help="只生成 manifest，不下载 supplementary 文件")
    parser.add_argument("--max-files", type=int, default=None, help="最多处理前 N 个文件，用于测试")
    parser.add_argument("--sample-accession", action="append", default=[], help="只解析指定 GSM 的 suppl 目录，可重复传入")
    parser.add_argument("--test-records", action="store_true", help="使用配置中的 test_records，不访问 GEO 元数据")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config_path = resolve_path(args.config)
    config = load_config(config_path)
    series_accession = str(config["series_accession"])
    output_dir = resolve_path(str(config["output_dir"]))
    output_dir.mkdir(parents=True, exist_ok=True)

    records: list[SupplementaryFile] = []
    if args.test_records:
        for item in config.get("test_records", []):
            url = str(item["url"])
            accession = str(item.get("accession", series_accession))
            scope = str(item.get("scope", "sample"))
            filename = unquote(Path(urlparse(url).path).name)
            records.append(
                SupplementaryFile(
                    scope=scope,
                    accession=accession,
                    url=url,
                    local_path=output_dir / "samples" / accession / filename,
                )
            )
        soft_path = None
    elif args.sample_accession:
        for gsm_accession in args.sample_accession:
            records.extend(parse_sample_directory(gsm_accession, output_dir, config))
        soft_path = None
    else:
        soft_path = download_soft(series_accession, output_dir, config)
        if config.get("include_sample_supplementary", True):
            records.extend(parse_sample_supplementary(soft_path, output_dir))
        if config.get("include_series_supplementary", True):
            records.extend(parse_series_supplementary(series_accession, output_dir, config))
    records = dedupe_records(records)
    if args.max_files is not None:
        records = records[: args.max_files]

    if not args.dry_run:
        download_cfg = dict(config.get("download", {}))
        resume = bool(download_cfg.get("resume", True))
        overwrite = bool(download_cfg.get("overwrite", False))
        for record in records:
            if record.local_path.exists() and not overwrite:
                print(f"[skip] {record.local_path}")
                continue
            print(f"[download] {record.url} -> {record.local_path}")
            run_curl(record.url, record.local_path, config, resume=resume)

    manifest_path = resolve_path(str(config["manifest_path"]))
    write_manifest(records, manifest_path)
    if soft_path is not None:
        print(f"[ok] soft     -> {soft_path}")
    print(f"[ok] manifest -> {manifest_path}")
    print(f"[ok] files    -> {len(records)}")


if __name__ == "__main__":
    main()
