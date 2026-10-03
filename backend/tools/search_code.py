"""
search_code tool implementation for Stage 2.
"""

import os
from pathlib import Path
from typing import Union, Dict, Any, List

from backend.repository.models import Repository
from .security import get_canonical_root, DEFAULT_IGNORED_DIRS


def is_binary_file_sample(file_path: Path) -> bool:
    """Quick check for binary content in initial bytes of a file."""
    try:
        with open(file_path, "rb") as f:
            sample = f.read(1024)
            return b"\x00" in sample
    except OSError:
        return True


def search_code(
    query: str,
    repo_root: Union[str, Path, Repository],
    case_sensitive: bool = False,
    max_matches: int = 100,
    max_snippet_len: int = 200,
) -> Dict[str, Any]:
    """
    Recursively searches repository files for occurrences of a text query.

    Args:
        query: Search string.
        repo_root: Repository root (Path, string, or Repository object).
        case_sensitive: If True, performs case-sensitive match; defaults to False.
        max_matches: Maximum number of match objects to return.
        max_snippet_len: Maximum length of returned line snippet.

    Returns:
        Dict[str, Any]: Structured dictionary with "query", "matches", "total_matches", "truncated".
    """
    if not query:
        return {
            "query": query,
            "matches": [],
            "total_matches": 0,
            "truncated": False,
            "error": "Search query cannot be empty.",
        }

    try:
        root_path = get_canonical_root(repo_root)
    except Exception as e:
        return {
            "query": query,
            "matches": [],
            "total_matches": 0,
            "truncated": False,
            "error": str(e),
        }

    search_term = query if case_sensitive else query.lower()
    matches: List[Dict[str, Any]] = []
    truncated = False

    # Collect files first for deterministic traversal
    file_list: List[tuple[Path, str]] = []

    for dirpath, dirnames, filenames in os.walk(root_path, followlinks=False):
        dirnames[:] = [
            d for d in dirnames
            if d not in DEFAULT_IGNORED_DIRS and not d.startswith(".git")
        ]

        for filename in filenames:
            file_full_path = Path(dirpath) / filename
            try:
                resolved_file = file_full_path.resolve(strict=True)
                resolved_file.relative_to(root_path)
            except (ValueError, OSError):
                continue

            if not resolved_file.is_file():
                continue

            rel_path = file_full_path.relative_to(root_path).as_posix()
            file_list.append((file_full_path, rel_path))

    # Sort files deterministically by relative path
    file_list.sort(key=lambda item: item[1])

    for file_full_path, rel_path in file_list:
        if truncated:
            break

        if is_binary_file_sample(file_full_path):
            continue

        try:
            with open(file_full_path, "r", encoding="utf-8", errors="replace") as f:
                for line_no, line in enumerate(f, start=1):
                    target_line = line if case_sensitive else line.lower()
                    if search_term in target_line:
                        snippet = line.strip()
                        if len(snippet) > max_snippet_len:
                            snippet = snippet[:max_snippet_len] + "..."

                        matches.append({
                            "path": rel_path,
                            "line": line_no,
                            "snippet": snippet,
                        })

                        if len(matches) >= max_matches:
                            truncated = True
                            break
        except OSError:
            # Skip unreadable files without crashing
            continue

    return {
        "query": query,
        "matches": matches,
        "total_matches": len(matches),
        "truncated": truncated,
        "error": None,
    }
