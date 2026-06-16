# Fix for Issue #4: Undesirable Folders Downloaded

## Problem

When using sparse checkout to download specific folders from GitHub repositories, extra folders that weren't requested were also being downloaded. For example:
- `raw-harness-repo/repos/affaan-m/ECC/docs` - not requested
- `raw-harness-repo/repos/garrytan/gstack/ios-qa` - not requested

## Root Cause

The folder paths in `repos-config.json` must be **absolute paths from the repository root, starting with `/`**.

When a path does **not** start with `/`, Git's cone mode treats it as a relative pattern and falls back to **non-cone (pattern-matching) mode**. In non-cone mode, specifying `docs` is interpreted as `**/docs` — matching any directory named `docs` anywhere in the repository. This caused unintended folders like `affaan-m/ECC/docs` and `garrytan/gstack/ios-qa` to be materialized.

In true cone mode, paths are strictly evaluated from the repository root, so `/docs` only matches the top-level `docs` directory.

## Solution

### 1. Use absolute paths (leading `/`) in config

```json
{
  "repos": [
    {
      "url": "https://github.com/owner/repo.git",
      "skill_folders": ["/skills", "/docs/api"]
    }
  ]
}
```

Paths starting with `/` anchor to the repo root, ensuring cone mode works correctly and only the specified directories are materialized.

### 2. Prune worktree after checkout

Added `_prune_worktree_to_requested_folders()` method that removes any files/directories not in the requested folder list, as a safety net against stale files from previous operations.

## Testing

The fix includes comprehensive tests:

- `test_setup_materializes_only_requested_folder` - Verifies only requested folders are downloaded
- `test_setup_strips_trailing_slashes_from_config` - Handles trailing slashes in config
- `test_prune_removes_stale_files_and_dirs` - Verifies pruning works correctly
- `test_prune_keeps_nested_requested_paths` - Handles nested paths like `src/core/templates/workflows`

## References

- [Git Sparse Checkout Documentation](https://git-scm.com/docs/git-sparse-checkout)
- Issue #4: undesirable folders downloaded
