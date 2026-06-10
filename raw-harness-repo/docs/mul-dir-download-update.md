# Multi-Directory Sparse Checkout — Implementation Guide

> Derived from `/grill-me` session on `raw-harness-repo/dir-download.py`.
> Decision log at end of document.

## Overview

`SparseCheckoutManager` currently downloads **one** directory per repo. This guide documents changes to support **multiple** directories per repo.

### Final Decisions

| # | Axis | Outcome |
|---|---|---|
| 1 | API shape | `folder_paths: list[str]` constructor param |
| 2 | Path getter | Rename to `get_folder_paths()` → `list[str]` |
| 3 | Copy behavior | Preserve relative directory structure in output |
| 4 | Branch config | Auto-detect default branch via `git ls-remote --symref` |
| 5 | Usage example | Guard with `if __name__ == "__main__":` + multi-dir demo |
| 6 | Missing paths | Raise error if any path absent after pull |
| 7 | New methods | None — update existing 4 methods only |

---

## Change 1 — Constructor

**Current (line 6–17):**

```python
def __init__(self, repo_url, folder_path, local_storage_path):
    """
    Manage a sparse checkout of a GitHub folder.
    ...
    """
    self.repo_url = repo_url
    self.folder_path = folder_path
    self.repo_path = local_storage_path
```

**Replace with:**

```python
def __init__(self, repo_url: str, folder_paths: list[str], local_storage_path: str):
    """
    Manage sparse checkouts of multiple GitHub folders from a single repo.

    Args:
        repo_url: "https://github.com/username/repo.git"
        folder_paths: List of folder paths, e.g. ["pandas/io", "pandas/core"]
        local_storage_path: Where to store the git repo (persistent)
    """
    if not folder_paths:
        raise ValueError("folder_paths must be non-empty")
    self.repo_url = repo_url
    self.folder_paths = list(folder_paths)       # defensive copy
    self.repo_path = local_storage_path
    self._default_branch: str | None = None       # detected in setup()
```

**Key points:**
- Param renamed `folder_path` → `folder_paths` with type `list[str]`
- Raises `ValueError` on empty list (no-op checkout makes no sense)
- Add `_default_branch` slot (populated by auto-detection in `setup()`)
- Docstring updated

---

## Change 2 — Branch Auto-Detection (private helper)

**Add new private method** before `setup()`:

```python
def _detect_default_branch(self) -> str:
    """Query remote HEAD to determine default branch name."""
    result = subprocess.run(
        ["git", "ls-remote", "--symref", "origin", "HEAD"],
        cwd=self.repo_path,
        capture_output=True, text=True, check=True
    )
    # Output format: "ref: refs/heads/main\tHEAD\n<hash>\tHEAD\n"
    for line in result.stdout.strip().split("\n"):
        if line.startswith("ref:") and "HEAD" in line:
            # line like: "ref: refs/heads/main\tHEAD"
            ref = line.split("\t")[0]         # "ref: refs/heads/main"
            branch = ref.split("/")[-1]        # "main"
            return branch
    raise RuntimeError(f"Could not detect default branch for {self.repo_url}")
```

**Why:** `setup()` calls this after adding the remote but before pulling. The branch is cached on `self._default_branch` so `update()` can reuse it without re-detecting.

---

## Change 3 — `setup()`

**Current (lines 19–53):**

```
# Hardcodes "main" on lines 49, 53
# Writes single folder_path to sparse-checkout file
```

**Replace with:**

```python
def setup(self) -> None:
    """Initial setup of sparse checkout for all requested folders."""
    if os.path.exists(self.repo_path):
        print(f"Repository already exists at {self.repo_path}")
        return

    os.makedirs(self.repo_path, exist_ok=True)

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=self.repo_path, check=True)

    # Add remote
    subprocess.run(
        ["git", "remote", "add", "origin", self.repo_url],
        cwd=self.repo_path, check=True
    )

    # Enable sparse checkout
    subprocess.run(
        ["git", "config", "core.sparseCheckout", "true"],
        cwd=self.repo_path, check=True
    )

    # Write ALL folder paths to sparse-checkout file (one per line)
    sparse_path = os.path.join(self.repo_path, ".git", "info", "sparse-checkout")
    with open(sparse_path, "w") as f:
        for folder in self.folder_paths:
            f.write(f"{folder}/\n")

    # Auto-detect default branch
    self._default_branch = self._detect_default_branch()

    # Initial pull
    subprocess.run(
        ["git", "pull", "origin", self._default_branch],
        cwd=self.repo_path, check=True
    )

    # Verify all paths exist
    self._verify_paths_exist()

    paths_display = ", ".join(self.folder_paths)
    print(f"Initial setup complete. Folders available under {self.repo_path}/")
    print(f"  ({paths_display})")
```

---

## Change 4 — `_verify_paths_exist()` (new private helper)

**Add before `update()`:**

```python
def _verify_paths_exist(self) -> None:
    """Raise error if any requested folder is missing after checkout."""
    missing = []
    for folder in self.folder_paths:
        full_path = os.path.join(self.repo_path, folder)
        if not os.path.isdir(full_path):
            missing.append(folder)
    if missing:
        raise FileNotFoundError(
            f"Folders not found in repo after checkout: {missing}\n"
            f"Repo: {self.repo_url}\n"
            f"Check that all paths exist on remote."
        )
```

**Why:** Decision #6 — raise error for ANY missing path. No silent skipping.

---

## Change 5 — `update()`

**Current (lines 55–78):**

```
# Hardcodes "main" on lines 68, 72
```

**Replace with:**

```python
def update(self) -> str:
    """Update all folders to the latest version."""
    if not os.path.exists(self.repo_path):
        raise RuntimeError("Repository not found. Run setup() first.")

    # Detect branch if not already cached (e.g. repo existed before this code upgrade)
    if self._default_branch is None:
        self._default_branch = self._detect_default_branch()

    # Fetch latest changes
    subprocess.run(
        ["git", "fetch", "origin"],
        cwd=self.repo_path, check=True
    )

    # Pull updates (only affects sparse checkout folders)
    result = subprocess.run(
        ["git", "pull", "origin", self._default_branch],
        cwd=self.repo_path, capture_output=True, text=True
    )

    if "Already up to date" in result.stdout:
        print("Folders are already up to date")
    else:
        print("Update completed successfully")
        print(result.stdout)

    # Re-verify after update (paths could have been removed upstream)
    self._verify_paths_exist()

    return result.stdout
```

**Key points:**
- Uses `self._default_branch` instead of hardcoded `"main"`
- Falls back to auto-detection if `_default_branch` is `None`
- Raises `RuntimeError` consistently (was `Exception`)
- Verifies paths after pull

---

## Change 6 — `get_folder_path()` → `get_folder_paths()`

**Current (lines 80–82):**

```python
def get_folder_path(self):
    """Get the path to the checked out folder"""
    return os.path.join(self.repo_path, self.folder_path)
```

**Replace with:**

```python
def get_folder_paths(self) -> list[str]:
    """Get absolute paths to all checked out folders.

    Returns:
        List of paths like ["/abs/path/repo/pandas/io", "/abs/path/repo/pandas/core"]
    """
    return [os.path.join(self.repo_path, f) for f in self.folder_paths]
```

**Key points:**
- Renamed to plural `get_folder_paths()`
- Returns `list[str]` — one absolute path per requested folder
- Type-annotated

---

## Change 7 — `copy_to_output()`

**Current (lines 84–91):**

```python
def copy_to_output(self, output_path):
    """Copy the folder to another location (for deployment)"""
    source = self.get_folder_path()
    if os.path.exists(source):
        if os.path.exists(output_path):
            shutil.rmtree(output_path)
        shutil.copytree(source, output_path)
        print(f"Copied to {output_path}")
```

**Replace with:**

```python
def copy_to_output(self, output_path: str) -> None:
    """Copy all checked-out folders to another location, preserving relative paths.

    Example:
        If folder_paths = ["pandas/io", "pandas/core"] and output_path = "./out":
        Result: ./out/pandas/io/  and  ./out/pandas/core/

        If folder_paths = ["src/backend", "docs/api"] and output_path = "./out":
        Result: ./out/src/backend/  and  ./out/docs/api/
    """
    for source in self.get_folder_paths():
        if not os.path.exists(source):
            raise FileNotFoundError(
                f"Source folder not found: {source}. Run setup() or update() first."
            )

        # Compute destination preserving relative structure
        rel_dir = os.path.relpath(source, self.repo_path)
        dest = os.path.join(output_path, rel_dir)

        if os.path.exists(dest):
            shutil.rmtree(dest)

        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copytree(source, dest)
        print(f"Copied {rel_dir} -> {dest}")
```

**Key points:**
- Iterates over all folder paths via `get_folder_paths()`
- Preserves relative directory structure (Decision #3)
- Raises `FileNotFoundError` if source doesn't exist (was: silent skip)
- Creates intermediate parent dirs (`os.makedirs`)

---

## Change 8 — Usage Example Block

**Current (lines 93–107):** Unguarded code that runs on `import`.

**Replace with:**

```python
if __name__ == "__main__":
    # --- Example: single directory (still works) ---
    manager_single = SparseCheckoutManager(
        repo_url="https://github.com/pandas-dev/pandas.git",
        folder_paths=["pandas/io"],
        local_storage_path="./my_sparse_repo"
    )
    # manager_single.setup()

    # --- Example: multiple directories ---
    manager_multi = SparseCheckoutManager(
        repo_url="https://github.com/pandas-dev/pandas.git",
        folder_paths=[
            "pandas/io",
            "pandas/core",
            "pandas/api",
        ],
        local_storage_path="./my_sparse_repo_multi"
    )
    # manager_multi.setup()
    # manager_multi.update()
    # manager_multi.copy_to_output("./pandas_latest")
```

**Key points:**
- Guarded with `if __name__ == "__main__":` (Decision #5)
- Includes both single-path and multi-path examples
- Calls commented out so examples are illustrative only

---

## Summary of All Edits

| Line range | Change | What |
|---|---|---|
| 5–17 | Edit | Constructor: `folder_paths: list[str]`, `_default_branch`, empty check |
| — | Add | `_detect_default_branch()` private method |
| 19–53 | Edit | `setup()`: multi-path sparse-checkout, branch auto-detect, path verification |
| — | Add | `_verify_paths_exist()` private method |
| 55–78 | Edit | `update()`: use `_default_branch`, verify paths post-pull |
| 80–82 | Edit | Rename `get_folder_path()` → `get_folder_paths()`, return `list[str]` |
| 84–91 | Edit | `copy_to_output()`: iterate all paths, preserve relative structure |
| 93–107 | Edit | `if __name__ == "__main__":` guard + multi-dir examples |

---

## Decision Log

```
Q1: API shape for multiple dirs?
    → Option a: folder_paths: list[str]

Q2: get_folder_path() with multiple dirs?
    → Option c: Rename to get_folder_paths(), return list[str]

Q3: copy_to_output() directory structure?
    → Option b: Preserve relative structure

Q4: Branch configuration?
    → Option c: Auto-detect via git ls-remote --symref

Q5: Usage example at bottom?
    → Options a & c: Guard with if __name__ + update examples

Q6: Missing path handling?
    → Raise error for any missing path

Q7: Additional utility methods?
    → Option a: None
```
