from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

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


# ---------------------------------------------------------------------------
# pre_down_hook / skill-folder discovery
# ---------------------------------------------------------------------------


def test_run_pre_down_hook_returns_empty_when_flag_false(tmp_path: Path) -> None:
    """When pre_down_hook is False, no subprocess runs and [] is returned."""
    repo_path = tmp_path / "gstack"

    manager = SparseCheckoutManager(
        repo_url="https://github.com/garrytan/gstack.git",
        folder_paths=["/docs/"],
        local_storage_path=str(repo_path),
        pre_down_hook=False,
    )

    with patch("subprocess.run") as mock_run:
        result = manager.run_pre_down_hook()

    assert result == []
    mock_run.assert_not_called()


def test_run_pre_down_hook_returns_empty_when_default_branch_unknown(tmp_path: Path) -> None:
    """When pre_down_hook is True but default branch isn't known yet, return []."""
    repo_path = tmp_path / "gstack"

    manager = SparseCheckoutManager(
        repo_url="https://github.com/garrytan/gstack.git",
        folder_paths=["/docs/"],
        local_storage_path=str(repo_path),
        pre_down_hook=True,
    )
    # _default_branch stays None — simulates pre-setup state
    assert manager._default_branch is None

    with patch("subprocess.run") as mock_run:
        result = manager.run_pre_down_hook()

    assert result == []
    mock_run.assert_not_called()


def test_run_pre_down_hook_parses_ls_tree_output(tmp_path: Path) -> None:
    """ls-tree output is parsed into sorted, deduped, normalized folder paths."""
    repo_path = tmp_path / "gstack"

    manager = SparseCheckoutManager(
        repo_url="https://github.com/garrytan/gstack.git",
        folder_paths=["/docs/"],
        local_storage_path=str(repo_path),
        pre_down_hook=True,
    )
    manager._default_branch = "main"

    fake_result = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="review/SKILL.md\nqa/SKILL.md\nqa/extra.md\n"
    )

    with patch("subprocess.run", return_value=fake_result) as mock_run:
        result = manager.run_pre_down_hook()

    assert result == ["/qa", "/review"]
    # Called via /bin/sh -c, in the manager's repo path
    assert mock_run.call_args.args[0][:2] == ["/bin/sh", "-c"]
    assert mock_run.call_args.kwargs["cwd"] == str(repo_path)


def test_run_pre_down_hook_returns_empty_for_non_gstack_url(tmp_path: Path) -> None:
    """pre_down_hook=True on a URL that no strategy matches returns [] silently."""
    repo_path = tmp_path / "superpowers"

    manager = SparseCheckoutManager(
        repo_url="https://github.com/obra/superpowers.git",
        folder_paths=["/skills/"],
        local_storage_path=str(repo_path),
        pre_down_hook=True,
    )
    manager._default_branch = "main"

    with patch("subprocess.run") as mock_run:
        result = manager.run_pre_down_hook()

    assert result == []
    mock_run.assert_not_called()


def test_run_pre_down_hook_handles_ls_tree_failure(tmp_path: Path) -> None:
    """If git ls-tree fails (non-zero exit, exception, or empty output), return []."""
    repo_path = tmp_path / "gstack"

    manager = SparseCheckoutManager(
        repo_url="https://github.com/garrytan/gstack.git",
        folder_paths=["/docs/"],
        local_storage_path=str(repo_path),
        pre_down_hook=True,
    )
    manager._default_branch = "main"

    # Non-zero exit code
    failed = subprocess.CompletedProcess(
        args=[], returncode=128, stdout="", stderr="fatal: bad object"
    )
    with patch("subprocess.run", return_value=failed):
        assert manager.run_pre_down_hook() == []

    # Exception during subprocess
    with patch("subprocess.run", side_effect=OSError("network down")):
        assert manager.run_pre_down_hook() == []

    # Empty stdout (no SKILL.md files)
    empty = subprocess.CompletedProcess(args=[], returncode=0, stdout="")
    with patch("subprocess.run", return_value=empty):
        assert manager.run_pre_down_hook() == []


def test_setup_dedupes_discovered_against_static_paths(tmp_path: Path) -> None:
    """Discovery results are merged with static paths, deduped, in-memory only."""
    repo_path = tmp_path / "gstack"

    manager = SparseCheckoutManager(
        repo_url="https://github.com/garrytan/gstack.git",
        folder_paths=["/docs", "/review"],
        local_storage_path=str(repo_path),
        pre_down_hook=True,
    )
    manager._default_branch = "main"

    fake_result = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="review/SKILL.md\nqa/SKILL.md\n"
    )

    with patch("subprocess.run", return_value=fake_result):
        extra = manager.run_pre_down_hook()
        merged = list(dict.fromkeys([*manager.folder_paths, *extra]))

    assert merged == ["/docs", "/review", "/qa"]


def test_setup_writes_augmented_sparse_checkout_file(tmp_path: Path) -> None:
    """End-to-end: setup() with pre_down_hook writes the union of static + discovered."""
    repo_path = tmp_path / "gstack"
    # Do NOT pre-create repo_path — setup() early-returns if it exists.
    # Because subprocess.run is mocked, simulate `git init` by creating
    # .git/info/ on disk so the sparse-checkout file can be written.
    info_dir = repo_path / ".git" / "info"

    manager = SparseCheckoutManager(
        repo_url="https://github.com/garrytan/gstack.git",
        folder_paths=["/docs/"],
        local_storage_path=str(repo_path),
        pre_down_hook=True,
    )

    discovery_result = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="review/SKILL.md\nqa/SKILL.md\n"
    )

    # Order of subprocess.run calls in setup() (with _detect_default_branch mocked):
    # 0: git init, 1: git remote add, 2: git config, 3: git fetch,
    # 4: discovery (pre_down_hook), 5: git sparse-checkout reapply, 6: git checkout
    call_count = {"n": 0}

    def fake_run(cmd, **kwargs):
        idx = call_count["n"]
        call_count["n"] += 1
        if isinstance(cmd, list) and len(cmd) >= 2 and cmd[0] == "git" and cmd[1] == "init":
            info_dir.mkdir(parents=True, exist_ok=True)
        if idx == 4:
            return discovery_result
        return subprocess.CompletedProcess(
            args=cmd if isinstance(cmd, list) else [str(cmd)],
            returncode=0, stdout="", stderr="",
        )

    with patch.object(
        SparseCheckoutManager, "_detect_default_branch", return_value="main"
    ):
        with patch.object(
            SparseCheckoutManager, "_verify_paths_exist", return_value=None
        ):
            with patch("subprocess.run", side_effect=fake_run):
                manager.setup()

    sparse_path = repo_path / ".git" / "info" / "sparse-checkout"
    contents = sparse_path.read_text().splitlines()
    # Trailing slashes are re-added by the writer
    assert "/docs/" in contents
    assert "/review/" in contents
    assert "/qa/" in contents
    # No accidental duplicates
    assert contents.count("/docs/") == 1
    assert contents.count("/review/") == 1

    sparse_path = repo_path / ".git" / "info" / "sparse-checkout"
    contents = sparse_path.read_text().splitlines()
    # Trailing slashes are re-added by the writer
    assert "/docs/" in contents
    assert "/review/" in contents
    assert "/qa/" in contents
    # No accidental duplicates
    assert contents.count("/docs/") == 1
    assert contents.count("/review/") == 1


@pytest.mark.integration
def test_gstack_includes_skill_folders(tmp_path: Path) -> None:
    """End-to-end integration: real gstack clone materializes review/SKILL.md and docs/."""
    repo_path = tmp_path / "gstack"

    manager = SparseCheckoutManager(
        repo_url="https://github.com/garrytan/gstack.git",
        folder_paths=["/docs/"],
        local_storage_path=str(repo_path),
        pre_down_hook=True,
    )
    manager.setup()

    assert (repo_path / "review" / "SKILL.md").is_file()
    assert (repo_path / "docs").is_dir()
