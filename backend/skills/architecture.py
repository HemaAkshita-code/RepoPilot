"""
Repository Architecture Skill implementation for RepoPilot (Person 2 Stage 5).
Investigates high-level repository layout, major packages, entry points, configuration, and subsystems.
"""

from typing import Any, Dict, List, Optional

from backend.agent.context import InvestigationContext
from backend.agent.registry import ToolRegistry
from .base import BaseSkill
from .models import Finding, SkillResult


class ArchitectureSkill(BaseSkill):
    """
    Skill for understanding the high-level architecture of an unfamiliar software repository.
    Discovers main directories, entry points, configuration files, and major subsystems.
    """

    name = "understand_architecture"
    description = (
        "Investigate and analyze high-level repository structure, directory layout, "
        "entry points, core configuration files, and major subsystems."
    )
    version = "1.0.0"

    parameters = {
        "type": "OBJECT",
        "properties": {
            "query": {
                "type": "STRING",
                "description": "Optional focus area or query for architecture analysis (e.g. 'backend architecture').",
            },
            "max_files_to_inspect": {
                "type": "INTEGER",
                "description": "Optional maximum number of candidate architecture files to read (defaults to 5).",
            },
        },
        "required": [],
    }

    param_validators = {
        "query": lambda val: isinstance(val, str),
        "max_files_to_inspect": lambda val: isinstance(val, int) and val > 0,
    }

    def execute(
        self,
        registry: ToolRegistry,
        context: Optional[InvestigationContext] = None,
        **kwargs: Any,
    ) -> SkillResult:
        """Executes repository architecture investigation."""
        query = kwargs.get("query", "")
        max_inspect = min(kwargs.get("max_files_to_inspect", 5), 10)

        findings: List[Dict[str, Any]] = []
        evidence_locs: List[str] = []
        unresolved: List[str] = []

        # 1. Step 1: List repository files
        list_res = registry.execute("list_files", {}, context=context)
        all_files: List[str] = []
        if list_res.success and isinstance(list_res.result, dict):
            all_files = list_res.result.get("files", [])

        if not all_files:
            return SkillResult(
                skill_name=self.name,
                status="failed",
                summary="No files discovered in repository.",
                error="Repository file listing returned empty result.",
            )

        # Classify top-level structure and config files
        top_level_dirs = sorted(list({f.split('/')[0] for f in all_files if '/' in f}))
        config_files = [
            f for f in all_files
            if f.lower() in [
                "readme.md", "pyproject.toml", "setup.py", "package.json",
                "config.py", "dockerfile", "requirements.txt", "cargo.toml", "go.mod"
            ] or f.endswith(".config.js") or f.endswith(".json")
        ]

        findings.append(Finding(
            description=f"Observed top-level directory layout: {', '.join(top_level_dirs) if top_level_dirs else 'flat repository'}.",
            finding_type="observed",
            evidence_locations=all_files[:10],
        ).to_dict())

        if config_files:
            findings.append(Finding(
                description=f"Identified core configuration and metadata files: {', '.join(config_files)}.",
                finding_type="observed",
                evidence_locations=config_files,
            ).to_dict())
            evidence_locs.extend(config_files)

        # 2. Step 2: Semantic retrieval for application entry points & architecture
        search_query = query if query else "main application entry point routes architecture configuration"
        rag_res = registry.execute("search_repository", {"query": search_query, "top_k": 5}, context=context)

        candidate_files: List[str] = []
        if rag_res.success and isinstance(rag_res.result, dict):
            chunks = rag_res.result.get("chunks", [])
            for c in chunks:
                p = c.get("path")
                if p and p not in candidate_files:
                    candidate_files.append(p)
                    loc = f"{p}:{c.get('start_line', 1)}-{c.get('end_line', 1)}"
                    if loc not in evidence_locs:
                        evidence_locs.append(loc)

        # Prioritize config and RAG candidate files for inspection
        inspect_queue = [f for f in config_files if f in all_files] + [f for f in candidate_files if f in all_files]
        inspect_queue = list(dict.fromkeys(inspect_queue))[:max_inspect]

        inspected_count = 0
        for filepath in inspect_queue:
            read_res = registry.execute("read_file", {"path": filepath}, context=context)
            if read_res.success and isinstance(read_res.result, dict):
                inspected_count += 1
                content = read_res.result.get("content", "")
                snippet = content[:250].replace("\n", " ")
                findings.append(Finding(
                    description=f"Inspected candidate architecture file '{filepath}': {snippet}...",
                    finding_type="observed",
                    evidence_locations=[filepath],
                ).to_dict())
                if filepath not in evidence_locs:
                    evidence_locs.append(filepath)

        # Synthesize inferences vs facts
        if candidate_files:
            findings.append(Finding(
                description=f"Inferred core functional entry points or key modules based on RAG context: {', '.join(candidate_files[:3])}.",
                finding_type="inference",
                evidence_locations=candidate_files[:3],
            ).to_dict())
        else:
            unresolved.append("Could not unambiguously identify application entry point from vector retrieval.")

        summary = (
            f"Repository architecture investigation completed. Analyzed {len(all_files)} total files across "
            f"{len(top_level_dirs)} top-level packages. Directly inspected {inspected_count} candidate architecture files."
        )

        return SkillResult(
            skill_name=self.name,
            status="completed",
            summary=summary,
            findings=findings,
            evidence=list(dict.fromkeys(evidence_locs)),
            unresolved_questions=unresolved,
            metadata={
                "total_files": len(all_files),
                "inspected_count": inspected_count,
                "top_level_dirs": top_level_dirs,
            },
        )
