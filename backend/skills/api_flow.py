"""
API / Request Flow Skill implementation for RepoPilot (Person 2 Stage 5).
Investigates request progression through routes, controllers, services, and data layers.
"""

from typing import Any, Dict, List, Optional

from backend.agent.context import InvestigationContext
from backend.agent.registry import ToolRegistry
from .base import BaseSkill
from .models import Finding, SkillResult


class APIFlowSkill(BaseSkill):
    """
    Skill for investigating how an API endpoint or request flows through the repository architecture.
    Traces from route handler -> service logic -> data access repository.
    """

    name = "investigate_api_flow"
    description = (
        "Investigate an API request flow across route handlers, controller logic, service functions, "
        "and data access layers."
    )
    version = "1.0.0"

    parameters = {
        "type": "OBJECT",
        "properties": {
            "endpoint_query": {
                "type": "STRING",
                "description": "API route path, endpoint name, or request concept to trace (e.g. '/api/v1/users' or 'login endpoint').",
            },
            "max_files_to_inspect": {
                "type": "INTEGER",
                "description": "Optional maximum number of candidate flow files to inspect (defaults to 5).",
            },
        },
        "required": ["endpoint_query"],
    }

    param_validators = {
        "endpoint_query": lambda val: isinstance(val, str) and bool(val.strip()),
        "max_files_to_inspect": lambda val: isinstance(val, int) and val > 0,
    }

    def execute(
        self,
        registry: ToolRegistry,
        context: Optional[InvestigationContext] = None,
        **kwargs: Any,
    ) -> SkillResult:
        """Executes API request flow investigation."""
        endpoint_query = kwargs["endpoint_query"].strip()
        max_inspect = min(kwargs.get("max_files_to_inspect", 5), 10)

        findings: List[Dict[str, Any]] = []
        evidence_locs: List[str] = []
        unresolved: List[str] = []

        flow_steps: List[str] = []
        candidate_files: List[str] = []

        # 1. Search for Route Declarations / Endpoints
        search_terms = [endpoint_query, "route", "controller", "service", "repository"]
        for term in search_terms:
            search_res = registry.execute("search_code", {"query": term}, context=context)
            if search_res.success and isinstance(search_res.result, dict):
                matches = search_res.result.get("matches", [])
                for m in matches:
                    p = m.get("path")
                    line = m.get("line", 1)
                    snippet = m.get("snippet", "")
                    if p and p not in candidate_files:
                        candidate_files.append(p)
                    loc = f"{p}:{line}"
                    if p and term == endpoint_query:
                        evidence_locs.append(loc)
                        findings.append(Finding(
                            description=f"Identified endpoint match in {loc}: '{snippet}'",
                            finding_type="observed",
                            evidence_locations=[loc],
                        ).to_dict())

        # 2. Semantic Search for API flow
        rag_res = registry.execute(
            "search_repository",
            {"query": f"API request route handler controller service database {endpoint_query}", "top_k": 5},
            context=context,
        )
        if rag_res.success and isinstance(rag_res.result, dict):
            chunks = rag_res.result.get("chunks", [])
            for c in chunks:
                p = c.get("path")
                if p:
                    if p not in candidate_files:
                        candidate_files.append(p)
                    loc = f"{p}:{c.get('start_line', 1)}-{c.get('end_line', 1)}"
                    evidence_locs.append(loc)

        # 2.5 Optional AST Call Flow Traversal (Stage 6 Structural Capability)
        if registry.get_tool("trace_call_flow") is not None:
            trace_res = registry.execute("trace_call_flow", {"symbol": endpoint_query, "direction": "downstream", "depth": 3}, context=context)
            if trace_res.success and isinstance(trace_res.result, dict):
                nodes = trace_res.result.get("nodes", [])
                for node in nodes:
                    p = node.get("file_path")
                    start = node.get("start_line", 1)
                    end = node.get("end_line", 1)
                    if p:
                        if p not in candidate_files:
                            candidate_files.append(p)
                        loc = f"{p}:{start}-{end}"
                        evidence_locs.append(loc)
                        findings.append(Finding(
                            description=f"Discovered AST call flow node '{node.get('name')}' in {loc}",
                            finding_type="observed",
                            evidence_locations=[loc],
                        ).to_dict())

        if not candidate_files:
            unresolved.append(f"No API routes or handlers discovered matching '{endpoint_query}'.")
            return SkillResult(
                skill_name=self.name,
                status="completed",
                summary=f"API flow investigation for '{endpoint_query}' yielded no candidate files.",
                findings=findings,
                evidence=[],
                unresolved_questions=unresolved,
            )

        # 3. Read & Trace candidate flow files
        inspect_queue = candidate_files[:max_inspect]
        for filepath in inspect_queue:
            read_res = registry.execute("read_file", {"path": filepath}, context=context)
            if read_res.success and isinstance(read_res.result, dict):
                content = read_res.result.get("content", "")
                flow_steps.append(filepath)
                findings.append(Finding(
                    description=f"Inspected API flow layer file '{filepath}'.",
                    finding_type="observed",
                    evidence_locations=[filepath],
                ).to_dict())
                if filepath not in evidence_locs:
                    evidence_locs.append(filepath)

        # Synthesize Request Flow Chain
        flow_chain_str = " -> ".join(flow_steps) if flow_steps else "unknown"
        findings.append(Finding(
            description=f"Constructed request flow chain: {flow_chain_str}",
            finding_type="inference",
            evidence_locations=flow_steps,
        ).to_dict())

        summary = (
            f"API request flow investigation for '{endpoint_query}' completed. "
            f"Traced flow across {len(flow_steps)} component layer files: {flow_chain_str}."
        )

        return SkillResult(
            skill_name=self.name,
            status="completed",
            summary=summary,
            findings=findings,
            evidence=list(dict.fromkeys(evidence_locs)),
            unresolved_questions=unresolved,
            metadata={"endpoint_query": endpoint_query, "flow_chain": flow_steps},
        )
