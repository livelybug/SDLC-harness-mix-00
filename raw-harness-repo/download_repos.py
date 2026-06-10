from __future__ import annotations

import importlib
import json
import re
import sys
from pathlib import Path

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