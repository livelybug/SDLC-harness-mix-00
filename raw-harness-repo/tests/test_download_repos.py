from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from raw_harness.download_repos import extract_owner_repo, get_repo_path, main, process_repo


def test_extract_owner_repo_parses_valid_github_url() -> None:
    url = "https://github.com/obra/superpowers.git"
    
    owner, repo = extract_owner_repo(url)
    
    assert owner == "obra"
    assert repo == "superpowers"


def test_extract_owner_repo_raises_value_error_for_invalid_url() -> None:
    url = "https://example.com/not-github"
    
    with pytest.raises(ValueError, match="Invalid GitHub URL"):
        extract_owner_repo(url)


def test_get_repo_path_returns_correct_path() -> None:
    url = "https://github.com/obra/superpowers.git"
    storage_base = Path("/tmp/repos")
    
    result = get_repo_path(url, storage_base)
    
    assert result == Path("/tmp/repos/obra/superpowers")


def test_process_repo_returns_error_for_empty_skill_folders() -> None:
    repo_config = {
        "url": "https://github.com/obra/superpowers.git",
        "skill_folders": []
    }
    storage_base = Path("/tmp/repos")
    
    url, success, message = process_repo(repo_config, storage_base)
    
    assert url == "https://github.com/obra/superpowers.git"
    assert success is False
    assert "skill_folders is empty" in message


@patch("raw_harness.download_repos.SparseCheckoutManager")
@patch("raw_harness.download_repos.Path.exists")
def test_process_repo_calls_setup_for_new_repo(
    mock_exists: MagicMock, mock_manager_class: MagicMock
) -> None:
    mock_exists.return_value = False
    mock_manager = MagicMock()
    mock_manager_class.return_value = mock_manager
    
    repo_config = {
        "url": "https://github.com/obra/superpowers.git",
        "skill_folders": ["skills"]
    }
    storage_base = Path("/tmp/repos")
    
    url, success, message = process_repo(repo_config, storage_base)
    
    assert url == "https://github.com/obra/superpowers.git"
    assert success is True
    assert "Downloaded" in message
    mock_manager.setup.assert_called_once()


@patch("raw_harness.download_repos.SparseCheckoutManager")
@patch("raw_harness.download_repos.Path.exists")
def test_process_repo_calls_update_for_existing_repo(
    mock_exists: MagicMock, mock_manager_class: MagicMock
) -> None:
    mock_exists.return_value = True
    mock_manager = MagicMock()
    mock_manager_class.return_value = mock_manager
    
    repo_config = {
        "url": "https://github.com/obra/superpowers.git",
        "skill_folders": ["skills"]
    }
    storage_base = Path("/tmp/repos")
    
    url, success, message = process_repo(repo_config, storage_base)
    
    assert url == "https://github.com/obra/superpowers.git"
    assert success is True
    assert "Updated" in message
    mock_manager.update.assert_called_once()


@patch("raw_harness.download_repos.SparseCheckoutManager")
@patch("raw_harness.download_repos.Path.exists")
def test_process_repo_returns_failure_on_exception(
    mock_exists: MagicMock, mock_manager_class: MagicMock
) -> None:
    mock_exists.return_value = False
    mock_manager = MagicMock()
    mock_manager.setup.side_effect = Exception("Git error")
    mock_manager_class.return_value = mock_manager
    
    repo_config = {
        "url": "https://github.com/obra/superpowers.git",
        "skill_folders": ["skills"]
    }
    storage_base = Path("/tmp/repos")
    
    url, success, message = process_repo(repo_config, storage_base)
    
    assert url == "https://github.com/obra/superpowers.git"
    assert success is False
    assert "Git error" in message


def test_main_prints_error_when_config_missing(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    mock_config_file = MagicMock()
    mock_config_file.exists.return_value = False
    mock_config_file.__str__ = lambda self: "/tmp/repos-config.json"
    
    with patch("raw_harness.download_repos.get_config_path", return_value=mock_config_file):
        main()
    
    captured = capsys.readouterr()
    assert "not found" in captured.out


def test_main_prints_summary_with_counts(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    config_content = {
        "repos": [
            {
                "url": "https://github.com/owner1/repo1.git",
                "skill_folders": ["skills"]
            },
            {
                "url": "https://github.com/owner2/repo2.git",
                "skill_folders": []
            }
        ]
    }
    config_file = tmp_path / "repos-config.json"
    config_file.write_text(json.dumps(config_content))
    
    def mock_get_config_path(name: str) -> Path:
        if name == "repos-config.json":
            return config_file
        return tmp_path / name
    
    with patch("raw_harness.download_repos.get_config_path", side_effect=mock_get_config_path):
        with patch("raw_harness.download_repos.process_repo") as mock_process:
            mock_process.side_effect = [
                ("https://github.com/owner1/repo1.git", True, "Downloaded successfully"),
                ("https://github.com/owner2/repo2.git", False, "skill_folders is empty")
            ]
            main()
    
    captured = capsys.readouterr()
    assert "SUMMARY" in captured.out
    assert "Total: 2" in captured.out
    assert "Success: 1" in captured.out
    assert "Failed: 1" in captured.out


def test_main_uses_default_config_name_when_env_unset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.delenv("REPOS_CONFIG_FILE", raising=False)

    requested: list[str] = []

    def mock_get_config_path(name: str) -> Path:
        requested.append(name)
        mock_file = MagicMock()
        mock_file.exists.return_value = False
        mock_file.__str__ = lambda self: f"/tmp/{name}"
        return mock_file

    with patch("raw_harness.download_repos.get_config_path", side_effect=mock_get_config_path):
        main()

    assert requested == ["repos-config.json"]
    captured = capsys.readouterr()
    assert "not found" in captured.out


def test_main_reads_config_name_from_env_var(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setenv("REPOS_CONFIG_FILE", "custom-config.json")

    requested: list[str] = []

    def mock_get_config_path(name: str) -> Path:
        requested.append(name)
        mock_file = MagicMock()
        mock_file.exists.return_value = False
        mock_file.__str__ = lambda self: f"/tmp/{name}"
        return mock_file

    with patch("raw_harness.download_repos.get_config_path", side_effect=mock_get_config_path):
        main()

    assert requested == ["custom-config.json"]


def test_main_loads_env_file_from_project_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("REPOS_CONFIG_FILE=from-dotenv.json\n# comment\n\nBAD LINE\n")
    monkeypatch.delenv("REPOS_CONFIG_FILE", raising=False)

    requested: list[str] = []

    def mock_get_config_path(name: str) -> Path:
        requested.append(name)
        mock_file = MagicMock()
        mock_file.exists.return_value = False
        mock_file.__str__ = lambda self: f"/tmp/{name}"
        return mock_file

    def mock_get_project_root() -> Path:
        return tmp_path

    with patch("raw_harness.download_repos.get_project_root", side_effect=mock_get_project_root):
        with patch("raw_harness.download_repos.get_config_path", side_effect=mock_get_config_path):
            main()

    assert requested == ["from-dotenv.json"]


def test_main_env_var_overrides_env_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("REPOS_CONFIG_FILE=from-dotenv.json\n")
    monkeypatch.setenv("REPOS_CONFIG_FILE", "from-shell.json")

    requested: list[str] = []

    def mock_get_config_path(name: str) -> Path:
        requested.append(name)
        mock_file = MagicMock()
        mock_file.exists.return_value = False
        mock_file.__str__ = lambda self: f"/tmp/{name}"
        return mock_file

    def mock_get_project_root() -> Path:
        return tmp_path

    with patch("raw_harness.download_repos.get_project_root", side_effect=mock_get_project_root):
        with patch("raw_harness.download_repos.get_config_path", side_effect=mock_get_config_path):
            main()

    assert requested == ["from-shell.json"]


@patch("raw_harness.download_repos.SparseCheckoutManager")
@patch("raw_harness.download_repos.Path.exists")
def test_process_repo_passes_pre_down_hook_to_manager(
    mock_exists: MagicMock, mock_manager_class: MagicMock
) -> None:
    """pre_down_hook from the config entry is forwarded to SparseCheckoutManager."""
    mock_exists.return_value = False
    mock_manager = MagicMock()
    mock_manager_class.return_value = mock_manager

    repo_config = {
        "url": "https://github.com/garrytan/gstack.git",
        "skill_folders": ["/docs/"],
        "pre_down_hook": True,
    }
    storage_base = Path("/tmp/repos")

    process_repo(repo_config, storage_base)

    mock_manager_class.assert_called_once_with(
        repo_url="https://github.com/garrytan/gstack.git",
        folder_paths=["/docs/"],
        local_storage_path="/tmp/repos/garrytan/gstack",
        pre_down_hook=True,
    )


@patch("raw_harness.download_repos.SparseCheckoutManager")
@patch("raw_harness.download_repos.Path.exists")
def test_process_repo_defaults_pre_down_hook_false_when_missing(
    mock_exists: MagicMock, mock_manager_class: MagicMock
) -> None:
    """pre_down_hook is False when not present in the config entry."""
    mock_exists.return_value = False
    mock_manager_class.return_value = MagicMock()

    repo_config = {
        "url": "https://github.com/obra/superpowers.git",
        "skill_folders": ["skills"],
    }
    storage_base = Path("/tmp/repos")

    process_repo(repo_config, storage_base)

    _, kwargs = mock_manager_class.call_args
    assert kwargs["pre_down_hook"] is False