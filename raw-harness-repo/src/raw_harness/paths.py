from __future__ import annotations
from pathlib import Path
import os

def make_relative_path(path: str):
    """Convert absolute path to relative path from root."""
    if os.path.isabs(path):
        relative_path = os.path.relpath(path, start='/')
        return relative_path
    return path

def get_project_root() -> Path:
    """Find project root by looking for pyproject.toml."""
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find project root (no pyproject.toml found)")


def get_config_path(filename: str) -> Path:
    """Get path to a config file in the config/ directory."""
    return get_project_root() / "config" / filename
