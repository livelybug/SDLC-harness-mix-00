from __future__ import annotations

import importlib
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

from raw_harness.paths import get_config_path, get_project_root
from raw_harness.utils.git_archive import move_git_folders, restore_git_folders

sys.path.insert(0, str(Path(__file__).parent))
dir_download = importlib.import_module("dir-download")
SparseCheckoutManager = dir_download.SparseCheckoutManager


def extract_owner_repo(url: str) -> tuple[str, str]:
    match = re.match(r"https://github\.com/([\w-]+)/([\w-]+)\.git", url)
    if not match:
        raise ValueError(f"Invalid GitHub URL: {url}")
    return match.group(1), match.group(2)


def get_repo_path(url: str, storage_base: Path) -> Path:
    owner, repo = extract_owner_repo(url)
    return storage_base / owner / repo


def process_repo(repo_config: dict, storage_base: Path) -> tuple[str, bool, str]:
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
            manager.update()
            return (url, True, "Updated successfully")
        else:
            manager.setup()
            return (url, True, "Downloaded successfully")
    
    except Exception as e:
        return (url, False, str(e))


def main() -> None:
    load_dotenv(get_project_root() / ".env")
    config_name = os.environ.get("REPOS_CONFIG_FILE", "repos-config.json")
    config_file = get_config_path(config_name)
    
    if not config_file.exists():
        print(f"Error: {config_file} not found")
        print("Run urls-to-config.py first to generate the config")
        return
    
    config = json.loads(config_file.read_text())
    settings = config.get("settings", {})
    repos = config.get(settings.get("repos_key", "repos"), [])
    storage_base = get_project_root() / settings.get("storage_dir", "repos")
    
    if not repos:
        print("No repos in config")
        return
    
    storage_base.mkdir(exist_ok=True)
    
    # Restore .git folders if archive exists (so git operations can work)
    archive_path = (
        get_project_root()
        / settings.get("git_archive_dir", ".tmp_store")
        / settings.get("git_archive_filename", "git-folders.tar.gz")
    )
    if archive_path.exists():
        try:
            restore_git_folders()
        except Exception as e:
            print(f"Warning: Failed to restore .git folders: {e}")
    
    results = []
    for repo_config in repos:
        result = process_repo(repo_config, storage_base)
        results.append(result)
    
    # Archive .git folders (clean up for indexing)
    try:
        move_git_folders()
    except Exception as e:
        print(f"Warning: Failed to archive .git folders: {e}")
    
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