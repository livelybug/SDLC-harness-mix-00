# Harness Mix Download

Downloads AI agent skill folders from GitHub repositories using sparse checkout.

## Prerequisites

- Python 3.10+
- Git

## Quick Start

```bash
cd raw-harness-repo

# Download all repos
python3 download_repos.py
```

## Configuration

Edit `repos-config.json` to add or modify repositories:

```json
{
  "repos": [
    {
      "url": "https://github.com/owner/repo.git",
      "skill_folders": ["path/to/skills"]
    }
  ]
}
```

**Important:** 
- `skill_folders` must be non-empty for each repo

## Files

| File | Purpose                                          |
|------|--------------------------------------------------|
| `repos-config.json` | Repository URLs and skill folder paths           |
| `download_repos.py` | Main script - downloads/updates repos            |
| `dir-download.py` | SparseCheckoutManager implementation             |
| `urls_to_config.py` | Helper: converts `repo-urls.md` to config        |
| `utils/git-archive.py` | Archive/restore `.git` folders for index cleanup |
| `test_download_repos.py` | Tests for download_repos.py                      |
| `test_urls_to_config.py` | Tests for urls_to_config.py                      |
| `utils/test_git_archive.py` | Tests for git-archive.py                         |

## Testing

Run all tests:
```bash
python3 -m pytest test_download_repos.py test_urls_to_config.py utils/test_git_archive.py -v
```

Run with coverage:
```bash
python3 -m pytest test_download_repos.py test_urls_to_config.py utils/test_git_archive.py --cov=. --cov-report=term-missing
```

## Storage Structure

Downloaded repos are stored in:
```
repos/
├── owner1/
│   └── repo1/
│       └── skills/
├── owner2/
│   └── repo2/
│       └── skills/
```

## Update Existing Repos

Run the same command to update:
```bash
python3 download_repos.py
```

The script detects existing repos and runs `git pull` instead of cloning.

## `.git` Management

Archived `.git` folders can cause noise when indexing `raw-harness-repo/repos`. Use `git-archive.py` to move them:

```bash
cd raw-harness-repo

# Archive .git folders to .tmp_store/git-folders.tar.gz (deletes originals)
python3 utils/git-archive.py move

# Restore .git folders from archive
python3 utils/git-archive.py restore
```

**What it does:**
- `move`: Walks `repos/{owner}/{repo}/` for `.git` dirs, creates `.tmp_store/git-folders.tar.gz`, deletes originals
- `restore`: Extracts archive back to original locations (overwrites existing `.git` dirs)

## Troubleshooting

**"skill_folders is empty"**  
→ Edit `repos-config.json` and add folder paths

**"Folders not found in repo after checkout"**  
→ Check that folder paths exist in the remote repository  
→ Ensure paths do NOT have trailing slashes

**"Invalid GitHub URL"**  
→ URL must match: `https://github.com/owner/repo.git`
