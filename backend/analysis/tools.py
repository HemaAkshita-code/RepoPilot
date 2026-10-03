"""
Structural Tools Implementation for RepoPilot (Person 2 Stage 6).
Exposes find_symbol, find_references, get_symbol_relationships, trace_call_flow, and get_file_dependencies.
Integrates with ToolRegistry and enforces filesystem security boundaries.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from backend.repository.models import Repository
from backend.tools.security import resolve_safe_path
from .index import StructuralIndex
from .relationships import trace_call_flow as trace_flow_engine

# Process-local cache of StructuralIndex instances keyed by repo_root string
_INDEX_CACHE: Dict[str, StructuralIndex] = {}


def get_structural_index(repo_root: Union[str, Path, Repository]) -> StructuralIndex:
    """
    Returns or initializes a cached, up-to-date StructuralIndex for a repository root.
    """
    if isinstance(repo_root, Repository):
        root_path = repo_root.root_path
    else:
        root_path = Path(repo_root).resolve()

    key = str(root_path)
    if key not in _INDEX_CACHE:
        _INDEX_CACHE[key] = StructuralIndex(root_path)

    index = _INDEX_CACHE[key]
    index.ensure_up_to_date()
    return index


def find_symbol(symbol_name: str, repo_root: Union[str, Path, Repository] = None) -> Dict[str, Any]:
    """
    Find definitions of a symbol by name or identifier in the repository.

    Args:
        symbol_name: Name of the symbol to find (e.g. 'login' or 'backend/auth.py::login').
        repo_root: Repository root path (injected by ToolRegistry).

    Returns:
        Dict[str, Any]: Structured dictionary with matching symbols and definition locations.
    """
    if not symbol_name or not isinstance(symbol_name, str) or not symbol_name.strip():
        return {"query": str(symbol_name), "symbols": [], "count": 0, "error": "Symbol name must be a non-empty string."}

    index = get_structural_index(repo_root)
    symbols = index.find_symbols(symbol_name.strip())
    sym_dicts = [s.to_dict() for s in symbols]

    return {
        "query": symbol_name.strip(),
        "symbols": sym_dicts,
        "count": len(sym_dicts),
        "error": None,
    }


def find_references(symbol_name: str, repo_root: Union[str, Path, Repository] = None) -> Dict[str, Any]:
    """
    Find references, AST call sites, and code occurrences of a symbol in the repository.

    Args:
        symbol_name: Name of the symbol to query.
        repo_root: Repository root path (injected by ToolRegistry).

    Returns:
        Dict[str, Any]: Structured dictionary with definitions, AST call references, and textual matches.
    """
    if not symbol_name or not isinstance(symbol_name, str) or not symbol_name.strip():
        return {"query": str(symbol_name), "definitions": [], "ast_references": [], "textual_matches": [], "error": "Symbol name must be a non-empty string."}

    index = get_structural_index(repo_root)
    res = index.find_references(symbol_name.strip())
    res["error"] = None
    return res


def get_symbol_relationships(symbol_name: str, repo_root: Union[str, Path, Repository] = None) -> Dict[str, Any]:
    """
    Retrieve incoming and outgoing structural relationships (calls, called_by, imports, inherits) for a symbol.

    Args:
        symbol_name: Symbol name or identifier.
        repo_root: Repository root path (injected by ToolRegistry).

    Returns:
        Dict[str, Any]: List of structural relationship dictionaries.
    """
    if not symbol_name or not isinstance(symbol_name, str) or not symbol_name.strip():
        return {"query": str(symbol_name), "relationships": [], "count": 0, "error": "Symbol name must be a non-empty string."}

    index = get_structural_index(repo_root)
    rels = index.get_symbol_relationships(symbol_name.strip())
    rel_dicts = [r.to_dict() for r in rels]

    return {
        "query": symbol_name.strip(),
        "relationships": rel_dicts,
        "count": len(rel_dicts),
        "error": None,
    }


def trace_call_flow(
    symbol: str,
    direction: str = "downstream",
    depth: int = 3,
    repo_root: Union[str, Path, Repository] = None,
) -> Dict[str, Any]:
    """
    Trace bounded call flow hierarchy (upstream or downstream) starting from a symbol.

    Args:
        symbol: Starting symbol name or identifier (e.g. 'login').
        direction: 'downstream' (called functions) or 'upstream' (calling functions).
        depth: Maximum graph depth limit (integer 1 to 10).
        repo_root: Repository root path (injected by ToolRegistry).

    Returns:
        Dict[str, Any]: Structured CallFlowTrace dictionary.
    """
    if not symbol or not isinstance(symbol, str) or not symbol.strip():
        return {"root_symbol": str(symbol), "direction": direction, "max_depth": depth, "nodes": [], "edges": [], "error": "Symbol must be a non-empty string."}

    direction_clean = str(direction).lower().strip()
    if direction_clean not in ["downstream", "upstream"]:
        return {"root_symbol": symbol, "direction": direction, "max_depth": depth, "nodes": [], "edges": [], "error": "Direction must be 'downstream' or 'upstream'."}

    try:
        depth_int = int(depth)
        if depth_int < 1:
            raise ValueError()
    except (ValueError, TypeError):
        return {"root_symbol": symbol, "direction": direction, "max_depth": depth, "nodes": [], "edges": [], "error": "Depth must be a positive integer."}

    index = get_structural_index(repo_root)
    trace = trace_flow_engine(index, symbol.strip(), direction=direction_clean, max_depth=depth_int)
    res_dict = trace.to_dict()
    res_dict["error"] = None
    return res_dict


def get_file_dependencies(file_path: str, repo_root: Union[str, Path, Repository] = None) -> Dict[str, Any]:
    """
    Get import dependencies for a specific repository file.

    Args:
        file_path: Repository-relative POSIX path (e.g. 'backend/routes.py').
        repo_root: Repository root path (injected by ToolRegistry).

    Returns:
        Dict[str, Any]: Import dependencies dictionary.
    """
    if not file_path or not isinstance(file_path, str) or not file_path.strip():
        return {"file_path": str(file_path), "imports": [], "imported_by": [], "error": "File path must be a non-empty string."}

    # Validate file path against repository security boundary
    try:
        resolve_safe_path(file_path.strip(), repo_root)
    except Exception as e:
        return {
            "file_path": file_path,
            "imports": [],
            "imported_by": [],
            "error": f"Security boundary violation: {e}",
        }

    index = get_structural_index(repo_root)
    res = index.get_file_dependencies(file_path.strip())
    res["error"] = None
    return res
