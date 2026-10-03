"""
Controlled workspace manager for cloned repositories.
"""

import re
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from .exceptions import WorkspaceError


class WorkspaceManager:
    """
    Manages controlled local workspaces for external repository cloning.
    Ensures repositories are kept safely outside the RepoPilot project directory.
    """

    def __init__(self, workspace_root: Optional[str | Path] = None):
        if workspace_root is None:
            # Default to dedicated temp workspace directory outside the source tree
            self._workspace_root = (Path(tempfile.gettempdir()) / "repopilot_workspaces").resolve()
        else:
            self._workspace_root = Path(workspace_root).resolve()

        self._ensure_workspace_root()

    @property
    def workspace_root(self) -> Path:
        """Returns the normalized workspace root path."""
        return self._workspace_root

    def _ensure_workspace_root(self) -> None:
        """Creates the workspace root directory if it does not exist."""
        try:
            self._workspace_root.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise WorkspaceError(f"Failed to create workspace root directory at '{self._workspace_root}': {e}")

    def prepare_clone_directory(self, owner: str, repo: str, clean_existing: bool = True) -> Path:
        """
        Prepares and returns a controlled, isolated target path for a repository.

        Args:
            owner: The GitHub repository owner.
            repo: The GitHub repository name.
            clean_existing: If True, removes any pre-existing directory at the target path.

        Returns:
            Path: The resolved target directory path inside the workspace.
        """
        # Sanitize owner and repo names to prevent path injection
        safe_owner = re.sub(r"[^a-zA-Z0-9_.-]", "_", owner)
        safe_repo = re.sub(r"[^a-zA-Z0-9_.-]", "_", repo)

        target_dir = (self._workspace_root / safe_owner / safe_repo).resolve()

        # Path safety check: target must be strictly inside workspace_root
        try:
            target_dir.relative_to(self._workspace_root)
        except ValueError:
            raise WorkspaceError(f"Target clone path '{target_dir}' escapes workspace root '{self._workspace_root}'")

        if clean_existing and target_dir.exists():
            try:
                shutil.rmtree(target_dir)
            except Exception as e:
                raise WorkspaceError(f"Failed to clean existing directory at '{target_dir}': {e}")

        return target_dir

    def cleanup_directory(self, path: str | Path) -> None:
        """Safely removes a repository directory inside the workspace."""
        try:
            path_obj = Path(path).resolve()
        except Exception:
            return

        try:
            path_obj.relative_to(self._workspace_root)
        except ValueError:
            raise WorkspaceError(f"Refusing to delete path '{path_obj}' outside workspace root '{self._workspace_root}'")

        if path_obj.exists():
            shutil.rmtree(path_obj, ignore_errors=True)
