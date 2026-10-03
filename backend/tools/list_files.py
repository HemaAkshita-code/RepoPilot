"""
list_files tool implementation for Stage 2.
"""

import os
from pathlib import Path
from typing import Union, List, Dict, Any

from backend.repository.models import Repository
from .security import get_canonical_root, DEFAULT_IGNORED_DIRS


def list_files(
    repo_root: Union[str, Path, Repository],
    max_files: int = 10_000,
) -> Dict[str, Any]:
    """
    Recursively inspects the configured repository and returns all repository-relative file paths.

    Args:
        repo_root: The repository root (Path, string, or Repository object).
        max_files: Maximum number of file paths to return.

    Returns:
        Dict[str, Any]: Structured dictionary with "files", "count", and "truncated".
    """
    try:
        root_path = get_canonical_root(repo_root)
    except Exception as e:
        return {
            "files": [],
            "count": 0,
            "truncated": False,
            "error": str(e),
        }

    discovered_files: List[str] = []
    truncated = False

    for dirpath, dirnames, filenames in os.walk(root_path, followlinks=False):
        # Prune ignored directories in-place
        dirnames[:] = [
            d for d in dirnames
            if d not in DEFAULT_IGNORED_DIRS and not d.startswith(".git")
        ]

        for filename in filenames:
            file_full_path = Path(dirpath) / filename

            # Inspect file safety and symlinks
            try:
                resolved_file = file_full_path.resolve(strict=True)
                resolved_file.relative_to(root_path)
            except (ValueError, OSError):
                # Skip files outside root or broken symlinks
                continue

            if not resolved_file.is_file():
                continue

            rel_path = file_full_path.relative_to(root_path).as_posix()
            discovered_files.append(rel_path)

    # Sort deterministically
    discovered_files.sort()

    if len(discovered_files) > max_files:
        discovered_files = discovered_files[:max_files]
        truncated = True

    return {
        "files": discovered_files,
        "count": len(discovered_files),
        "truncated": truncated,
        "error": None,
    }
