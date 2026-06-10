from __future__ import annotations

from pathlib import Path

from urls_to_config import parse_repo_urls


def test_parse_repo_urls_extracts_urls_from_markdown(tmp_path: Path) -> None:
    markdown_content = """# Repo URLs

* https://github.com/owner1/repo1.git
* https://github.com/owner2/repo2.git
* https://github.com/owner3/repo3.git
"""
    urls_file = tmp_path / "repo-urls.md"
    urls_file.write_text(markdown_content)

    result = parse_repo_urls(urls_file)

    assert len(result) == 3
    assert result[0]["url"] == "https://github.com/owner1/repo1.git"
    assert result[1]["url"] == "https://github.com/owner2/repo2.git"
    assert result[2]["url"] == "https://github.com/owner3/repo3.git"
    for repo in result:
        assert repo["skill_folders"] == []


def test_parse_repo_urls_returns_empty_list_for_no_urls(tmp_path: Path) -> None:
    urls_file = tmp_path / "repo-urls.md"
    urls_file.write_text("# No URLs here\n\nJust some text.\n")

    result = parse_repo_urls(urls_file)

    assert result == []
