"""回归检查：版本化公开清单可通过，私有文件和未登记输入仍被拒绝。"""

import hashlib
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("public_bundle", ROOT / "scripts/release/validate_public_bundle.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


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
