"""
Data models for Stage 6 RepoPilot Structural Analysis Engine (Person 1 Stage 6).
Provides typed representations for symbols, AST relationships, and call flow traces.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Symbol:
    """
    Typed representation of a code symbol (module, class, function, method).

    Attributes:
        symbol_id: Unique identifier string (e.g. 'backend/auth.py::login').
        name: Short name of the symbol (e.g. 'login').
        symbol_type: Classification ('module', 'class', 'function', 'method').
        file_path: Repository-relative POSIX file path.
        start_line: 1-indexed starting line number.
        end_line: 1-indexed ending line number.
        parent_symbol: Optional parent symbol ID (e.g. enclosing class or module).
        language: Source language ('python').
        docstring: Optional docstring snippet.
        signature: Optional function/method signature summary string.
    """
    symbol_id: str
    name: str
    symbol_type: str
    file_path: str
    start_line: int
    end_line: int
    parent_symbol: Optional[str] = None
    language: str = "python"
    docstring: Optional[str] = None
    signature: Optional[str] = None

    @property
    def source_location(self) -> str:
        """Returns formatted line citation location string (e.g. 'backend/auth.py:10-25')."""
        if self.start_line is not None and self.end_line is not None:
            return f"{self.file_path}:{self.start_line}-{self.end_line}"
        return self.file_path

    def to_dict(self) -> Dict[str, Any]:
        """Converts Symbol to a JSON-serializable dictionary representation."""
        return {
            "symbol_id": self.symbol_id,
            "name": self.name,
            "symbol_type": self.symbol_type,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "parent_symbol": self.parent_symbol,
            "language": self.language,
            "docstring": self.docstring,
            "signature": self.signature,
            "source_location": self.source_location,
        }


@dataclass
class Relationship:
    """
    Typed representation of a structural code relationship.

    Attributes:
        relationship_id: Unique relationship ID.
        relationship_type: Relationship classification ('defines', 'contains', 'imports', 'calls', 'inherits', 'references').
        source: Source symbol ID or file path.
        target: Target symbol ID, file path, or external module name.
        evidence: Dictionary containing file path and line location evidence.
        resolution_status: Status ('resolved', 'unresolved', 'ambiguous', 'textual_reference').
        confidence: Confidence score (1.0 for AST verified, 0.5 for ambiguous/textual).
    """
    relationship_id: str
    relationship_type: str
    source: str
    target: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    resolution_status: str = "resolved"
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Converts Relationship to a JSON-serializable dictionary representation."""
        return {
            "relationship_id": self.relationship_id,
            "relationship_type": self.relationship_type,
            "source": self.source,
            "target": self.target,
            "evidence": self.evidence,
            "resolution_status": self.resolution_status,
            "confidence": self.confidence,
        }


@dataclass
class CallFlowTrace:
    """
    Result model for bounded call hierarchy traversal (upstream or downstream).

    Attributes:
        root_symbol: Starting symbol name or ID for the trace.
        direction: Traversal direction ('downstream' or 'upstream').
        max_depth: Maximum requested traversal depth.
        nodes: List of discovered symbol dictionary representations.
        edges: List of call relationship dictionary representations.
        cycles_detected: Boolean flag indicating if recursive/cyclic call loops were encountered.
        unresolved_calls: List of call targets that could not be resolved.
    """
    root_symbol: str
    direction: str
    max_depth: int
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    cycles_detected: bool = False
    unresolved_calls: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converts CallFlowTrace to a JSON-serializable dictionary representation."""
        return {
            "root_symbol": self.root_symbol,
            "direction": self.direction,
            "max_depth": self.max_depth,
            "nodes": self.nodes,
            "edges": self.edges,
            "cycles_detected": self.cycles_detected,
            "unresolved_calls": self.unresolved_calls,
        }
