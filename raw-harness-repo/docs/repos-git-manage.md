# Automatic `.git` Archive/Restore in `download_repos.py`

## Purpose

Automatically archive and restore `.git` folders during batch repo processing, so the project maintains "one git state at a time" — `.git` folders exist only during active git operations, then get archived to avoid noise git state noise.

## Current State

- `git_archive.py` provides `move_git_folders()` and `restore_git_folders()` for manual CLI use
- `download_repos.py` loops through repos, calling `setup()` or `update()` on each
- `.git` folders persist after operations, causing indexing noise

## Requirements

### Flow

```
1. Pre-check: Does .tmp_store/git-folders.tar.gz exist?
   ├─ Yes → restore_git_folders() (so git operations can work)
   └─ No  → skip (first run scenario)
2. Loop: process each repo (setup or update)
3. move_git_folders() (archive all .git folders)
```

### Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Scope | `download_repos.py` only | Central orchestration point, not per-repo |
| Reuse | Import from `git_archive.py` | DRY, single source of truth |
| Restore timing | Before loop, pre-check exists | Avoid `sys.exit(1)` on first run |
| Archive timing | After loop | Clean up after all operations complete |
| Error handling | try/except, log warning, continue | Don't kill batch on archive/restore failure |
| Output | Keep verbose | User sees .git management activity |

### Error Handling Details

```python
# Restore: pre-check + try/except
archive_path = get_project_root() / ".tmp_store" / "git-folders.tar.gz"
if archive_path.exists():
    try:
        restore_git_folders()
    except Exception as e:
        print(f"Warning: Failed to restore .git folders: {e}")

# ... loop ...

# Archive: try/except
try:
    move_git_folders()
except Exception as e:
    print(f"Warning: Failed to archive .git folders: {e}")
```

## Implementation Tasks

### Task 1: Add imports to `download_repos.py`

Add import for git_archive functions and path helper:

```python
from raw_harness.utils.git_archive import move_git_folders, restore_git_folders
from raw_harness.paths import get_project_root
```

Location: Top of `src/raw_harness/download_repos.py`, after existing imports.

### Task 2: Add restore before loop

Insert before the `results = []` line (currently line 73):

```python
# Restore .git folders if archive exists (so git operations can work)
archive_path = get_project_root() / ".tmp_store" / "git-folders.tar.gz"
if archive_path.exists():
    try:
        restore_git_folders()
    except Exception as e:
        print(f"Warning: Failed to restore .git folders: {e}")
```

### Task 3: Add archive after loop

Insert after the loop completes, before the summary print (currently line 78):

```python
# Archive .git folders (clean up for indexing)
try:
    move_git_folders()
except Exception as e:
    print(f"Warning: Failed to archive .git folders: {e}")
```

### Task 4: Update README

Update `README.md` section "`.git` Management" (lines 83-99) to document automatic behavior:

```markdown
## `.git` Management

`.git` folders are automatically managed during batch operations:

- **Before `download_repos.py` runs:** Restores `.git` folders from `.tmp_store/git-folders.tar.gz` (if archive exists)
- **After `download_repos.py` finishes:** Archives all `.git` folders to `.tmp_store/git-folders.tar.gz`

This maintains "one git state at a time" — `.git` folders exist only during active operations.

### Manual CLI Usage

For manual archive/restore outside of batch operations:

```bash
cd raw-harness-repo

# Archive .git folders to .tmp_store/git-folders.tar.gz (deletes originals)
python3 -m raw_harness.utils.git_archive move

# Restore .git folders from archive
python3 -m raw_harness.utils.git_archive restore
```
```

## Files to Modify

| File | Change |
|------|--------|
| `src/raw_harness/download_repos.py` | Add imports, restore before loop, archive after loop |
| `README.md` | Update `.git` Management section |

## Testing

After implementation, verify:

1. First run (no archive): Should work normally, archive created at end
2. Second run (archive exists): Should restore, process, archive again
3. Error case: Manually corrupt archive, verify warning printed, batch continues
