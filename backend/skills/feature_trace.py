"""
Feature Trace Skill implementation for RepoPilot (Person 2 Stage 5).
Traces a specific feature, concept, or data model through repository components.
"""

from typing import Any, Dict, List, Optional

from backend.agent.context import InvestigationContext
from backend.agent.registry import ToolRegistry
from .base import BaseSkill
from .models import Finding, SkillResult


class FeatureTraceSkill(BaseSkill):
    """
    Skill for tracing a requested feature, concept, or data flow across the codebase.
    Combines semantic retrieval, exact code search, and targeted file inspection.
    """

    name = "trace_feature"
    description = (
        "Trace how a feature, concept, or data model is implemented across repository components, "
        "identifying definitions, usages, and relationships."
    )
    version = "1.0.0"

    parameters = {
        "type": "OBJECT",
        "properties": {
            "feature_query": {
                "type": "STRING",
                "description": "Feature, concept, or function name to trace across the repository (e.g. 'authentication login').",
            },
            "max_depth": {
                "type": "INTEGER",
                "description": "Optional maximum number of feature files to inspect (defaults to 5).",
            },
        },
        "required": ["feature_query"],
    }

    param_validators = {
        "feature_query": lambda val: isinstance(val, str) and bool(val.strip()),
        "max_depth": lambda val: isinstance(val, int) and val > 0,
    }

    def execute(
        self,
        registry: ToolRegistry,
        context: Optional[InvestigationContext] = None,
        **kwargs: Any,
    ) -> SkillResult:
        """Executes feature trace investigation."""
        feature_query = kwargs["feature_query"].strip()
        max_depth = min(kwargs.get("max_depth", 5), 10)

        findings: List[Dict[str, Any]] = []
        evidence_locs: List[str] = []
        unresolved: List[str] = []

        candidate_files: List[str] = []

        # 1. Step 1: Semantic Retrieval (RAG)
        rag_res = registry.execute("search_repository", {"query": feature_query, "top_k": 5}, context=context)
        if rag_res.success and isinstance(rag_res.result, dict):
            chunks = rag_res.result.get("chunks", [])
            for c in chunks:
                p = c.get("path")
                if p:
                    if p not in candidate_files:
                        candidate_files.append(p)
                    loc = f"{p}:{c.get('start_line', 1)}-{c.get('end_line', 1)}"
                    evidence_locs.append(loc)
                    findings.append(Finding(
                        description=f"Retrieved semantic match for feature '{feature_query}' in {loc}.",
                        finding_type="observed",
                        evidence_locations=[loc],
                    ).to_dict())

        # 2. Step 2: Exact Code Search
        search_res = registry.execute("search_code", {"query": feature_query}, context=context)
        if search_res.success and isinstance(search_res.result, dict):
            matches = search_res.result.get("matches", [])
            for m in matches:
                p = m.get("path")
                line = m.get("line", 1)
                snippet = m.get("snippet", "")
                if p:
                    if p not in candidate_files:
                        candidate_files.append(p)
                    loc = f"{p}:{line}"
                    evidence_locs.append(loc)
                    findings.append(Finding(
                        description=f"Found exact code occurrence for '{feature_query}' in {loc}: '{snippet}'",
                        finding_type="observed",
                        evidence_locations=[loc],
                    ).to_dict())

        if not candidate_files:
            unresolved.append(f"No code occurrences or semantic matches found for feature '{feature_query}'.")
            return SkillResult(
                skill_name=self.name,
                status="completed",
                summary=f"Feature trace for '{feature_query}' yielded no matches.",
                findings=findings,
                evidence=[],
                unresolved_questions=unresolved,
            )

        # 3. Step 3: Targeted File Inspection
        inspect_files = candidate_files[:max_depth]
        for filepath in inspect_files:
            read_res = registry.execute("read_file", {"path": filepath}, context=context)
            if read_res.success and isinstance(read_res.result, dict):
                content = read_res.result.get("content", "")
                findings.append(Finding(
                    description=f"Directly inspected candidate feature file '{filepath}' ({len(content.splitlines())} lines).",
                    finding_type="observed",
                    evidence_locations=[filepath],
                ).to_dict())
                if filepath not in evidence_locs:
                    evidence_locs.append(filepath)

        # Synthesize flow inference
        findings.append(Finding(
            description=f"Feature '{feature_query}' spans across {len(candidate_files)} file(s): {', '.join(candidate_files)}.",
            finding_type="inference",
            evidence_locations=candidate_files,
        ).to_dict())

        summary = (
            f"Feature trace for '{feature_query}' completed across {len(candidate_files)} file(s). "
            f"Inspected {len(inspect_files)} primary implementation files."
        )

        return SkillResult(
            skill_name=self.name,
            status="completed",
            summary=summary,
            findings=findings,
            evidence=list(dict.fromkeys(evidence_locs)),
            unresolved_questions=unresolved,
            metadata={"feature_query": feature_query, "matched_files": candidate_files},
        )
