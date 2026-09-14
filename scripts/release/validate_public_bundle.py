"""Validate public allowlists, checking legacy and versioned layouts against their manifests."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from functools import lru_cache
from pathlib import Path
from pathlib import PurePosixPath


ALLOWED_ACTIVE_PANELS = {
    "Figure_1": set("abc"),
    "Figure_2": set("abcde"),
    "Figure_3": set("abcdef"),
    "Figure_4": set("abc"),
    "Extended_Data_Figure_1": set("abc"),
    "Extended_Data_Figure_2": set("abcdef"),
    "Extended_Data_Figure_3": set("a"),
    "Extended_Data_Figure_4": set("ab"),
    "Extended_Data_Figure_5": set("abc"),
    "Extended_Data_Figure_6": set("abcd"),
}

ALLOWED_TOP_LEVEL = {
    ".gitignore",
    ".github",
    ".zenodo.json",
    "CITATION.cff",
    "DATA_AVAILABILITY.md",
    "LICENSE",
    "README.md",
    "benchmark",
    "configs",
    "data",
    "figures",
    "pixi.lock",
    "pixi.toml",
    "pytest.ini",
    "reproduce_figures.sh",
    "scripts",
    "source_data",
    "src",
    "tests",
}

MACHINE_PATH_PATTERNS = (
    re.compile(r"/home/[^/\s]+/"),
    re.compile(r"/Users/[^/\s]+/"),
    re.compile(r"/mnt/(?:data|scratch|home)/"),
    re.compile(r"/scratch/"),
    re.compile(r"file://"),
)

TEXT_SUFFIXES = {
    ".cff",
    ".csv",
    ".json",
    ".md",
    ".py",
    ".r",
    ".sh",
    ".svg",
    ".toml",
    ".tsv",
    ".txt",
    ".yaml",
    ".yml",
}

PUBLIC_DOCUMENTS = {
    "docs/CHANGELOG.md",
    "docs/THIRD_PARTY_NOTICES.md",
    "docs/verification/v1.2.1/local_source_verification.json",
    "docs/verification/v1.2.1/github_release_verification.json",
}
RELEASE_INDEXES = {
    "reproducibility/v1.2.0/": "reproducibility/v1.2.0/manifests/file_index.tsv",
}
# Published historical receipts contain machine paths; do not reject or rewrite historical evidence for that alone.
# Allow only specified JSON records matching registered bytes, not executable code, configurations, or arbitrary logs.
HISTORICAL_PATH_RECORDS = {
    f"reproducibility/{version}/provenance/revision_cellot_replay/verification_manifest.json"
    for version in ("v1.2.0",)
} | {
    f"reproducibility/v1.2.0/reports/revision/other_model_training_seeds_v1/cpa/seed{seed}/{context}/completed.json"
    for seed in (123, 124, 125)
    for context in ("HCC38", "HCC1143")
} | {
    f"reproducibility/v1.2.0/reports/revision/other_model_training_seeds_v1/{name}.json"
    for name in ("progress", "training_complete")
}


@lru_cache(maxsize=1)
def release_files() -> dict[str, str]:
    entries = {}
    for prefix, index_path in RELEASE_INDEXES.items():
        with Path(index_path).open(encoding="utf-8") as handle:
            rows = json.load(handle)["files"] if index_path.endswith(".json") else csv.DictReader(handle, delimiter="\t")
            entries.update({prefix + row["path"]: row["sha256"] for row in rows})
    return entries


def tracked_paths() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def validate_path(path_text: str) -> list[str]:
    path = PurePosixPath(path_text)
    errors: list[str] = []
    top_level = path.parts[0] if path.parts else ""

    versioned = any(path_text.startswith(prefix) for prefix in RELEASE_INDEXES)
    if versioned:
        if path_text not in release_files() and path_text not in RELEASE_INDEXES.values():
            errors.append("file is not registered in the versioned public manifest")
    elif path_text not in PUBLIC_DOCUMENTS and top_level not in ALLOWED_TOP_LEVEL:
        errors.append("path is outside the curated public repository layout")
    if top_level in {"manuscript", "reports", "resource_registry", "model_registry"}:
        errors.append("internal analysis or submission material is excluded")
    if any(name in path.name.lower() for name in (
        "manuscript_revision", "response_to_reviewers", "revision_text_en",
        "closure_audit", "reviewer_response_evidence_map",
    )) or any(part in {".env", "private_submission"} for part in path.parts):
        errors.append("private submission or account material is excluded")
    if "caption" in path.name.lower() or "figure_legend" in path.name.lower():
        errors.append("figure captions and manuscript legends are excluded")
    if path.parts[:2] == ("figure_build", "output"):
        errors.append("figure_build/output is a local generated directory")
    if path.suffix.lower() in {".png", ".pdf", ".docx"}:
        errors.append("raster/PDF/DOCX artifacts are excluded")
    if path.parts[:2] == ("data", "predictions"):
        errors.append("model prediction intermediates are excluded")

    if path.parts and path.parts[0] == "figures":
        if path == PurePosixPath("figures/README.md"):
            pass
        elif "panels" not in path.parts:
            errors.append("only panel-level figure files are public")
        elif path.suffix.lower() not in {".svg", ".tsv", ".json"}:
            errors.append("panel files must be SVG, TSV or JSON")
        else:
            figure_group = path.parts[1] if len(path.parts) > 1 else ""
            if figure_group not in ALLOWED_ACTIVE_PANELS:
                errors.append("retired or unknown figure group")
            elif "_panel_" in path.name:
                panel_id = path.name.split("_panel_", 1)[1].split("_", 1)[0].split(".", 1)[0]
                if panel_id not in ALLOWED_ACTIVE_PANELS[figure_group]:
                    errors.append("retired or unknown panel")

    return [f"{path_text}: {message}" for message in errors]


def validate_contents(path_text: str) -> list[str]:
    path = Path(path_text)
    if path_text == "scripts/release/validate_public_bundle.py":
        return []
    errors = []
    declared_hash = release_files().get(path_text)
    if declared_hash is not None:
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != declared_hash:
            return [f"{path_text}: frozen public manifest SHA256 mismatch"]
    if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    for pattern in MACHINE_PATH_PATTERNS:
        match = pattern.search(text)
        if match and not (declared_hash is not None and path_text in HISTORICAL_PATH_RECORDS):
            errors.append(
                f"{path_text}: machine-specific absolute path is forbidden ({match.group(0)})"
            )
    return errors


def main() -> None:
    paths = tracked_paths()
    errors = [error for path in paths for error in validate_path(path)]
    errors.extend(error for path in paths for error in validate_contents(path))
    if errors:
        raise SystemExit("Public release validation failed:\n" + "\n".join(errors))
    print("Public release validation passed.")


if __name__ == "__main__":
    main()
