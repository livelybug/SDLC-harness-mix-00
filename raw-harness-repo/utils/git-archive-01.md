# git-archive.py — Specification

## Purpose

Archive and restore `.git` folders from all repos in `raw-harness-repo/repos/`. This allows stripping version control metadata to save space, then restoring it later.

## User Story

As a developer managing multiple cloned repos,
I want to archive all `.git` folders into a single tarball and restore them later,
so that I can reclaim disk space without losing git history.

## CLI Interface

```bash
# Archive: zip all .git folders, then delete originals
python3 utils/git-archive.py move

# Restore: extract .git folders back to their repos
python3 utils/git-archive.py restore
```

## Behavior

### `move` command

1. Walk `repos/{owner}/{repo}/` directories
2. For each repo, check if `.git/` exists
   - If missing: print warning, skip
   - If present: add to archive list
3. Create `.tmp_store/git-folders.tar.gz` containing all `.git/` folders with paths preserved:
   ```
   git-folders.tar.gz
   └── repos/
       ├── affaan-m/ECC/.git/...
       ├── obra/superpowers/.git/...
       └── ...
   ```
4. After successful tar, delete each `.git/` folder from the repos

### `restore` command

1. Check if `.tmp_store/git-folders.tar.gz` exists
   - If missing: print error, exit with code 1
2. Extract directly into `raw-harness-repo/` — the tar's internal paths (`repos/...`) map back naturally
3. For each `.git/` being restored:
   - If repo already has `.git/`: overwrite with warning
   - If repo has no `.git/`: restore normally

## Path Resolution

All paths are relative to the script's grandparent directory (`raw-harness-repo/`).

```
raw-harness-repo/
├── utils/
│   └── git-archive.py      # script lives here
├── repos/                    # repos_dir = ../repos
│   ├── affaan-m/
│   │   └── ECC/
│   │       └── .git/
│   └── ...
└── .tmp_store/                # archive_dir = ../.tmp_store
    └── git-folders.tar.gz
```

Implementation: use `Path(__file__).resolve().parent.parent` to get `raw-harness-repo/`.

## Technical Details

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Format | `tar.gz` via `tarfile` | Preserves symlinks and permissions; `.git/hooks/` often has symlinks |
| Compression | `tar.gz` (gzip) | Good compression, universal support |
| Dependencies | stdlib only (`tarfile`, `pathlib`, `argparse`) | Zero external deps |
| Path encoding | Natural directory structure in tar | No separator tricks; `repos/{owner}/{repo}/.git/` maps 1:1 |
| Filename | `git-folders.tar.gz` | Fixed name; `.tmp_store/` is throwaway |

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| Repo has no `.git` on move | Skip with warning |
| Repo already has `.git` on restore | Overwrite with warning |
| `git-folders.tar.gz` missing on restore | Error + exit code 1 |
| `.tmp_store/` doesn't exist | Create it |
| `.understand-anything/` in repos/ | Skip (not a git repo) |

## Implementation Skeleton

```python
#!/usr/bin/env python3
"""Archive and restore .git folders from repos."""

import argparse
import sys
import tarfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
REPOS_DIR = BASE_DIR / "repos"
ARCHIVE_DIR = BASE_DIR / ".tmp_store"
ARCHIVE_NAME = "git-folders.tar.gz"


def find_git_folders():
    """Find all repos/{owner}/{repo}/.git directories."""
    git_folders = []
    for owner_dir in sorted(REPOS_DIR.iterdir()):
        if not owner_dir.is_dir() or owner_dir.name.startswith("."):
            continue
        for repo_dir in sorted(owner_dir.iterdir()):
            if not repo_dir.is_dir():
                continue
            git_path = repo_dir / ".git"
            if git_path.exists():
                git_folders.append(git_path)
            else:
                print(f"WARNING: No .git in {repo_dir.relative_to(BASE_DIR)}, skipping")
    return git_folders


def cmd_move():
    """Archive all .git folders into tar.gz, then delete originals."""
    git_folders = find_git_folders()
    if not git_folders:
        print("No .git folders found.")
        return

    ARCHIVE_DIR.mkdir(exist_ok=True)
    archive_path = ARCHIVE_DIR / ARCHIVE_NAME

    print(f"Archiving {len(git_folders)} .git folders to {archive_path.name}...")
    with tarfile.open(archive_path, "w:gz") as tar:
        for git_folder in git_folders:
            tar.add(git_folder, arcname=git_folder.relative_to(BASE_DIR))
            print(f"  + {git_folder.relative_to(BASE_DIR)}")

    print("Removing original .git folders...")
    for git_folder in git_folders:
        # Use shutil.rmtree for actual deletion
        import shutil
        shutil.rmtree(git_folder)
        print(f"  - {git_folder.relative_to(BASE_DIR)}")

    print(f"Done. Archive: {archive_path}")


def cmd_restore():
    """Extract .git folders from tar.gz back to their repos."""
    archive_path = ARCHIVE_DIR / ARCHIVE_NAME

    if not archive_path.exists():
        print(f"ERROR: Archive not found: {archive_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Restoring from {archive_path.name}...")
    with tarfile.open(archive_path, "r:gz") as tar:
        for member in tar.getmembers():
            # Check if target .git already exists
            target = BASE_DIR / member.name
            if target.exists() and target == target.parent / ".git":
                print(f"  WARNING: Overwriting {member.name}")
            tar.extract(member, path=BASE_DIR)
            print(f"  + {member.name}")

    print("Done.")


def main():
    parser = argparse.ArgumentParser(description="Archive/restore .git folders")
    parser.add_argument("command", choices=["move", "restore"])
    args = parser.parse_args()

    if args.command == "move":
        cmd_move()
    elif args.command == "restore":
        cmd_restore()


if __name__ == "__main__":
    main()
```

## Usage

```bash
cd raw-harness-repo

# Archive all .git folders
python3 utils/git-archive.py move

# Verify
ls .tmp_store/git-folders.tar.gz
ls repos/affaan-m/ECC/  # should have no .git

# Restore
python3 utils/git-archive.py restore
```
