"""
read_file tool implementation for Stage 2.
"""

from pathlib import Path
from typing import Union, Dict, Any

from backend.repository.models import Repository
from .security import get_canonical_root, resolve_safe_path, PathTraversalError, FileAccessError


def is_binary_content(data: bytes) -> bool:
    """Checks if raw bytes contain NUL bytes indicating binary content."""
    return b"\x00" in data


def read_file(
    path: Union[str, Path],
    repo_root: Union[str, Path, Repository],
    max_bytes: int = 100_000,
) -> Dict[str, Any]:
    """
    Safely reads content from a repository-relative file.

    Args:
        path: Repository-relative path to the file.
        repo_root: Repository root (Path, string, or Repository object).
        max_bytes: Maximum number of bytes to read before truncating.

    Returns:
        Dict[str, Any]: Structured dictionary containing file content or error state.
    """
    path_str = str(path) if path is not None else ""

    try:
        root_path = get_canonical_root(repo_root)
        target_path = resolve_safe_path(path, root_path)
    except (PathTraversalError, FileAccessError) as e:
        return {
            "path": path_str,
            "content": "",
            "size_bytes": 0,
            "encoding": None,
            "is_binary": False,
            "truncated": False,
            "error": str(e),
        }

    if not target_path.exists():
        return {
            "path": path_str,
            "content": "",
            "size_bytes": 0,
            "encoding": None,
            "is_binary": False,
            "truncated": False,
            "error": f"File not found: '{path_str}'",
        }

    if target_path.is_dir():
        return {
            "path": path_str,
            "content": "",
            "size_bytes": 0,
            "encoding": None,
            "is_binary": False,
            "truncated": False,
            "error": f"Path is a directory, not a file: '{path_str}'",
        }

    try:
        stat_info = target_path.stat()
        file_size = stat_info.st_size
    except OSError as e:
        return {
            "path": path_str,
            "content": "",
            "size_bytes": 0,
            "encoding": None,
            "is_binary": False,
            "truncated": False,
            "error": f"Failed to access file attributes: {e}",
        }

    try:
        with open(target_path, "rb") as f:
            chunk = f.read(max_bytes + 1)
    except OSError as e:
        return {
            "path": path_str,
            "content": "",
            "size_bytes": file_size,
            "encoding": None,
            "is_binary": False,
            "truncated": False,
            "error": f"Failed to read file: {e}",
        }

    if is_binary_content(chunk[:1024]):
        return {
            "path": path_str,
            "content": "",
            "size_bytes": file_size,
            "encoding": None,
            "is_binary": True,
            "truncated": False,
            "error": None,
        }

    truncated = False
    if len(chunk) > max_bytes:
        chunk = chunk[:max_bytes]
        truncated = True

    try:
        content = chunk.decode("utf-8")
        encoding = "utf-8"
    except UnicodeDecodeError:
        try:
            content = chunk.decode("latin-1")
            encoding = "latin-1"
        except Exception:
            return {
                "path": path_str,
                "content": "",
                "size_bytes": file_size,
                "encoding": None,
                "is_binary": True,
                "truncated": False,
                "error": None,
            }

    return {
        "path": path_str,
        "content": content,
        "size_bytes": file_size,
        "encoding": encoding,
        "is_binary": False,
        "truncated": truncated,
        "error": None,
    }
