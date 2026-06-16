# Harness Mix Download

Downloads AI agent skill folders from GitHub repositories using sparse checkout.

## Prerequisites

- Python 3.10+
- Git

## Quick Start

```bash
cd raw-harness-repo
source .venv/bin/activate

# Install the package in development mode
pip install -e .

# Download all repos
python3 -m raw_harness.download_repos
```

## Configuration

Edit `config/repos-config.json` to add or modify repositories:

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

### Config file location

By default, `download_repos.py` reads `config/repos-config.json`. To use a different config file, set the `REPOS_CONFIG_FILE` environment variable to the filename (e.g. `custom-config.json`); the file is still resolved relative to `config/`. Values from a `.env` file in the project root are loaded first; shell-exported env vars take precedence over `.env`.

```bash
# .env in the project root
REPOS_CONFIG_FILE=repos-config.json
```

## Project Structure

```
raw-harness-repo/
├── src/raw_harness/          # Python package
│   ├── __init__.py
│   ├── paths.py              # Project root discovery
│   ├── download_repos.py     # Main download script
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── git_archive.py    # Archive/restore .git folders
│   │   └── urls_to_config.py # URL to config converter
├── tests/                    # Test files
├── config/                   # Configuration files
│   ├── repo-urls.md          # Source URLs
│   └── repos-config.json     # Generated config
├── docs/                     # Documentation
└── pyproject.toml            # Package configuration
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

## Testing

Run all tests:
```bash
python3 -m pytest
```

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

## Troubleshooting

**"skill_folders is empty"**  
→ Edit `config/repos-config.json` and add folder paths

**"Folders not found in repo after checkout"**  
→ Check that folder paths exist in the remote repository  
→ Ensure paths do NOT have trailing slashes

**"Invalid GitHub URL"**  
→ URL must match: `https://github.com/owner/repo.git`
