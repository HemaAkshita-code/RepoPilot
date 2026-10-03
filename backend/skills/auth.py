"""
Authentication Skill implementation for RepoPilot (Person 2 Stage 5).
Investigates security middleware, login mechanisms, token handling, and authorization boundaries.
"""

from typing import Any, Dict, List, Optional

from backend.agent.context import InvestigationContext
from backend.agent.registry import ToolRegistry
from .base import BaseSkill
from .models import Finding, SkillResult


class AuthSkill(BaseSkill):
    """
    Skill for investigating authentication, authorization, and security mechanisms in a repository.
    """

    name = "investigate_auth"
    description = (
        "Investigate authentication and authorization implementations, security middleware, "
        "login endpoints, token/session management, and access control boundaries."
    )
    version = "1.0.0"

    parameters = {
        "type": "OBJECT",
        "properties": {
            "auth_query": {
                "type": "STRING",
                "description": "Optional specific authentication concept or focus query (defaults to general auth/login search).",
            },
            "max_files_to_inspect": {
                "type": "INTEGER",
                "description": "Optional maximum number of security files to inspect (defaults to 5).",
            },
        },
        "required": [],
    }

    param_validators = {
        "auth_query": lambda val: isinstance(val, str),
        "max_files_to_inspect": lambda val: isinstance(val, int) and val > 0,
    }

    def execute(
        self,
        registry: ToolRegistry,
        context: Optional[InvestigationContext] = None,
        **kwargs: Any,
    ) -> SkillResult:
        """Executes authentication investigation."""
        auth_query = kwargs.get("auth_query", "").strip()
        search_query = auth_query if auth_query else "authentication login token password session middleware permission"
        max_inspect = min(kwargs.get("max_files_to_inspect", 5), 10)

        findings: List[Dict[str, Any]] = []
        evidence_locs: List[str] = []
        unresolved: List[str] = []

        candidate_files: List[str] = []

        # 1. Search code for key auth terms
        auth_keywords = ["login", "auth", "token", "password", "middleware", "jwt", "session"]
        for kw in auth_keywords:
            search_res = registry.execute("search_code", {"query": kw}, context=context)
            if search_res.success and isinstance(search_res.result, dict):
                matches = search_res.result.get("matches", [])
                for m in matches:
                    p = m.get("path")
                    line = m.get("line", 1)
                    snippet = m.get("snippet", "")
                    if p and p not in candidate_files:
                        candidate_files.append(p)
                    loc = f"{p}:{line}"
                    if p:
                        evidence_locs.append(loc)
                        findings.append(Finding(
                            description=f"Observed authentication keyword '{kw}' in {loc}: '{snippet}'",
                            finding_type="observed",
                            evidence_locations=[loc],
                        ).to_dict())

        # 2. Semantic retrieval for auth concepts
        rag_res = registry.execute("search_repository", {"query": search_query, "top_k": 5}, context=context)
        if rag_res.success and isinstance(rag_res.result, dict):
            chunks = rag_res.result.get("chunks", [])
            for c in chunks:
                p = c.get("path")
                if p:
                    if p not in candidate_files:
                        candidate_files.append(p)
                    loc = f"{p}:{c.get('start_line', 1)}-{c.get('end_line', 1)}"
                    evidence_locs.append(loc)

        if not candidate_files:
            unresolved.append("No authentication files or mechanisms discovered in repository.")
            return SkillResult(
                skill_name=self.name,
                status="completed",
                summary="Authentication investigation yielded no security candidate files.",
                findings=findings,
                evidence=[],
                unresolved_questions=unresolved,
            )

        # 3. Read candidate security files
        inspect_queue = candidate_files[:max_inspect]
        for filepath in inspect_queue:
            read_res = registry.execute("read_file", {"path": filepath}, context=context)
            if read_res.success and isinstance(read_res.result, dict):
                content = read_res.result.get("content", "")
                findings.append(Finding(
                    description=f"Inspected candidate security module '{filepath}'.",
                    finding_type="observed",
                    evidence_locations=[filepath],
                ).to_dict())
                if filepath not in evidence_locs:
                    evidence_locs.append(filepath)

        findings.append(Finding(
            description=f"Inferred authentication components located across {len(candidate_files)} file(s): {', '.join(candidate_files)}.",
            finding_type="inference",
            evidence_locations=candidate_files,
        ).to_dict())

        summary = (
            f"Authentication investigation completed across {len(candidate_files)} security file(s). "
            f"Inspected {len(inspect_queue)} key implementation files."
        )

        return SkillResult(
            skill_name=self.name,
            status="completed",
            summary=summary,
            findings=findings,
            evidence=list(dict.fromkeys(evidence_locs)),
            unresolved_questions=unresolved,
            metadata={"search_query": search_query, "security_files": candidate_files},
        )
