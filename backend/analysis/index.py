"""
StructuralIndex implementation for RepoPilot (Person 1 Stage 6).
Provides an in-memory, repository-scoped index mapping symbols, definitions, calls, imports, and references.
Includes repository fingerprinting and staleness detection.
"""

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from backend.repository.models import Repository
from backend.tools import list_files, read_file, search_code
from .analyzer import parse_python_file
from .models import Relationship, Symbol


class StructuralIndex:
    """
    In-memory repository-scoped structural index for fast symbol discovery, call graph queries, and dependency tracking.
    """

    def __init__(self, repository: Union[str, Path, Repository]):
        if isinstance(repository, Repository):
            self._repo = repository
        else:
            self._repo = Repository(root_path=repository)

        self._repo_root = self._repo.root_path

        self._symbols: Dict[str, Symbol] = {}
        self._symbols_by_name: Dict[str, List[Symbol]] = {}
        self._symbols_by_file: Dict[str, List[Symbol]] = {}

        self._relationships: List[Relationship] = []
        self._calls_by_source: Dict[str, List[Relationship]] = {}
        self._calls_by_target: Dict[str, List[Relationship]] = {}
        self._imports_by_file: Dict[str, List[Relationship]] = {}

        self._parse_errors: Dict[str, str] = {}
        self._fingerprint: Optional[str] = None

    @property
    def repository(self) -> Repository:
        """Returns attached Repository object."""
        return self._repo

    @property
    def parse_errors(self) -> Dict[str, str]:
        """Returns map of file paths to parse error descriptions."""
        return dict(self._parse_errors)

    def compute_fingerprint(self) -> str:
        """
        Computes a deterministic hash of repository Python files metadata to detect staleness.
        """
        hasher = hashlib.sha256()
        try:
            list_res = list_files(repo_root=self._repo_root)
            files = sorted(list_res.get("files", []))
            py_files = [f for f in files if f.endswith(".py")]

            for rel_path in py_files:
                abs_path = self._repo_root / rel_path
                hasher.update(rel_path.encode("utf-8"))
                if abs_path.exists():
                    stat = abs_path.stat()
                    hasher.update(f"{stat.st_mtime}:{stat.st_size}".encode("utf-8"))
        except Exception as e:
            hasher.update(str(e).encode("utf-8"))

        return hasher.hexdigest()

    def is_stale(self) -> bool:
        """Returns True if repository fingerprint has changed since last index build."""
        if self._fingerprint is None:
            return True
        return self.compute_fingerprint() != self._fingerprint

    def ensure_up_to_date(self) -> None:
        """Builds index if uninitialized or stale."""
        if self.is_stale():
            self.build_index()

    def build_index(self) -> None:
        """
        Scans repository Python files, extracts AST symbols and raw relationships,
        and executes cross-file relationship resolution.
        """
        self._symbols.clear()
        self._symbols_by_name.clear()
        self._symbols_by_file.clear()
        self._relationships.clear()
        self._calls_by_source.clear()
        self._calls_by_target.clear()
        self._imports_by_file.clear()
        self._parse_errors.clear()

        list_res = list_files(repo_root=self._repo_root)
        all_files = list_res.get("files", [])
        py_files = [f for f in all_files if f.endswith(".py")]

        # Phase 1: File-level AST Parsing
        raw_relationships: List[Relationship] = []
        for rel_path in py_files:
            read_res = read_file(path=rel_path, repo_root=self._repo_root)
            content = read_res.get("content", "")
            if read_res.get("error"):
                self._parse_errors[rel_path] = read_res["error"]
                continue

            symbols, rels, parse_err = parse_python_file(rel_path, content)
            if parse_err:
                self._parse_errors[rel_path] = parse_err

            self._symbols_by_file[rel_path] = symbols

            for sym in symbols:
                self._symbols[sym.symbol_id] = sym
                self._symbols_by_name.setdefault(sym.name, []).append(sym)

            raw_relationships.extend(rels)

        # Phase 2: Cross-File Relationship Resolution
        for rel in raw_relationships:
            resolved_rel = self._resolve_relationship(rel)
            self._relationships.append(resolved_rel)

            if resolved_rel.relationship_type == "calls":
                self._calls_by_source.setdefault(resolved_rel.source, []).append(resolved_rel)
                self._calls_by_target.setdefault(resolved_rel.target, []).append(resolved_rel)
            elif resolved_rel.relationship_type == "imports":
                self._imports_by_file.setdefault(resolved_rel.source, []).append(resolved_rel)

        self._fingerprint = self.compute_fingerprint()

    def _resolve_relationship(self, rel: Relationship) -> Relationship:
        """Attempts to resolve relative or target name strings to exact symbol_ids."""
        if rel.relationship_type not in ["calls", "inherits", "imports"]:
            return rel

        target_str = rel.target

        # Handle calls / inherits
        if rel.relationship_type in ["calls", "inherits"]:
            # If target_str contains dot (e.g. self.login or auth.login or login)
            short_target = target_str.split(".")[-1]

            matching_symbols = self._symbols_by_name.get(short_target, [])
            if len(matching_symbols) == 1:
                return Relationship(
                    relationship_id=rel.relationship_id,
                    relationship_type=rel.relationship_type,
                    source=rel.source,
                    target=matching_symbols[0].symbol_id,
                    evidence=rel.evidence,
                    resolution_status="resolved",
                    confidence=1.0,
                )
            elif len(matching_symbols) > 1:
                # Ambiguous match across multiple symbols
                return Relationship(
                    relationship_id=rel.relationship_id,
                    relationship_type=rel.relationship_type,
                    source=rel.source,
                    target=matching_symbols[0].symbol_id,  # Primary candidate
                    evidence=rel.evidence,
                    resolution_status="ambiguous",
                    confidence=0.5,
                )
            else:
                # Unresolved / external call target
                return Relationship(
                    relationship_id=rel.relationship_id,
                    relationship_type=rel.relationship_type,
                    source=rel.source,
                    target=target_str,
                    evidence=rel.evidence,
                    resolution_status="unresolved",
                    confidence=0.3,
                )

        # Handle imports
        if rel.relationship_type == "imports":
            # Check if import target matches any known repository file
            mod_path_candidate = target_str.replace(".", "/") + ".py"
            if mod_path_candidate in self._symbols_by_file:
                return Relationship(
                    relationship_id=rel.relationship_id,
                    relationship_type=rel.relationship_type,
                    source=rel.source,
                    target=mod_path_candidate,
                    evidence=rel.evidence,
                    resolution_status="resolved",
                    confidence=1.0,
                )
            # Check if import target is a parent directory init or module file
            init_candidate = target_str.replace(".", "/") + "/__init__.py"
            if init_candidate in self._symbols_by_file:
                return Relationship(
                    relationship_id=rel.relationship_id,
                    relationship_type=rel.relationship_type,
                    source=rel.source,
                    target=init_candidate,
                    evidence=rel.evidence,
                    resolution_status="resolved",
                    confidence=1.0,
                )

        return rel

    def find_symbols(self, name: str) -> List[Symbol]:
        """
        Finds symbols matching a name or symbol ID string.

        Args:
            name: Symbol name (e.g. 'login') or full symbol ID (e.g. 'backend/auth.py::login').

        Returns:
            List[Symbol]: List of matching symbol models.
        """
        self.ensure_up_to_date()
        query = name.strip()
        if query in self._symbols:
            return [self._symbols[query]]

        # Search by exact name match
        if query in self._symbols_by_name:
            return self._symbols_by_name[query]

        # Case-insensitive substring match fallback
        matches: List[Symbol] = []
        for sym_id, sym in self._symbols.items():
            if query.lower() in sym.name.lower() or query.lower() in sym_id.lower():
                matches.append(sym)

        return matches

    def find_references(self, name: str) -> Dict[str, Any]:
        """
        Finds definitions, AST call sites, and textual code matches referencing a symbol.

        Args:
            name: Symbol name or identifier string.

        Returns:
            Dict[str, Any]: Structured dictionary with definitions, AST calls, and textual references.
        """
        self.ensure_up_to_date()
        query = name.strip()

        defs = [s.to_dict() for s in self.find_symbols(query)]
        ast_references: List[Dict[str, Any]] = []

        # Gather AST calls matching target name or target symbol ID
        for rel in self._relationships:
            if rel.relationship_type in ["calls", "references", "imports"]:
                if query in rel.target or any(d["symbol_id"] == rel.target for d in defs):
                    ast_references.append(rel.to_dict())

        # Perform fallback code search for textual occurrences
        search_res = search_code(query=query, repo_root=self._repo_root)
        textual_matches = search_res.get("matches", []) if isinstance(search_res, dict) else []

        return {
            "query": query,
            "definitions": defs,
            "ast_references": ast_references,
            "textual_matches": textual_matches,
            "total_ast_references": len(ast_references),
        }

    def get_symbol_relationships(self, name: str) -> List[Relationship]:
        """
        Retrieves all incoming and outgoing structural relationships involving a symbol.
        """
        self.ensure_up_to_date()
        query = name.strip()
        matching_sym_ids = [s.symbol_id for s in self.find_symbols(query)]

        rels: List[Relationship] = []
        for r in self._relationships:
            if r.source == query or r.target == query or r.source in matching_sym_ids or r.target in matching_sym_ids:
                rels.append(r)

        return rels

    def get_file_dependencies(self, file_path: str) -> Dict[str, Any]:
        """
        Returns import dependencies for a specific repository file.
        """
        self.ensure_up_to_date()
        rel_path = file_path.strip()

        imported_modules: List[Dict[str, Any]] = []
        for rel in self._relationships:
            if rel.relationship_type == "imports" and rel.source == rel_path:
                imported_modules.append(rel.to_dict())

        imported_by: List[Dict[str, Any]] = []
        for rel in self._relationships:
            if rel.relationship_type == "imports" and rel.target == rel_path:
                imported_by.append(rel.to_dict())

        return {
            "file_path": rel_path,
            "imports": imported_modules,
            "imported_by": imported_by,
            "total_imports": len(imported_modules),
        }
