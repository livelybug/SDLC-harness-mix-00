from __future__ import annotations

import os
import shutil
import subprocess
from raw_harness.paths import make_relative_path
from raw_harness.skill_folders import discover_skill_folders

class SparseCheckoutManager:
    def __init__(
        self,
        repo_url: str,
        folder_paths: list[str],
        local_storage_path: str,
        pre_down_hook: bool = False,
    ):
        """
        Manage sparse checkouts of multiple GitHub folders from a single repo.

        Args:
            repo_url: "https://github.com/username/repo.git"
            folder_paths: List of folder paths, e.g. ["pandas/io", "pandas/core"]
            local_storage_path: Where to store the git repo (persistent)
            pre_down_hook: When True, run skill-folder discovery before writing
                the sparse-checkout file. Default is False.
        """
        if not folder_paths:
            raise ValueError("folder_paths must be non-empty")
        self.repo_url = repo_url
        self.folder_paths = list(folder_paths)       # defensive copy
        self.repo_path = local_storage_path
        self.pre_down_hook = pre_down_hook
        self._default_branch: str | None = None       # detected in setup()

    def _detect_default_branch(self) -> str:
        """Query remote HEAD to determine default branch name."""
        result = subprocess.run(
            ["git", "ls-remote", "--symref", "origin", "HEAD"],
            cwd=self.repo_path,
            capture_output=True, text=True, check=True
        )
        # Output format: "ref: refs/heads/main\tHEAD\n<hash>\tHEAD\n"
        for line in result.stdout.strip().split("\n"):
            if line.startswith("ref:") and "HEAD" in line:
                # line like: "ref: refs/heads/main\tHEAD"
                ref = line.split("\t")[0]         # "ref: refs/heads/main"
                branch = ref.split("/")[-1]        # "main"
                return branch
        raise RuntimeError(f"Could not detect default branch for {self.repo_url}")

    def run_pre_down_hook(self) -> list[str]:
        """If a pre-down hook is configured for this repo, run it and return extra folder paths.

        Returns an empty list when the hook is disabled, when the default
        branch has not been detected yet, or when no strategy matches the
        repo URL. Discovery failures are logged and treated as a no-op so a
        broken discovery never breaks a working static config.
        """
        if not self.pre_down_hook:
            return []
        if self._default_branch is None:
            return []
        try:
            extra = discover_skill_folders(
                self.repo_url, self.repo_path, self._default_branch
            )
        except Exception as exc:
            print(
                f"Warning: pre_down_hook failed for {self.repo_url}: {exc}. "
                "Falling back to static config."
            )
            return []
        if not extra:
            # Flag is on but no skill folder matched — surface it so operators notice.
            print(
                f"Warning: pre_down_hook is True for {self.repo_url} "
                "but no skill-folder discovery strategy matches this URL."
            )
        return extra

    def setup(self) -> None:
        """Initial setup of sparse checkout for all requested folders."""
        if os.path.exists(self.repo_path):
            print(f"Repository already exists at {self.repo_path}")
            return

        os.makedirs(self.repo_path, exist_ok=True)

        # Initialize git repo
        subprocess.run(["git", "init"],
                    cwd=self.repo_path, text=True, check=True)

        # Add remote
        subprocess.run(
            ["git", "remote", "add", "origin", self.repo_url],
            cwd=self.repo_path, text=True, check=True
        )

        # Auto-detect default branch (must happen after `git remote add`)
        self._default_branch = self._detect_default_branch()
        # print("self._default_branch", self._default_branch)

        # Enable sparse checkout
        subprocess.run(
            ["git", "config", "core.sparseCheckout", "true"],
            cwd=self.repo_path, text=True, check=True
        )

        # Fetch the default branch early so the pre_down_hook (if any) can run
        # `git ls-tree origin/<branch>` against a real remote-tracking ref.
        subprocess.run(
            ["git", "fetch", "--depth", "1", "origin", self._default_branch],
            cwd=self.repo_path, text=True, check=True
        )

        # Run pre-down hook (e.g. skill-folder discovery) and merge results
        # in-memory. The static config on disk is never mutated.
        extra = self.run_pre_down_hook()
        if extra:
            self.folder_paths = list(dict.fromkeys([*self.folder_paths, *extra]))

        # Write ALL folder paths to sparse-checkout file (one per line)
        sparse_path = os.path.join(self.repo_path, ".git", "info", "sparse-checkout")
        with open(sparse_path, "w") as f:
            for folder in self.folder_paths:
                folder=os.path.join(folder, '')
                f.write(f"{folder}\n")

        subprocess.run(
            ["git", "sparse-checkout", "reapply"],
            cwd=self.repo_path, text=True, check=True
        )

        subprocess.run(
            ["git", "checkout", self._default_branch],
            cwd=self.repo_path, text=True, check=True
        )

        # self._prune_worktree_to_requested_folders()  # Todo: to test and enable
        self._verify_paths_exist()

        paths_display = ", ".join(self.folder_paths)
        print(f"Initial setup complete. Folders available under {self.repo_path}/")
        print(f"  ({paths_display})")

    def _verify_paths_exist(self) -> None:
        """Raise error if any requested folder is missing after checkout."""
        missing = []
        for folder in self.folder_paths:
            folder = make_relative_path(folder)
            full_path = os.path.join(self.repo_path, folder)
            if not os.path.isdir(full_path):
                missing.append(folder)
        if missing:
            raise FileNotFoundError(
                f"Folders not found in repo after checkout: {missing}\n"
                f"Repo: {self.repo_url}\n"
                f"Check that all paths exist on remote."
            )

    def _prune_worktree_to_requested_folders(self) -> None:
        """Delete worktree entries outside the requested folders.

        Non-cone sparse-checkout does not evict files left over from a prior
        full checkout, so we remove anything not under one of the requested
        folder paths (issue #4).
        """
        keep = {os.path.normpath(f.rstrip("/")) for f in self.folder_paths}
        for entry in os.listdir(self.repo_path):
            if entry == ".git":
                continue
            entry_norm = os.path.normpath(entry)
            if entry_norm in keep:
                continue
            if any(p == entry_norm or p.startswith(entry_norm + os.sep)
                   for p in keep):
                continue
            target = os.path.join(self.repo_path, entry)
            if os.path.isdir(target):
                shutil.rmtree(target)
            else:
                os.remove(target)

    def update(self) -> str:  # Todo: dedup with setup(self)
        """Update all folders to the latest version."""
        if not os.path.exists(self.repo_path):
            raise RuntimeError("Repository not found. Run setup() first.")

        # Detect branch if not already cached (e.g. repo existed before this code upgrade)
        if self._default_branch is None:
            self._default_branch = self._detect_default_branch()

        # Write ALL folder paths to sparse-checkout file (one per line) # Todo: dedup
        sparse_path = os.path.join(self.repo_path, ".git", "info", "sparse-checkout")
        with open(sparse_path, "w") as f:
            for folder in self.folder_paths:
                folder=os.path.join(folder, '')
                f.write(f"{folder}\n")

        # Re-apply sparsity so any newly-removed upstream paths are pruned  # Todo: to verify
        subprocess.run(
            ["git", "sparse-checkout", "reapply"],
            cwd=self.repo_path, text=True, check=True
        )

        # Pull updates (only affects sparse checkout folders)
        result = subprocess.run(
            ["git", "pull", "--depth", "1", "origin", self._default_branch],
            cwd=self.repo_path, capture_output=True, text=True
        )

        if "Already up to date" in result.stdout:
            print("Folders are already up to date")
        else:
            print("Update completed successfully")
            print(result.stdout)

        # Re-verify after update (paths could have been removed upstream)
        self._verify_paths_exist()

        return result.stdout

    def get_folder_paths(self) -> list[str]:
        """Get absolute paths to all checked out folders.

        Returns:
            List of paths like ["/abs/path/repo/pandas/io", "/abs/path/repo/pandas/core"]
        """
        return [os.path.join(self.repo_path, f) for f in self.folder_paths]

    def copy_to_output(self, output_path: str) -> None:
        """Copy all checked-out folders to another location, preserving relative paths.

        Example:
            If folder_paths = ["pandas/io", "pandas/core"] and output_path = "./out":
            Result: ./out/pandas/io/  and  ./out/pandas/core/

            If folder_paths = ["src/backend", "docs/api"] and output_path = "./out":
            Result: ./out/src/backend/  and  ./out/docs/api/
        """
        for source in self.get_folder_paths():
            if not os.path.exists(source):
                raise FileNotFoundError(
                    f"Source folder not found: {source}. Run setup() or update() first."
                )

            # Compute destination preserving relative structure
            rel_dir = os.path.relpath(source, self.repo_path)
            dest = os.path.join(output_path, rel_dir)

            if os.path.exists(dest):
                shutil.rmtree(dest)

            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copytree(source, dest)
            print(f"Copied {rel_dir} -> {dest}")


if __name__ == "__main__":
    # --- Example: single directory (still works) ---
    manager_single = SparseCheckoutManager(
        repo_url="https://github.com/pandas-dev/pandas.git",
        folder_paths=["pandas/io"],
        local_storage_path="./my_sparse_repo"
    )
    # manager_single.setup()

    # --- Example: multiple directories ---
    manager_multi = SparseCheckoutManager(
        repo_url="https://github.com/pandas-dev/pandas.git",
        folder_paths=[
            "pandas/io",
            "pandas/core",
            "pandas/api",
        ],
        local_storage_path="./my_sparse_repo_multi"
    )
    # manager_multi.setup()
    # manager_multi.update()
    # manager_multi.copy_to_output("./pandas_latest")
