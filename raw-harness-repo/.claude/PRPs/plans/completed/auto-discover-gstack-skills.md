# Plan: Auto-discover gstack skill folders

Issue: https://github.com/livelybug/SDLC-harness-mix-00/issues/8

## Context

GitHub issue [livelybug/SDLC-harness-mix-00#8](https://github.com/livelybug/SDLC-harness-mix-00/issues/8) reports that **gstack's skill and agent files are missing** from the harness output. Root cause: gstack's `SKILL.md` files are distributed across ~50 sibling folders at the repo root (`review/SKILL.md`, `qa/SKILL.md`, `ship/SKILL.md`, `plan-ceo-review/SKILL.md`, …) and the current `repos-config.json` only lists `["/docs/"]` for gstack. Sparse-checkout then materializes only `docs/`, so the actual skill folders are never downloaded.

The user proposed running `git ls-tree` against `origin/HEAD` to discover the skill folder paths, then appending them to the gstack entry's `skill_folders` in `repos-config.json`. This plan reviews that proposal and recommends the final approach.

## Review verdict on the proposed solution

The proposal is **directionally correct** but has three real issues that need correction:

1. **`git ls-tree origin/HEAD` will fail at the proposed injection point.** `origin/HEAD` is a remote-tracking ref that only exists after `git fetch`. The user proposed injecting *immediately after `# Add remote`*, but the current `setup()` flow doesn't fetch until later. We need to move the fetch **earlier** (just after the remote is added and sparse-checkout is enabled) so that `origin/<branch>` exists when `git ls-tree` runs.

2. **Mutating `repos-config.json` on disk is the wrong default.** It creates a stale-by-design config: if gstack upstream adds/removes a skill folder, the persisted JSON drifts. The harness should augment `self.folder_paths` **in memory** and let the static config stay as a human-authored source of truth. If persistence is wanted later, gate it behind an opt-in env var (e.g. `PERSIST_DISCOVERY=1`).

3. **Hard-coding `repo_url == gstack URL`** is brittle. Even if only gstack needs this today, the natural next case is `open-gsd/gsd-core`, `Trellis`, or `superpowers`. Use a per-repo `pre_down_hook` flag in the config so the policy decision lives where humans author it.

Everything else in the proposal (the `git ls-tree` pipeline, `grep '/SKILL\.md$'`, `sort -u`, dedup) is sound and reusable as-is.

## Recommended approach

### Config change: add `pre_down_hook` boolean to repo entries

In `raw-harness-repo/config/repos-config.json` (and `repos-config.json.full`, `repos-config.json.test`), each repo entry may now have a `pre_down_hook: true` flag. When `true`, the manager runs the built-in skill-discovery strategy (currently a single strategy — gstack's `SKILL.md` pattern) for that repo before writing the sparse-checkout file.

Updated gstack entry:
```json
{
  "url": "https://github.com/garrytan/gstack.git",
  "skill_folders": ["/docs/"],
  "pre_down_hook": true
}
```

Keep `/docs/` as a fallback — if discovery fails, `docs/` is still downloaded. Dedup naturally handles any overlap (currently none — gstack's `SKILL.md` folders don't include `docs/`).

The flag defaults to `false` (treated as missing) for any repo that doesn't set it, so existing entries need no change.

### New module: `raw-harness-repo/src/raw_harness/skill_folders.py`

Single responsibility: implement skill-folder discovery.

- `class GstackSkillDiscovery` — runs the user's shell pipeline against the URL it was given (no hard-coded URL constant):
  ```
  git ls-tree -r origin/<branch> --name-only \
    | grep '/SKILL\.md$' \
    | while read -r f; do echo "/$(dirname "$f")"; done \
    | sort -u
  ```
  via `subprocess.run(["/bin/sh", "-c", cmd], cwd=repo_path, capture_output=True, text=True, check=False)`. On non-zero exit or empty stdout, returns `[]`. Path normalization: strip trailing slashes, ensure leading `/`.
- `GSTACK_URL` lives **in the config only** (not in Python code). The strategy takes the URL as a parameter; the matcher (in `dir-download.py`) compares `self.repo_url` to the URL from the config entry to decide whether to invoke the strategy.
- `def discover_skill_folders(repo_url: str, repo_path: str, branch: str) -> list[str]` — dispatcher; for now, if the URL matches the gstack pattern, run `GstackSkillDiscovery`; otherwise return `[]`. (Future strategies are added here, not in a hard-coded URL dict in the strategy module.)

### Modify: `raw-harness-repo/src/raw_harness/dir-download.py`

Reorder `setup()` and add a thin hook runner on `SparseCheckoutManager`:

1. Add `from raw_harness.skill_folders import discover_skill_folders` at the top.
2. Add an instance attribute to `__init__` to hold the hook flag, defaulted to `False`. Since the manager is constructed from a config entry, the caller (`download_repos.py` `process_repo`) will pass it in. (See step 7 below for the orchestrator change.)
3. Add method to `SparseCheckoutManager`:
   ```python
   def run_pre_down_hook(self) -> list[str]:
       """If a pre-down hook is configured for this repo, run it and return extra folder paths."""
       if not self.pre_down_hook:
           return []
       if self._default_branch is None:
           return []
       return discover_skill_folders(self.repo_url, self.repo_path, self._default_branch)
   ```
4. In `setup()`, **move** the `git fetch --depth 1 origin <branch>` block (currently near the end of `setup()`) **up** so it runs immediately after `git config core.sparseCheckout true`. This is the same fetch — moved, not duplicated — so total work is unchanged.
5. Insert after the moved fetch and **before** the sparse-checkout file is written:
   ```python
   extra = self.run_pre_down_hook()
   self.folder_paths = list(dict.fromkeys([*self.folder_paths, *extra]))
   ```
   This dedupes against the static config, preserves insertion order (static first, then discovered), and reassigns (immutable pattern).
6. Leave the existing write-to-sparse-checkout-file block unchanged — it now writes the augmented list.
7. Leave the trailing `git sparse-checkout reapply` and `git checkout` unchanged. The old fetch is removed because the moved fetch (step 4) covers it.

### Modify: `raw-harness-repo/src/raw_harness/download_repos.py`

In `process_repo()` (line 32), pass the new field from the config entry into the manager:
```python
manager = SparseCheckoutManager(
    repo_url=url,
    folder_paths=skill_folders,
    local_storage_path=str(repo_path),
    pre_down_hook=repo_config.get("pre_down_hook", False),
)
```

### Do NOT modify

- `repos-config.json` (only edit the gstack entry to add the flag — same shape as before, no migration needed for other entries).
- `config/features-locations/gstack.md` — reference doc only.
- `update()` — its write-to-sparse-checkout-file block already iterates `self.folder_paths`, so the augmentation persists naturally across `update()` calls (or is re-discovered on a fresh manager, since the orchestrator constructs a new manager per run).

## Test plan

Add to `raw-harness-repo/tests/test_dir_download.py`:

**Unit tests (fast, mocked):**
- `test_run_pre_down_hook_returns_empty_when_flag_false` — manager with `pre_down_hook=False` returns `[]` without subprocess.
- `test_run_pre_down_hook_parses_ls_tree_output` — mock `subprocess.run` to return `review/SKILL.md\nqa/SKILL.md\nqa/extra.md\n`; assert parsed result is `["/review", "/qa"]` (sorted, deduped, no trailing slash).
- `test_run_pre_down_hook_returns_empty_for_non_gstack_url` — `pre_down_hook=True` but URL is superpowers; returns `[]` without subprocess.
- `test_setup_dedupes_discovered_against_static_paths` — `self.folder_paths = ["/docs/", "/review/"]`, discovery returns `["/review", "/qa"]`, final is `["/docs", "/review", "/qa"]` (dedup, no trailing slash).
- `test_run_pre_down_hook_handles_ls_tree_failure` — mock `subprocess.run` to raise; assert returns `[]` and `setup()` continues with the original static paths.
- `test_setup_writes_augmented_sparse_checkout_file` — mock all subprocess calls; assert `.git/info/sparse-checkout` file contains the union of static + discovered paths.

**Integration test (slow, real network, mark `@pytest.mark.integration`):**
- `test_gstack_includes_skill_folders` — clone `https://github.com/garrytan/gstack.git` into `tmp_path` with `pre_down_hook=True`; assert `repo_path / "review" / "SKILL.md"` and `repo_path / "docs"` both exist. Pattern matches the existing superpowers integration tests at the top of `test_dir_download.py`.

Also add a test to `tests/test_download_repos.py` to confirm `process_repo` passes `pre_down_hook` through to the manager (mock the manager and assert constructor args).

Minimum viable: the augmented-write unit test (covers end-to-end with mocks). The integration test is high-value but slow.

## Edge cases to handle

1. `pre_down_hook` missing from config entry → treated as `False` (default in `repo_config.get("pre_down_hook", False)` at the call site and in the manager's `__init__`).
2. `git ls-tree` returns nothing → return `[]`, don't fail.
3. `git ls-tree` fails (network blip, branch moved) → catch exception, log warning, return `[]`. Discovery is opportunistic; a broken discovery must not break a working static config.
4. Discovered path collides with static `/docs/` → dedup handles it.
5. Trailing slash inconsistency (static uses `/docs/`, pipeline emits `/review`) → canonicalize to no-trailing-slash in memory; the existing `os.path.join(folder, '')` in the sparse-checkout writer re-adds trailing slashes on write.
6. OpenSpec's skills are TypeScript templates (not `.md` files, per `config/features-locations/OpenSpec.md`) → out of scope; **do not** set `pre_down_hook: true` on OpenSpec — it would silently discover nothing and confuse operators. (Will be obvious to anyone reading the config because the entry has no flag.)
7. `git ls-tree` may not match if upstream ever moves SKILL.md outside the `*/SKILL.md` pattern — `_verify_paths_exist()` will catch a missing discovered folder and raise `FileNotFoundError`, which surfaces as a clean per-repo failure in `download_repos.py`'s `process_repo()`.
8. `pre_down_hook: true` on a repo whose URL isn't matched by any registered strategy → returns `[]` silently. Add a `print` warning so it's visible in logs.

## Critical files

- `/home/burt/p2/src/AI/SDLC-harness-mix/raw-harness-repo/src/raw_harness/dir-download.py` — modify `setup()` flow, add a method, add a constructor param.
- `/home/burt/p2/src/AI/SDLC-harness-mix/raw-harness-repo/src/raw_harness/skill_folders.py` — **new** file (~50 lines): strategy, dispatcher.
- `/home/burt/p2/src/AI/SDLC-harness-mix/raw-harness-repo/src/raw_harness/download_repos.py` — pass `pre_down_hook` into the manager constructor.
- `/home/burt/p2/src/AI/SDLC-harness-mix/raw-harness-repo/config/repos-config.json` — add `"pre_down_hook": true` to the gstack entry (and `.full`, `.test`).
- `/home/burt/p2/src/AI/SDLC-harness-mix/raw-harness-repo/tests/test_dir_download.py` — add 6 unit tests + 1 integration test.
- `/home/burt/p2/src/AI/SDLC-harness-mix/raw-harness-repo/tests/test_download_repos.py` — add 1 test for hook pass-through.

## Step-by-step implementation order

1. Add the 6 unit tests to `test_dir_download.py` (RED — they should fail because `run_pre_down_hook` doesn't exist yet) and 1 pass-through test to `test_download_repos.py`.
2. Create `skill_folders.py` with the strategy and dispatcher (URL is a parameter, not a constant). Run the new unit tests — they should pass for the strategy module (GREEN).
3. Modify `dir-download.py`: add import, add `pre_down_hook` param to `__init__`, add `run_pre_down_hook()` method, move the fetch block earlier in `setup()`, insert the in-memory augmentation. Run all unit tests (GREEN).
4. Modify `download_repos.py`: pass `pre_down_hook` from config entry into the manager constructor. Run all unit tests (GREEN).
5. Update `config/repos-config.json` (and `.full`, `.test`): add `"pre_down_hook": true` to the gstack entry only.
6. Add the integration test to `test_dir_download.py` (gated by `@pytest.mark.integration`).
7. Run `pytest raw-harness-repo/tests/ -m "not integration"` and confirm unit tests pass.
8. Run the integration test against the test config (`repos-config.json.test`) to confirm gstack skill folders are materialized.
9. Run `black`, `isort`, `ruff` on modified files (per project `python/coding-style.md`).
10. Refactor (IMPROVE) — if the new code has duplication, magic strings, or unclear names, clean them up. Re-run unit tests.
11. Update the issue close-out referencing the new module.

## Verification

End-to-end check (manual, against the gstack-only test config):
```bash
cd /home/burt/p2/src/AI/SDLC-harness-mix/raw-harness-repo
REPOS_CONFIG_FILE=repos-config.json.test python -m raw_harness.download_repos
ls repos/garrytan/gstack/ | head
# expect: docs, review, qa, ship, investigate, office-hours, plan-ceo-review, ... (50+ folders)
test -f repos/garrytan/gstack/review/SKILL.md && echo "PASS: gstack skills materialized"
test -d repos/garrytan/gstack/docs && echo "PASS: gstack docs materialized"
```

Expected: both checks pass. The harness now self-discovers gstack's distributed skill folders via the `pre_down_hook: true` flag, while preserving the human-authored `/docs/` entry from the static config.
