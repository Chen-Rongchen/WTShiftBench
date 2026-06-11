"""Validate the curated public release file set in Git's index.

Local manuscript and build artifacts may remain in the working tree without
entering the public release.
"""

from __future__ import annotations

import subprocess
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

    if top_level not in ALLOWED_TOP_LEVEL:
        errors.append("path is outside the curated public repository layout")
    if top_level in {"manuscript", "reports", "docs", "resource_registry", "model_registry"}:
        errors.append("internal analysis or submission material is excluded")
    if "caption" in path.name.lower() or "figure_legend" in path.name.lower():
        errors.append("figure captions and manuscript legends are excluded")
    if path.parts[:2] == ("figure_build", "output"):
        errors.append("figure_build/output is a local generated directory")
    if path.suffix.lower() in {".png", ".pdf", ".docx"}:
        errors.append("raster/PDF/DOCX artifacts are excluded")
    if path.parts[:2] == ("data", "predictions"):
        errors.append("model prediction intermediates are excluded")

    if path.parts and path.parts[0] == "figures":
        if "panels" not in path.parts:
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


def main() -> None:
    errors = [error for path in tracked_paths() for error in validate_path(path)]
    if errors:
        raise SystemExit("Public release validation failed:\n" + "\n".join(errors))
    print("Public release validation passed.")


if __name__ == "__main__":
    main()
