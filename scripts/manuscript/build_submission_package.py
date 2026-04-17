from __future__ import annotations

import argparse
import csv
import json
import zipfile
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

import pandas as pd

from wtbench.manuscript.hash_manifest import git_metadata, sha256_file, utc_now_iso


DEFAULT_CONFIG = Path("configs/manuscript/submission_package_v1.json")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def iter_configured_paths(root: Path, config: dict[str, Any]) -> list[tuple[str, Path]]:
    records: list[tuple[str, Path]] = []
    seen: set[Path] = set()
    for item in config["items"]:
        category = item["category"]
        for rel_path in item.get("paths", []):
            path = root / rel_path
            if not path.exists():
                raise FileNotFoundError(rel_path)
            if path.is_file() and path not in seen:
                records.append((category, path))
                seen.add(path)
        for pattern in item.get("globs", []):
            for path in sorted(root.glob(pattern)):
                if path.is_file() and path not in seen:
                    records.append((category, path))
                    seen.add(path)
    return records


def tsv_shape(path: Path) -> tuple[int | None, int | None]:
    if path.suffix != ".tsv":
        return None, None
    df = pd.read_csv(path, sep="\t")
    return int(df.shape[0]), int(df.shape[1])


def build_file_manifest(root: Path, configured_paths: list[tuple[str, Path]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for category, path in configured_paths:
        n_rows, n_columns = tsv_shape(path)
        rows.append(
            {
                "category": category,
                "path": str(path.relative_to(root)),
                "suffix": path.suffix.lstrip("."),
                "bytes": path.stat().st_size,
                "rows": n_rows,
                "columns": n_columns,
                "sha256": sha256_file(path),
            }
        )
    return pd.DataFrame(rows).sort_values(["category", "path"]).reset_index(drop=True)


def column_name(index: int) -> str:
    name = ""
    while index:
        index, rem = divmod(index - 1, 26)
        name = chr(65 + rem) + name
    return name


def cell_xml(row_idx: int, col_idx: int, value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    ref = f"{column_name(col_idx)}{row_idx}"
    text = escape(str(value))
    return f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>'


def sheet_xml(df: pd.DataFrame) -> str:
    rows: list[str] = []
    header_cells = "".join(cell_xml(1, idx, column) for idx, column in enumerate(df.columns, start=1))
    rows.append(f'<row r="1">{header_cells}</row>')
    for row_idx, row in enumerate(df.itertuples(index=False), start=2):
        cells = "".join(cell_xml(row_idx, col_idx, value) for col_idx, value in enumerate(row, start=1))
        rows.append(f'<row r="{row_idx}">{cells}</row>')
    max_col = max(len(df.columns), 1)
    max_row = max(len(df) + 1, 1)
    dimension = f"A1:{column_name(max_col)}{max_row}"
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<dimension ref="{dimension}"/>'
        '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
        f'<sheetData>{"".join(rows)}</sheetData>'
        f'<autoFilter ref="{dimension}"/>'
        "</worksheet>"
    )


def write_xlsx(path: Path, sheets: list[tuple[str, pd.DataFrame]]) -> None:
    content_type_overrides = [
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    workbook_sheets = []
    workbook_rels = []
    for idx, (name, _df) in enumerate(sheets, start=1):
        content_type_overrides.append(
            f'<Override PartName="/xl/worksheets/sheet{idx}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
        workbook_sheets.append(f'<sheet name="{escape(name)}" sheetId="{idx}" r:id="rId{idx}"/>')
        workbook_rels.append(
            f'<Relationship Id="rId{idx}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{idx}.xml"/>'
        )

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        f'{"".join(content_type_overrides)}'
        "</Types>"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        "</Relationships>"
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets>{"".join(workbook_sheets)}</sheets>'
        "</workbook>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f'{"".join(workbook_rels)}'
        "</Relationships>"
    )
    now = utc_now_iso()
    core = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<dc:creator>WTKO manuscript build_submission_package.py</dc:creator>"
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'
        "</cp:coreProperties>"
    )
    app = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        "<Application>WTKO manuscript package builder</Application>"
        "</Properties>"
    )

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("docProps/core.xml", core)
        zf.writestr("docProps/app.xml", app)
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/_rels/workbook.xml.rels", rels)
        for idx, (_name, df) in enumerate(sheets, start=1):
            zf.writestr(f"xl/worksheets/sheet{idx}.xml", sheet_xml(df))


def read_tsv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t", dtype=object)


def safe_sheet_name(prefix: str, used: set[str]) -> str:
    name = prefix[:31]
    if name not in used:
        used.add(name)
        return name
    for idx in range(1, 1000):
        suffix = f"_{idx}"
        candidate = f"{prefix[: 31 - len(suffix)]}{suffix}"
        if candidate not in used:
            used.add(candidate)
            return candidate
    raise RuntimeError(f"Cannot create unique sheet name for {prefix}")


def write_supplementary_workbook(root: Path, config: dict[str, Any], out_dir: Path) -> tuple[Path, pd.DataFrame]:
    index_path = root / config["supplementary_table_index"]
    summary_path = root / config["supplementary_table_summary"]
    file_index = read_tsv(index_path)
    table_summary = read_tsv(summary_path)

    readme = pd.DataFrame(
        [
            {"field": "generated_at_utc", "value": utc_now_iso()},
            {
                "field": "purpose",
                "value": "Supplementary Tables workbook generated from frozen TSV sources. Non-TSV files remain listed in File_index.",
            },
            {"field": "source_index", "value": config["supplementary_table_index"]},
            {"field": "source_summary", "value": config["supplementary_table_summary"]},
        ]
    )
    used = {"README"}
    sheets: list[tuple[str, pd.DataFrame]] = [
        ("README", readme),
        (safe_sheet_name("Table_summary", used), table_summary),
        (safe_sheet_name("File_index", used), file_index),
    ]

    sheet_records: list[dict[str, Any]] = []
    tsv_rows = file_index[file_index["suffix"] == "tsv"].reset_index(drop=True)
    for idx, row in enumerate(tsv_rows.itertuples(index=False), start=1):
        path = root / str(row.path)
        sheet_name = safe_sheet_name(f"T{idx:02d}", used)
        df = read_tsv(path)
        sheets.append((sheet_name, df))
        sheet_records.append(
            {
                "sheet": sheet_name,
                "table_id": row.table_id,
                "title": row.title,
                "path": row.path,
                "rows": int(df.shape[0]),
                "columns": int(df.shape[1]),
                "sha256": row.sha256,
            }
        )

    sheet_index = pd.DataFrame(sheet_records)
    sheets.append((safe_sheet_name("Sheet_index", used), sheet_index))
    workbook_path = out_dir / config["workbook_name"]
    write_xlsx(workbook_path, sheets)
    return workbook_path, sheet_index


def write_outputs(root: Path, config: dict[str, Any]) -> None:
    out_dir = root / config["output_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    workbook_path, sheet_index = write_supplementary_workbook(root, config, out_dir)
    configured_paths = iter_configured_paths(root, config)
    configured_paths.append(("submission_package", workbook_path))
    manifest_df = build_file_manifest(root, configured_paths)
    manifest_path = out_dir / config["manifest_name"]
    manifest_df.to_csv(manifest_path, sep="\t", index=False, quoting=csv.QUOTE_MINIMAL)

    summary_df = (
        manifest_df.groupby("category", as_index=False)
        .agg(n_files=("path", "count"), total_bytes=("bytes", "sum"), tsv_files=("rows", lambda x: int(x.notna().sum())))
        .sort_values("category")
    )
    summary_path = out_dir / config["summary_name"]
    summary_df.to_csv(summary_path, sep="\t", index=False)

    json_path = out_dir / config["json_name"]
    payload = {
        "generated_at_utc": utc_now_iso(),
        "config": str(DEFAULT_CONFIG),
        "output_dir": config["output_dir"],
        "git": git_metadata(root),
        "outputs": {
            "file_manifest": str(manifest_path.relative_to(root)),
            "summary": str(summary_path.relative_to(root)),
            "supplementary_workbook": str(workbook_path.relative_to(root)),
        },
        "counts": {
            "n_files": int(manifest_df.shape[0]),
            "n_categories": int(manifest_df["category"].nunique()),
            "n_workbook_table_sheets": int(sheet_index.shape[0]),
        },
        "category_summary": summary_df.to_dict(orient="records"),
        "files": manifest_df.to_dict(orient="records"),
        "workbook_sheets": sheet_index.to_dict(orient="records"),
    }
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build manuscript submission package manifest and supplementary workbook.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)
    root = repo_root()
    config = load_config(root / args.config)
    write_outputs(root, config)


if __name__ == "__main__":
    main()
