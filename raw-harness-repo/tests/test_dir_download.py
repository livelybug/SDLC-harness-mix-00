from __future__ import annotations

import importlib.util
import os
from pathlib import Path

_DIR_DOWNLOAD_PATH = Path(__file__).resolve().parent.parent / "src" / "raw_harness" / "dir-download.py"
_spec = importlib.util.spec_from_file_location("dir_download", _DIR_DOWNLOAD_PATH)
_dir_download = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_dir_download)
SparseCheckoutManager = _dir_download.SparseCheckoutManager


def test_setup_materializes_only_requested_folder(tmp_path: Path) -> None:
    """Regression for issue #4: non-cone patterns must not pull siblings/parents."""
    repo_path = tmp_path / "superpowers"

    manager = SparseCheckoutManager(
        repo_url="https://github.com/obra/superpowers.git",
        folder_paths=["skills"],
        local_storage_path=str(repo_path),
    )
    manager.setup()

    materialized = {p.name for p in repo_path.iterdir() if p.name != ".git"}
    assert materialized == {"skills"}, f"Unexpected folders materialized: {materialized}"


def test_setup_strips_trailing_slashes_from_config(tmp_path: Path) -> None:
    """Configs may include trailing slashes (e.g. 'skills/'); setup must still work."""
    repo_path = tmp_path / "superpowers"

    manager = SparseCheckoutManager(
        repo_url="https://github.com/obra/superpowers.git",
        folder_paths=["skills/"],
        local_storage_path=str(repo_path),
    )
    manager.setup()

    assert (repo_path / "skills").is_dir()
    materialized = {p.name for p in repo_path.iterdir() if p.name != ".git"}
    assert materialized == {"skills"}, f"Unexpected folders materialized: {materialized}"


def test_prune_removes_stale_files_and_dirs(tmp_path: Path) -> None:
    """Pruner evicts siblings, dotfiles, and stale loose files outside requested folders."""
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    (repo_path / ".git").mkdir()
    (repo_path / "skills").mkdir()
    (repo_path / "skills" / "keep.md").write_text("keep me")
    (repo_path / "docs").mkdir()
    (repo_path / "docs" / "sub").write_text("delete me")
    (repo_path / "README.md").write_text("stale")
    (repo_path / ".claude").mkdir()

    manager = SparseCheckoutManager(
        repo_url="https://example.com/repo.git",
        folder_paths=["skills"],
        local_storage_path=str(repo_path),
    )
    manager._prune_worktree_to_requested_folders()

    remaining = sorted(p.name for p in repo_path.iterdir())
    assert remaining == [".git", "skills"], f"Unexpected survivors: {remaining}"
    assert (repo_path / "skills" / "keep.md").read_text() == "keep me"


def test_prune_preserves_git_dir_and_requested_folders_with_trailing_slash(tmp_path: Path) -> None:
    """Trailing slashes in folder_paths must not confuse the keep-set."""
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    (repo_path / ".git").mkdir()
    (repo_path / "skills").mkdir()
    (repo_path / "docs").mkdir()

    manager = SparseCheckoutManager(
        repo_url="https://example.com/repo.git",
        folder_paths=["skills/"],
        local_storage_path=str(repo_path),
    )
    manager._prune_worktree_to_requested_folders()

    remaining = {p.name for p in repo_path.iterdir()}
    assert remaining == {".git", "skills"}


def test_prune_keeps_nested_requested_paths(tmp_path: Path) -> None:
    """A requested path like 'src/core/templates/workflows' must keep its parent top-level dir."""
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    (repo_path / ".git").mkdir()
    keep_dir = repo_path / "src" / "core" / "templates" / "workflows"
    keep_dir.mkdir(parents=True)
    (keep_dir / "x.md").write_text("keep")
    (repo_path / "README.md").write_text("stale")
    (repo_path / "docs").mkdir()

    manager = SparseCheckoutManager(
        repo_url="https://example.com/repo.git",
        folder_paths=["src/core/templates/workflows"],
        local_storage_path=str(repo_path),
    )
    manager._prune_worktree_to_requested_folders()

    assert (repo_path / "src" / "core" / "templates" / "workflows" / "x.md").exists()
    assert (repo_path / "src").is_dir()
    assert not (repo_path / "README.md").exists()
    assert not (repo_path / "docs").exists()
    assert (repo_path / ".git").exists()
