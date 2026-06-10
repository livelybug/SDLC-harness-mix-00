from __future__ import annotations

import json
import re
from pathlib import Path


def parse_repo_urls(urls_file: Path) -> list[dict]:
    repos = []
    content = urls_file.read_text()
    
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
