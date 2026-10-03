"""
Call Flow Traversal Engine for RepoPilot (Person 1 Stage 6).
Provides bounded upstream and downstream call hierarchy traversal with cycle detection.
"""

from typing import Any, Dict, List, Set

from .index import StructuralIndex
from .models import CallFlowTrace


def trace_call_flow(
    index: StructuralIndex,
    symbol_name: str,
    direction: str = "downstream",
    max_depth: int = 3,
) -> CallFlowTrace:
    """
    Traces bounded call flow hierarchy starting from a root symbol.

    Args:
        index: Initialized and up-to-date StructuralIndex.
        symbol_name: Starting symbol name or ID (e.g. 'login' or 'backend/auth.py::login').
        direction: Traversal direction ('downstream' for functions called, 'upstream' for callers).
        max_depth: Maximum call graph depth limit (bounded 1 to 10).

    Returns:
        CallFlowTrace: Structured traversal result with nodes, edges, cycle detection, and unresolved targets.
    """
    index.ensure_up_to_date()

    query = symbol_name.strip()
    direction_clean = direction.lower().strip()
    if direction_clean not in ["downstream", "upstream"]:
        direction_clean = "downstream"

    depth_limit = max(1, min(max_depth, 10))

    root_symbols = index.find_symbols(query)
    if not root_symbols:
        return CallFlowTrace(
            root_symbol=query,
            direction=direction_clean,
            max_depth=depth_limit,
            nodes=[],
            edges=[],
            cycles_detected=False,
            unresolved_calls=[f"Root symbol '{query}' not found in index."],
        )

    root_sym = root_symbols[0]
    root_id = root_sym.symbol_id

    nodes_dict: Dict[str, Dict[str, Any]] = {root_id: root_sym.to_dict()}
    edges: List[Dict[str, Any]] = []
    unresolved: List[str] = []
    cycles_detected = False

    # Queue item: (symbol_id, current_depth)
    visited_in_path: Set[str] = set()

    def _traverse_downstream(curr_id: str, curr_depth: int, path: Set[str]) -> None:
        nonlocal cycles_detected
        if curr_depth >= depth_limit:
            return

        # Find outgoing call relationships from curr_id
        for rel in index._relationships:
            if rel.relationship_type == "calls" and (rel.source == curr_id or rel.source.endswith(f"::{curr_id.split('::')[-1]}")):
                target_id = rel.target
                edge_dict = rel.to_dict()
                if edge_dict not in edges:
                    edges.append(edge_dict)

                if rel.resolution_status == "unresolved":
                    if target_id not in unresolved:
                        unresolved.append(target_id)
                    continue

                if target_id in path:
                    cycles_detected = True
                    continue

                target_syms = index.find_symbols(target_id)
                if target_syms:
                    t_sym = target_syms[0]
                    nodes_dict[t_sym.symbol_id] = t_sym.to_dict()

                    new_path = set(path)
                    new_path.add(t_sym.symbol_id)
                    _traverse_downstream(t_sym.symbol_id, curr_depth + 1, new_path)

    def _traverse_upstream(curr_id: str, curr_depth: int, path: Set[str]) -> None:
        nonlocal cycles_detected
        if curr_depth >= depth_limit:
            return

        curr_short_name = curr_id.rsplit("::", 1)[-1].rsplit(".", 1)[-1]

        # Find incoming call relationships where target is curr_id or curr_short_name
        for rel in index._relationships:
            if rel.relationship_type == "calls" and (rel.target == curr_id or rel.target == curr_short_name or rel.target.endswith(f"::{curr_short_name}")):
                source_id = rel.source
                edge_dict = rel.to_dict()
                if edge_dict not in edges:
                    edges.append(edge_dict)

                if source_id in path:
                    cycles_detected = True
                    continue

                source_syms = index.find_symbols(source_id)
                if source_syms:
                    s_sym = source_syms[0]
                    nodes_dict[s_sym.symbol_id] = s_sym.to_dict()

                    new_path = set(path)
                    new_path.add(s_sym.symbol_id)
                    _traverse_upstream(s_sym.symbol_id, curr_depth + 1, new_path)

    initial_path = {root_id}
    if direction_clean == "downstream":
        _traverse_downstream(root_id, 0, initial_path)
    else:
        _traverse_upstream(root_id, 0, initial_path)

    return CallFlowTrace(
        root_symbol=root_id,
        direction=direction_clean,
        max_depth=depth_limit,
        nodes=list(nodes_dict.values()),
        edges=edges,
        cycles_detected=cycles_detected,
        unresolved_calls=unresolved,
    )
