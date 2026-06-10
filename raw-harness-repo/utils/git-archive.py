from __future__ import annotations

import shutil
import sys
import tarfile
from pathlib import Path


def get_base_dir() -> Path:
    return Path(__file__).parent.parent


def move_git_folders() -> None:
    base_dir = get_base_dir()
    repos_dir = base_dir / "repos"
    tmp_store_dir = base_dir / ".tmp_store"
    archive_path = tmp_store_dir / "git-folders.tar.gz"

    if not repos_dir.exists():
        print(f"Error: repos directory not found at {repos_dir}")
        sys.exit(1)

    tmp_store_dir.mkdir(exist_ok=True)

    git_dirs: list[Path] = []
    warnings: list[str] = []

    for owner_dir in repos_dir.iterdir():
        if not owner_dir.is_dir():
            continue
        for repo_dir in owner_dir.iterdir():
            if not repo_dir.is_dir():
                continue
            git_dir = repo_dir / ".git"
            if git_dir.exists():
                git_dirs.append(git_dir)
            else:
                warnings.append(f"Warning: {repo_dir.relative_to(base_dir)} has no .git — skipping")

    for warning in warnings:
        print(warning)

    if not git_dirs:
        print("No .git folders found to archive")
        sys.exit(0)

    with tarfile.open(archive_path, "w:gz") as tar:
        for git_dir in git_dirs:
            tar.add(git_dir, arcname=git_dir.relative_to(base_dir))

    print(f"Archived {len(git_dirs)} .git folders to {archive_path.relative_to(base_dir)}")

    for git_dir in git_dirs:
        shutil.rmtree(git_dir)
        print(f"Deleted {git_dir.relative_to(base_dir)}")


def restore_git_folders() -> None:
    base_dir = get_base_dir()
    archive_path = base_dir / ".tmp_store" / "git-folders.tar.gz"

    if not archive_path.exists():
        print(f"Error: Archive not found at {archive_path.relative_to(base_dir)}")
        sys.exit(1)

    repos_dir = base_dir / "repos"
    if repos_dir.exists():
        for owner_dir in repos_dir.iterdir():
            if not owner_dir.is_dir():
                continue
            for repo_dir in owner_dir.iterdir():
                if not repo_dir.is_dir():
                    continue
                git_path = repo_dir / ".git"
                if git_path.exists():
                    print(f"Warning: {git_path.relative_to(base_dir)} already exists — overwriting")
                    shutil.rmtree(git_path)

    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(base_dir)

    print("Restored .git folders from archive")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("move", "restore"):
        print("Usage: python3 utils/git-archive.py [move|restore]")
        sys.exit(1)

    command = sys.argv[1]
    if command == "move":
        move_git_folders()
    elif command == "restore":
        restore_git_folders()


if __name__ == "__main__":
    main()
