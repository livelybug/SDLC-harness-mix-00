from __future__ import annotations

import shutil
import tarfile
from pathlib import Path
from unittest.mock import patch

import pytest

from raw_harness.utils import git_archive


@pytest.fixture
def tmp_base_dir(tmp_path: Path) -> Path:
    repos_dir = tmp_path / "repos"
    repos_dir.mkdir()
    tmp_store_dir = tmp_path / ".tmp_store"
    tmp_store_dir.mkdir()
    return tmp_path


@pytest.fixture
def create_git_dirs(tmp_base_dir: Path) -> list[Path]:
    repos_dir = tmp_base_dir / "repos"
    git_dirs: list[Path] = []
    for owner in ["owner1", "owner2"]:
        owner_dir = repos_dir / owner
        owner_dir.mkdir()
        for repo in ["repo1", "repo2"]:
            repo_dir = owner_dir / repo
            repo_dir.mkdir()
            git_dir = repo_dir / ".git"
            git_dir.mkdir()
            git_dirs.append(git_dir)
    return git_dirs


def test_get_base_dir() -> None:
    result = git_archive.get_base_dir()
    assert result == Path(__file__).parent.parent


def test_move_git_folders(tmp_base_dir: Path, create_git_dirs: list[Path]) -> None:
    archive_path = tmp_base_dir / ".tmp_store" / "git-folders.tar.gz"

    with patch.object(git_archive, "get_base_dir", return_value=tmp_base_dir):
        git_archive.move_git_folders()

    assert archive_path.exists()
    with tarfile.open(archive_path, "r:gz") as tar:
        members = tar.getmembers()
        git_members = [m for m in members if ".git" in m.name]
        assert len(git_members) > 0

    for git_dir in create_git_dirs:
        assert not git_dir.exists()


def test_move_git_folders_no_repos(tmp_base_dir: Path) -> None:
    repos_dir = tmp_base_dir / "repos"
    shutil.rmtree(repos_dir)

    with patch.object(git_archive, "get_base_dir", return_value=tmp_base_dir):
        with pytest.raises(SystemExit) as exc_info:
            git_archive.move_git_folders()
        assert exc_info.value.code == 1


def test_move_git_folders_no_git_dirs(tmp_base_dir: Path) -> None:
    repos_dir = tmp_base_dir / "repos"
    owner_dir = repos_dir / "owner"
    owner_dir.mkdir()
    repo_dir = owner_dir / "repo"
    repo_dir.mkdir()

    with patch.object(git_archive, "get_base_dir", return_value=tmp_base_dir):
        with pytest.raises(SystemExit) as exc_info:
            git_archive.move_git_folders()
        assert exc_info.value.code == 0


def test_restore_git_folders(tmp_base_dir: Path, create_git_dirs: list[Path]) -> None:
    with patch.object(git_archive, "get_base_dir", return_value=tmp_base_dir):
        git_archive.move_git_folders()

    for git_dir in create_git_dirs:
        assert not git_dir.exists()

    with patch.object(git_archive, "get_base_dir", return_value=tmp_base_dir):
        git_archive.restore_git_folders()

    for git_dir in create_git_dirs:
        assert git_dir.exists()


def test_restore_git_folders_no_archive(tmp_base_dir: Path) -> None:
    with patch.object(git_archive, "get_base_dir", return_value=tmp_base_dir):
        with pytest.raises(SystemExit) as exc_info:
            git_archive.restore_git_folders()
        assert exc_info.value.code == 1


def test_restore_git_folders_overwrite(tmp_base_dir: Path, create_git_dirs: list[Path]) -> None:
    with patch.object(git_archive, "get_base_dir", return_value=tmp_base_dir):
        git_archive.move_git_folders()

    for git_dir in create_git_dirs:
        git_dir.mkdir()

    with patch.object(git_archive, "get_base_dir", return_value=tmp_base_dir):
        git_archive.restore_git_folders()

    for git_dir in create_git_dirs:
        assert git_dir.exists()


def test_main_move(tmp_base_dir: Path, create_git_dirs: list[Path]) -> None:
    with patch.object(git_archive, "get_base_dir", return_value=tmp_base_dir):
        with patch("sys.argv", ["git-archive.py", "move"]):
            git_archive.main()

    archive_path = tmp_base_dir / ".tmp_store" / "git-folders.tar.gz"
    assert archive_path.exists()


def test_main_restore(tmp_base_dir: Path, create_git_dirs: list[Path]) -> None:
    with patch.object(git_archive, "get_base_dir", return_value=tmp_base_dir):
        with patch("sys.argv", ["git-archive.py", "move"]):
            git_archive.main()

    with patch.object(git_archive, "get_base_dir", return_value=tmp_base_dir):
        with patch("sys.argv", ["git-archive.py", "restore"]):
            git_archive.main()

    for git_dir in create_git_dirs:
        assert git_dir.exists()


def test_main_invalid_command() -> None:
    with patch("sys.argv", ["git-archive.py", "invalid"]):
        with pytest.raises(SystemExit) as exc_info:
            git_archive.main()
        assert exc_info.value.code == 1


def test_main_no_args() -> None:
    with patch("sys.argv", ["git-archive.py"]):
        with pytest.raises(SystemExit) as exc_info:
            git_archive.main()
        assert exc_info.value.code == 1
