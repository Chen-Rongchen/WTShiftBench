"""Validate the curated public release file set.

The validator inspects Git's staged file list. Local manuscript and build
artifacts may remain in the working tree without entering the public release.
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


def staged_paths() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def validate_path(path_text: str) -> list[str]:
    path = PurePosixPath(path_text)
    errors: list[str] = []

    if path.parts and path.parts[0] == "manuscript":
        errors.append("manuscript files are local submission artifacts")
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
    errors = [error for path in staged_paths() for error in validate_path(path)]
    if errors:
        raise SystemExit("Public release validation failed:\n" + "\n".join(errors))
    print("Public release validation passed.")


if __name__ == "__main__":
    main()
