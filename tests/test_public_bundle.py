"""Validate public manifests, documentation language, and private-file exclusion."""

import hashlib
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("public_bundle", ROOT / "scripts/release/validate_public_bundle.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_public_documents_do_not_use_submission_iteration_labels(monkeypatch):
    monkeypatch.chdir(ROOT)
    pattern = re.compile(r"(?<![A-Za-z0-9])v[456](?![A-Za-z0-9])|\d+\.\d+\.\d+-dev(?:[.\d]+)?")
    for name in MODULE.tracked_paths():
        if name.endswith(".md"):
            assert not pattern.search((ROOT / name).read_text()), name


def test_historical_figures_are_not_presented_as_current_results():
    historical = (ROOT / "figures/README.md").read_text()
    assert historical.startswith("# Historical public figures")
    assert "../reproducibility/v1.2.1/README.md" in historical
    assert "do not represent the formal v1.2.1 results" in historical
    assert "Active figure panels" not in historical
    assert "[Existing SVG figures](figures/README.md)" in (ROOT / "README.md").read_text()


def test_current_reading_guides_are_in_english():
    paths = ["README.md", "DATA_AVAILABILITY.md", "CITATION.cff", ".zenodo.json",
             "docs/CHANGELOG.md", "docs/THIRD_PARTY_NOTICES.md", "figures/README.md",
             "data/reference/gene_sets/axis_annotation/README.md",
             "reproducibility/v1.2.1/README.md", "reproducibility/v1.2.1/docs/README.md",
             "reproducibility/v1.2.1/docs/data_dictionary.md",
             "reproducibility/v1.2.1/provenance/README.md",
             "reproducibility/v1.2.1/training/cellot/docs/README.md"]
    for path in paths:
        assert not re.search(r"[\u4e00-\u9fff]", (ROOT / path).read_text()), path


def test_english_release_preserves_scientific_paths_and_uses_new_downloads():
    metadata = json.loads((ROOT / ".zenodo.json").read_text())
    assert metadata["version"] == "1.2.2"
    assert "version: 1.2.2" in (ROOT / "CITATION.cff").read_text()
    manifest = json.loads((ROOT / "reproducibility/v1.2.1/manifests/archive_assets.json").read_text())
    assert manifest["version"] == "1.2.1" and manifest["distribution_release"] == "v1.2.2"
    for row in manifest["archives"]:
        assert "/download/v1.2.2/" in row["download_url"]
        assert row["path"].startswith("WTShiftBench_v1.2.1_")
    for name in ["README.md", "DATA_AVAILABILITY.md", "reproducibility/v1.2.1/README.md"]:
        text = (ROOT / name).read_text()
        assert "/releases/tag/v1.2.2" in text
        assert "/releases/tag/v1.2.1" not in text


def test_current_and_historical_public_trees_pass(monkeypatch):
    monkeypatch.chdir(ROOT)
    paths = MODULE.tracked_paths()
    assert not [error for path in paths for error in MODULE.validate_path(path)]
    assert not [error for path in paths for error in MODULE.validate_contents(path)]


def test_unlisted_private_and_large_artifacts_remain_excluded():
    for path in (
        "docs/private_note.md", "docs/revision_delivery/Manuscript_revision_clean.docx",
        "reproducibility/v1.2.1/Response_to_reviewers.md",
        "reproducibility/v1.2.1/unlisted.py", "private_submission/reply.md",
        ".env", "figures/Fig1.pdf", "data/predictions/unlisted.tsv",
    ):
        assert MODULE.validate_path(path), path


def test_historical_machine_path_exception_requires_matching_hash(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    relative = sorted(MODULE.HISTORICAL_PATH_RECORDS)[0]
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    original = '{"recorded_path": "' + "/".join(["", "home", "recorded", "run"]) + '"}'
    path.write_text(original)
    monkeypatch.setattr(MODULE, "release_files", lambda: {relative: hashlib.sha256(original.encode()).hexdigest()})
    assert not MODULE.validate_contents(relative)
    path.write_text(original + "\n")
    assert "SHA256 mismatch" in MODULE.validate_contents(relative)[0]


def test_runtime_code_machine_path_is_not_a_historical_exception(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    relative = "reproducibility/v1.2.1/run.py"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    original = 'input_path = "' + "/".join(["", "home", "recorded", "input"]) + '"'
    path.write_text(original)
    monkeypatch.setattr(MODULE, "release_files", lambda: {relative: hashlib.sha256(original.encode()).hexdigest()})
    assert "machine-specific" in MODULE.validate_contents(relative)[0]
