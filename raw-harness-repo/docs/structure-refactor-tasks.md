# Structure Refactor Tasks

Detailed task breakdown for refactoring `raw-harness-repo/` file structure.

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Package management | `pyproject.toml` + `pip install -e .` | Standard Python, works with pytest |
| Package structure | Proper packages (`raw_harness`) | Clean imports, no `src` in import path |
| Config path resolution | Project root discovery | Robust, handles future moves |
| Temp directory naming | `.tmp_store` (with dot) | Matches code expectations |
| Cache cleanup | Clean before refactor | Avoids stale bytecode errors |
| Empty `utils/` | Delete after move | No empty directories |
| `.gitignore` | Skip | Developer responsibility |
| Test verification | `pytest tests/ -v` | Simple, catches everything |
| `__init__.py` content | Empty files | Explicit imports, no circular deps |
| Documentation | Update README and plan | Keep docs accurate |

---

## Task 1: Clean Cache Directories

**Goal:** Remove stale bytecode and test cache before refactor.

**Steps:**
```bash
cd raw-harness-repo
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
rm -rf .pytest_cache
```

**Verify:**
- No `__pycache__/` directories remain
- No `.pytest_cache/` directory remains

---

## Task 2: Rename `tmp-store` to `.tmp_store`

**Goal:** Match code expectations (code uses `.tmp_store`, directory was `tmp-store`).

**Steps:**
```bash
cd raw-harness-repo
mv tmp-store .tmp_store
```

**Verify:**
- `.tmp_store/git-folders.tar.gz` exists

---

## Task 3: Create Package Structure

**Goal:** Create `src/raw_harness/` and `src/raw_harness/utils/` with `__init__.py` files.

**Steps:**
```bash
cd raw-harness-repo
mkdir -p src/raw_harness/utils
touch src/raw_harness/__init__.py
touch src/raw_harness/utils/__init__.py
```

**Verify:**
- `src/raw_harness/__init__.py` exists (empty)
- `src/raw_harness/utils/__init__.py` exists (empty)

---

## Task 4: Create `pyproject.toml`

**Goal:** Define package metadata for `pip install -e .`

**Steps:**
Create `raw-harness-repo/pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=64"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "raw-harness"
version = "0.1.0"
requires-python = ">=3.10"

[tool.setuptools.packages.find]
where = ["src"]
```

**Verify:**
- `pyproject.toml` exists in project root

---

## Task 5: Create Project Root Discovery Utility

**Goal:** Add utility to find project root for config path resolution.

**Steps:**
Create `src/raw_harness/paths.py`:
```python
from __future__ import annotations

from pathlib import Path


def get_project_root() -> Path:
    """Find project root by looking for pyproject.toml."""
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find project root (no pyproject.toml found)")


def get_config_path(filename: str) -> Path:
    """Get path to a config file in the config/ directory."""
    return get_project_root() / "config" / filename
```

**Verify:**
- `src/raw_harness/paths.py` exists
- Contains `get_project_root()` and `get_config_path()` functions

---

## Task 6: Move Markdown Files to `docs/`

**Goal:** Move documentation files to `docs/` directory.

**Files to move:**
- `harness-mix-download.md` → `docs/`
- `idea.md` → `docs/`
- `mul-dir-download-update.md` → `docs/`
- `note.md` → `docs/`
- `utils/git-archive-01.md` → `docs/`

**Steps:**
```bash
cd raw-harness-repo
mv harness-mix-download.md docs/
mv idea.md docs/
mv mul-dir-download-update.md docs/
mv note.md docs/
mv utils/git-archive-01.md docs/
```

**Verify:**
- All 5 files exist in `docs/`
- No `.md` files remain in root (except README.md)
- `utils/git-archive-01.md` no longer exists

---

## Task 7: Move Config Files to `config/`

**Goal:** Move configuration files to `config/` directory.

**Files to move:**
- `repo-urls.md` → `config/`
- `repos-config.json` → `config/`

**Steps:**
```bash
cd raw-harness-repo
mv repo-urls.md config/
mv repos-config.json config/
```

**Verify:**
- `config/repo-urls.md` exists
- `config/repos-config.json` exists

---

## Task 8: Move Source Files to `src/raw_harness/`

**Goal:** Move Python source files to proper package location.

**Files to move:**
- `urls_to_config.py` → `src/raw_harness/`
- `download_repos.py` → `src/raw_harness/`
- `dir-download.py` → `src/raw_harness/`
- `utils/git-archive.py` → `src/raw_harness/utils/`

**Steps:**
```bash
cd raw-harness-repo
mv urls_to_config.py src/raw_harness/
mv download_repos.py src/raw_harness/
mv dir-download.py src/raw_harness/
mv utils/git-archive.py src/raw_harness/utils/
```

**Verify:**
- `src/raw_harness/urls_to_config.py` exists
- `src/raw_harness/download_repos.py` exists
- `src/raw_harness/dir-download.py` exists
- `src/raw_harness/utils/git-archive.py` exists

---

## Task 9: Move Test Files to `tests/`

**Goal:** Move test files to `tests/` directory.

**Files to move:**
- `test_download_repos.py` → `tests/`
- `test_urls_to_config.py` → `tests/`
- `utils/test_git_archive.py` → `tests/`

**Steps:**
```bash
cd raw-harness-repo
mv test_download_repos.py tests/
mv test_urls_to_config.py tests/
mv utils/test_git_archive.py tests/
```

**Verify:**
- `tests/test_download_repos.py` exists
- `tests/test_urls_to_config.py` exists
- `tests/test_git_archive.py` exists

---

## Task 10: Delete Empty `utils/` Directory

**Goal:** Remove empty `utils/` directory after moving contents.

**Steps:**
```bash
cd raw-harness-repo
rmdir utils
```

**Verify:**
- `utils/` directory does not exist

---

## Task 11: Install Package in Editable Mode

**Goal:** Make imports work with new package structure.

**Steps:**
```bash
cd raw-harness-repo
pip install -e .
```

**Verify:**
- Command succeeds
- `pip show raw-harness` shows package info

---

## Task 12: Update Config Path References in `download_repos.py`

**Goal:** Use project root discovery for config file path.

**Current code (line 54):**
```python
config_file = Path(__file__).parent / "repos-config.json"
```

**New code:**
```python
from raw_harness.paths import get_config_path

# ...

config_file = get_config_path("repos-config.json")
```

**Steps:**
1. Add import for `get_config_path`
2. Replace `Path(__file__).parent / "repos-config.json"` with `get_config_path("repos-config.json")`

**Verify:**
- No `Path(__file__).parent` references to config files
- Import statement present

---

## Task 13: Update Config Path References in `urls_to_config.py`

**Goal:** Use project root discovery for config and URLs file paths.

**Current code (lines 25-26):**
```python
urls_file = Path(__file__).parent / "repo-urls.md"
config_file = Path(__file__).parent / "repos-config.json"
```

**New code:**
```python
from raw_harness.paths import get_config_path

# ...

urls_file = get_config_path("repo-urls.md")
config_file = get_config_path("repos-config.json")
```

**Steps:**
1. Add import for `get_config_path`
2. Replace both path references

**Verify:**
- No `Path(__file__).parent` references to config files
- Import statement present

---

## Task 14: Update Import Statements in `test_urls_to_config.py`

**Goal:** Fix import after moving to `tests/` directory.

**Current code (line 5):**
```python
from urls_to_config import parse_repo_urls
```

**New code:**
```python
from raw_harness.urls_to_config import parse_repo_urls
```

**Steps:**
1. Update import statement

**Verify:**
- Import uses `raw_harness.urls_to_config`

---

## Task 15: Update Import Statements in `test_download_repos.py`

**Goal:** Fix import after moving to `tests/` directory.

**Current code (line 9):**
```python
from download_repos import extract_owner_repo, get_repo_path, main, process_repo
```

**New code:**
```python
from raw_harness.download_repos import extract_owner_repo, get_repo_path, main, process_repo
```

**Steps:**
1. Update import statement

**Verify:**
- Import uses `raw_harness.download_repos`

---

## Task 16: Update Import Statements in `test_git_archive.py`

**Goal:** Fix import after moving to `tests/` directory.

**Check current imports and update to:**
```python
from raw_harness.utils.git_archive import ...
```

**Steps:**
1. Check current imports (may need to read file)
2. Update to use `raw_harness.utils.git_archive`

**Verify:**
- Import uses `raw_harness.utils.git_archive`

---

## Task 17: Run Tests to Verify Utils

**Goal:** Ensure utility functions work after refactor.

**Steps:**
```bash
cd raw-harness-repo
python3 -m pytest tests/test_urls_to_config.py tests/test_git_archive.py -v
```

**Verify:**
- All tests pass
- No import errors

---

## Task 18: Run Tests to Verify Download Functions

**Goal:** Ensure download functions work after refactor.

**Steps:**
```bash
cd raw-harness-repo
python3 -m pytest tests/test_download_repos.py -v
```

**Verify:**
- All tests pass
- No import errors

---

## Task 19: Run All Tests

**Goal:** Final verification that everything works together.

**Steps:**
```bash
cd raw-harness-repo
python3 -m pytest tests/ -v
```

**Verify:**
- All tests pass
- No warnings about imports

---

## Task 20: Update README.md

**Goal:** Update file table and test commands to reflect new structure.

**Changes needed:**
1. Update file table with new paths
2. Update test commands
3. Update any other path references

**New file table:**
```markdown
| File | Purpose                                          |
|------|--------------------------------------------------|
| `config/repos-config.json` | Repository URLs and skill folder paths           |
| `src/raw_harness/download_repos.py` | Main script - downloads/updates repos            |
| `src/raw_harness/dir-download.py` | SparseCheckoutManager implementation             |
| `src/raw_harness/urls_to_config.py` | Helper: converts `repo-urls.md` to config        |
| `src/raw_harness/utils/git-archive.py` | Archive/restore `.git` folders for index cleanup |
| `tests/test_download_repos.py` | Tests for download_repos.py                      |
| `tests/test_urls_to_config.py` | Tests for urls_to_config.py                      |
| `tests/test_git_archive.py` | Tests for git-archive.py                         |
```

**New test commands:**
```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific tests
python3 -m pytest tests/test_download_repos.py tests/test_urls_to_config.py tests/test_git_archive.py -v
```

**Verify:**
- File table matches actual file locations
- Test commands work

---

## Task 21: Update `structure-refactor.md`

**Goal:** Document our decisions in the plan file.

**Add section:**
```markdown
## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Package management | `pyproject.toml` + `pip install -e .` | Standard Python, works with pytest |
| Package structure | Proper packages (`raw_harness`) | Clean imports, no `src` in import path |
| Config path resolution | Project root discovery | Robust, handles future moves |
| Temp directory naming | `.tmp_store` (with dot) | Matches code expectations |
| Cache cleanup | Clean before refactor | Avoids stale bytecode errors |
| Empty `utils/` | Delete after move | No empty directories |
| `.gitignore` | Skip | Developer responsibility |
| Test verification | `pytest tests/ -v` | Simple, catches everything |
| `__init__.py` content | Empty files | Explicit imports, no circular deps |
| Documentation | Update README and plan | Keep docs accurate |
```

**Verify:**
- Decisions section added to plan

---

## Execution Order

Execute tasks in this order:

1. **Preparation:** Tasks 1-2 (clean cache, rename tmp-store)
2. **Structure Setup:** Tasks 3-5 (create packages, pyproject.toml, paths utility)
3. **File Moves:** Tasks 6-10 (move files, delete empty dirs)
4. **Package Install:** Task 11 (pip install -e .)
5. **Reference Updates:** Tasks 12-16 (update imports and paths)
6. **Verification:** Tasks 17-19 (run tests)
7. **Documentation:** Tasks 20-21 (update README and plan)

---

## Success Criteria

- [ ] All files in correct locations
- [ ] `pip install -e .` succeeds
- [ ] `pytest tests/ -v` passes
- [ ] README.md updated
- [ ] structure-refactor.md updated
- [ ] No stale cache directories
- [ ] Empty `utils/` deleted
