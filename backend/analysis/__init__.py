"""
RepoPilot Structural Analysis Engine package (Stage 6).
Provides AST analysis, in-memory structural indexing, call flow tracing, and structural tools.
"""

from .models import Symbol, Relationship, CallFlowTrace
from .analyzer import parse_python_file
from .index import StructuralIndex
from .relationships import trace_call_flow as trace_call_flow_engine
from .tools import (
    get_structural_index,
    find_symbol,
    find_references,
    get_symbol_relationships,
    trace_call_flow,
    get_file_dependencies,
)

__all__ = [
    "Symbol",
    "Relationship",
    "CallFlowTrace",
    "parse_python_file",
    "StructuralIndex",
    "trace_call_flow_engine",
    "get_structural_index",
    "find_symbol",
    "find_references",
    "get_symbol_relationships",
    "trace_call_flow",
    "get_file_dependencies",
]
