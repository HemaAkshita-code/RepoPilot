"""
Local repository loader for Stage 2.
"""

import os
from pathlib import Path
from .models import Repository
from .exceptions import LocalRepositoryError


def load_local_repository(path: str | Path) -> Repository:
    """
    Loads and validates a local filesystem directory as a repository.

    Args:
        path: Path to local directory.

    Returns:
        Repository: A Repository abstraction object.

    Raises:
        LocalRepositoryError: If path does not exist, is a file, or is inaccessible.
    """
    if not path:
        raise LocalRepositoryError("Local repository path cannot be empty.")

    try:
        path_obj = Path(path).resolve()
    except Exception as e:
        raise LocalRepositoryError(f"Invalid local repository path format: {e}")

    if not path_obj.exists():
        raise LocalRepositoryError(f"Local repository path does not exist: '{path}'")

    if not path_obj.is_dir():
        raise LocalRepositoryError(f"Local repository path is a file, not a directory: '{path}'")

    # Accessibility check: attempt to test readability
    if not os.access(path_obj, os.R_OK):
        raise LocalRepositoryError(f"Local repository directory is not accessible/readable: '{path}'")

    return Repository(root_path=path_obj, source_type="local")
