from __future__ import annotations

import logging
import posixpath
import subprocess
from typing import Protocol

logger = logging.getLogger(__name__)

def _normalize_folder(path: str) -> str:
    """Strip trailing slashes and ensure a single leading slash."""
    cleaned = path.strip().rstrip("/")
    if not cleaned.startswith("/"):
        cleaned = "/" + cleaned
    return cleaned


class GstackSkillDiscovery:
    """Discover skill folders by scanning for `*/SKILL.md` files on the remote."""

    def discover(self, repo_path: str, branch: str) -> list[str]:
        cmd = f'git ls-tree -r origin/{branch} --name-only | grep "/SKILL\\.md$"'
        result = subprocess.run(
            ["/bin/sh", "-c", cmd],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            logger.warning(
                "gstack skill discovery: git ls-tree failed (rc=%s): %s",
                result.returncode,
                result.stderr.strip(),
            )
            return []
        if not result.stdout.strip():
            return []
        folders: set[str] = set()
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            # Convert file path to its parent folder, then normalize.
            folder = posixpath.dirname(line)
            if folder and folder != ".":
                folders.add(_normalize_folder("/" + folder))
        return sorted(folders)


def discover_skill_folders(repo_url: str, repo_path: str, branch: str) -> list[str]:
    """Dispatch to the appropriate strategy for the given repo URL.

    New strategies are added here (not in the strategy module) so the matcher
    can grow without coupling strategy classes to a URL constant.
    """
    return GstackSkillDiscovery().discover(repo_path, branch)