# Harness Mix Download — Implementation Guide

> Derived from `/grill-me` session on `raw-harness-repo/idea.md`.
> Decision log at end of document.

## Overview

Create a download system that iterates through GitHub repositories listed in a JSON config, downloads or updates each repo using sparse checkout (only specified skill folders), and stores them locally.

### Final Decisions

| # | Axis | Outcome |
|---|---|---|
| 1 | Config format | JSON file (`repos-config.json`) |
| 2 | Config structure | Array of objects with `url` and `skill_folders` |
| 3 | Storage path | `raw-harness-repo/repos/{owner}/{repo}/` (hardcoded) |
| 4 | Empty skill_folders | `SparseCheckoutManager` raises `ValueError` — user must fill before running |
| 5 | SparseCheckoutManager | No modification needed |
| 6 | Error handling | Log errors, continue, report summary at end |
| 7 | Update logic | Check if repo exists → update, if not → download |
| 8 | Helper script | `urls-to-config.py` converts `repo-urls.md` → `repos-config.json` |
| 9 | Main script | `download-repos.py` reads config, downloads/updates repos |

---

## Files to Create

### 1. `repos-config.json`

JSON config file with repo URLs and skill folders.

**Structure:**

```json
{
  "repos": [
    {
      "url": "https://github.com/obra/superpowers.git",
      "skill_folders": []
    },
    {
      "url": "https://github.com/mattpocock/skills.git",
      "skill_folders": []
    },
    {
      "url": "https://github.com/affaan-m/ECC.git",
      "skill_folders": []
    },
    {
      "url": "https://github.com/Fission-AI/OpenSpec.git",
      "skill_folders": []
    },
    {
      "url": "https://github.com/mindfold-ai/Trellis.git",
      "skill_folders": []
    },
    {
      "url": "https://github.com/garrytan/gstack.git",
      "skill_folders": []
    },
    {
      "url": "https://github.com/EveryInc/compound-engineering-plugin.git",
      "skill_folders": []
    }
  ]
}
```

**Notes:**
- `skill_folders` must be non-empty before running `download-repos.py`
- Add skill folder paths as strings (e.g., `["skills", "agents"]`)

---

### 2. `urls-to-config.py`

Helper script to convert `repo-urls.md` → `repos-config.json`.

**Purpose:**
- One-time utility to generate initial config
- Can be re-run if `repo-urls.md` changes

**Implementation:**

```python
"""Convert repo-urls.md to repos-config.json."""
from __future__ import annotations

import json
import re
from pathlib import Path


def parse_repo_urls(urls_file: Path) -> list[dict]:
    """Parse repo-urls.md and return list of repo dicts."""
    repos = []
    content = urls_file.read_text()
    
    # Match URLs in format: * https://github.com/owner/repo.git
    url_pattern = re.compile(r"\*\s+(https://github\.com/[\w-]+/[\w-]+\.git)")
    
    for match in url_pattern.finditer(content):
        url = match.group(1)
        repos.append({
            "url": url,
            "skill_folders": []
        })
    
    return repos


def main() -> None:
    urls_file = Path(__file__).parent / "repo-urls.md"
    config_file = Path(__file__).parent / "repos-config.json"
    
    if not urls_file.exists():
        print(f"Error: {urls_file} not found")
        return
    
    repos = parse_repo_urls(urls_file)
    config = {"repos": repos}
    
    config_file.write_text(json.dumps(config, indent=2) + "\n")
    print(f"Generated {config_file} with {len(repos)} repos")


if __name__ == "__main__":
    main()
```

**Usage:**

```bash
python urls-to-config.py
```

---

### 3. `download-repos.py`

Main script to download/update repositories.

**Purpose:**
- Read `repos-config.json`
- For each repo: check if folder exists → update, if not → download
- Use `SparseCheckoutManager` from `dir-download.py`
- Log errors, continue, report summary at end

**Implementation:**

```python
"""Download or update repositories from repos-config.json."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from dir_download import SparseCheckoutManager


def extract_owner_repo(url: str) -> tuple[str, str]:
    """Extract owner and repo name from GitHub URL."""
    # Match: https://github.com/owner/repo.git
    match = re.match(r"https://github\.com/([\w-]+)/([\w-]+)\.git", url)
    if not match:
        raise ValueError(f"Invalid GitHub URL: {url}")
    return match.group(1), match.group(2)


def get_repo_path(url: str, storage_base: Path) -> Path:
    """Get local path for a repo."""
    owner, repo = extract_owner_repo(url)
    return storage_base / owner / repo


def process_repo(repo_config: dict, storage_base: Path) -> tuple[str, bool, str]:
    """Process a single repo: download or update.
    
    Returns:
        Tuple of (url, success, message)
    """
    url = repo_config["url"]
    skill_folders = repo_config["skill_folders"]
    
    if not skill_folders:
        return (url, False, "skill_folders is empty — fill before running")
    
    repo_path = get_repo_path(url, storage_base)
    
    try:
        manager = SparseCheckoutManager(
            repo_url=url,
            folder_paths=skill_folders,
            local_storage_path=str(repo_path)
        )
        
        if repo_path.exists():
            print(f"Updating: {url}")
            manager.update()
            return (url, True, "Updated successfully")
        else:
            print(f"Downloading: {url}")
            manager.setup()
            return (url, True, "Downloaded successfully")
    
    except Exception as e:
        return (url, False, str(e))


def main() -> None:
    config_file = Path(__file__).parent / "repos-config.json"
    storage_base = Path(__file__).parent / "repos"
    
    if not config_file.exists():
        print(f"Error: {config_file} not found")
        print("Run urls-to-config.py first to generate the config")
        return
    
    config = json.loads(config_file.read_text())
    repos = config.get("repos", [])
    
    if not repos:
        print("No repos in config")
        return
    
    storage_base.mkdir(exist_ok=True)
    
    results = []
    for repo_config in repos:
        result = process_repo(repo_config, storage_base)
        results.append(result)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    successes = [r for r in results if r[1]]
    failures = [r for r in results if not r[1]]
    
    for url, success, message in results:
        status = "✓" if success else "✗"
        print(f"  {status} {url}: {message}")
    
    print(f"\nTotal: {len(results)}, Success: {len(successes)}, Failed: {len(failures)}")
    
    if failures:
        print("\nFailed repos:")
        for url, _, message in failures:
            print(f"  - {url}: {message}")


if __name__ == "__main__":
    main()
```

**Usage:**

```bash
# First time: generate config
python urls-to-config.py

# Edit repos-config.json to add skill_folders

# Download/update repos
python download-repos.py
```

---

## Storage Structure

```
raw-harness-repo/
├── repos/
│   ├── obra/
│   │   └── superpowers/
│   ├── mattpocock/
│   │   └── skills/
│   ├── affaan-m/
│   │   └── ECC/
│   ├── Fission-AI/
│   │   └── OpenSpec/
│   ├── mindfold-ai/
│   │   └── Trellis/
│   ├── garrytan/
│   │   └── gstack/
│   └── EveryInc/
│       └── compound-engineering-plugin/
├── repos-config.json
├── urls-to-config.py
├── download-repos.py
└── dir-download.py
```

---

## Decision Log

```
Q1: Empty folder_paths problem?
    → SparseCheckoutManager raises ValueError — user must fill before running

Q2: Config structure?
    → JSON file with array of objects

Q3: Config format?
    → JSON (no extra dependencies)

Q4: Local storage path?
    → raw-harness-repo/repos/{owner}/{repo}/ (hardcoded)

Q5: Repo folder naming?
    → owner/repo structure

Q6: Script filename?
    → download-repos.py

Q7: Config filename?
    → repos-config.json

Q8: Error handling?
    → Log errors, continue, report summary at end

Q9: repo-urls.md integration?
    → Single source of truth in repos-config.json

Q10: SparseCheckoutManager modification?
    → No modification needed

Q11: Full repo clone behavior?
    → Not needed (skill_folders will be filled)

Q12: Update for full clones?
    → Not needed (skill_folders will be filled)

Q13: Config structure refinement?
    → Array of objects (simpler to iterate)

Q14: Anything else?
    → No

Q15: Helper script location?
    → Separate file (urls-to-config.py)

Q16: Conversion script filename?
    → urls-to-config.py

Q17: Storage path in config?
    → Hardcoded in script

Q18: Storage path value?
    → raw-harness-repo/repos/{owner}/{repo}/
```
