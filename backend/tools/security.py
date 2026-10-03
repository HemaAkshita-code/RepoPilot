"""
Security and path resolution helpers for repository investigation tools.
"""

from pathlib import Path
from typing import Union

from backend.repository.models import Repository
from .exceptions import PathTraversalError, FileAccessError

DEFAULT_IGNORED_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "ENV",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "htmlcov",
    ".idea",
    ".vscode",
}


def get_canonical_root(repo_root: Union[str, Path, Repository]) -> Path:
    """
    Extracts and resolves the canonical root directory path from a Repository object,
    Path, or string path.

    Raises:
        FileAccessError: If the root path does not exist or is not a directory.
    """
    if isinstance(repo_root, Repository):
        root_path = repo_root.root_path
    elif isinstance(repo_root, (str, Path)):
        if not repo_root and repo_root != "":
            raise FileAccessError("Repository root path cannot be empty.")
        root_path = Path(repo_root)
    else:
        raise FileAccessError(f"Invalid repository root type: {type(repo_root)}")

    if str(root_path).strip() == "":
        raise FileAccessError("Repository root path cannot be empty.")

    try:
        resolved_root = root_path.resolve(strict=True)
    except Exception as e:
        raise FileAccessError(f"Repository root path cannot be resolved or does not exist: {e}")

    if not resolved_root.is_dir():
        raise FileAccessError(f"Repository root path is not a directory: '{resolved_root}'")

    return resolved_root


def resolve_safe_path(
    relative_path: Union[str, Path],
    repo_root: Union[str, Path, Repository],
) -> Path:
    """
    Safely resolves a repository-relative path against the repository root.
    Strictly enforces security boundaries:
    1. Rejects absolute paths.
    2. Rejects path traversal (../../secret.txt).
    3. Rejects symlinks pointing outside the repository root.

    Returns:
        Path: Resolved absolute Path within the repository root.

    Raises:
        PathTraversalError: If the path attempts to escape the repository root.
    """
    root_path = get_canonical_root(repo_root)

    if relative_path is None or str(relative_path).strip() == "":
        raise PathTraversalError("Path cannot be empty.")

    raw_path = Path(relative_path)

    # 1. Reject absolute paths
    if raw_path.is_absolute():
        raise PathTraversalError(f"Absolute paths are forbidden: '{relative_path}'")

    # 2. Combine with root
    candidate_path = root_path / raw_path

    # 3. Resolve candidate path
    try:
        resolved_path = candidate_path.resolve(strict=False)
    except Exception as e:
        raise PathTraversalError(f"Invalid path structure: {e}")

    # 4. Enforce repository root containment
    try:
        resolved_path.relative_to(root_path)
    except ValueError:
        raise PathTraversalError(f"Access denied: Path '{relative_path}' escapes repository root.")

    # 5. Check real path for existing symlinks
    if candidate_path.exists() or candidate_path.is_symlink():
        try:
            real_target = candidate_path.resolve(strict=True)
            real_target.relative_to(root_path)
        except (ValueError, OSError):
            raise PathTraversalError(f"Access denied: Symlink '{relative_path}' points outside repository root.")

    return resolved_path
