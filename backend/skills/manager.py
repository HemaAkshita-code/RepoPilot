"""
SkillManager implementation for RepoPilot Agent Skills (Person 1 Stage 5).
Manages skill registration, lookup, input validation, safe execution, and tool registry binding.
"""

from typing import Any, Dict, List, Optional

from backend.agent.context import InvestigationContext
from backend.agent.registry import ToolRegistry
from .base import BaseSkill
from .models import SkillResult


class SkillManager:
    """
    Central registry and execution manager for RepoPilot Agent Skills.
    Guarantees input validation, boundary enforcement, and structured error reporting.
    """

    def __init__(self) -> None:
        self._skills: Dict[str, BaseSkill] = {}

    def register(self, skill: BaseSkill) -> None:
        """
        Registers a BaseSkill instance into the manager.

        Args:
            skill: An instance of a concrete BaseSkill subclass.
        """
        if not isinstance(skill, BaseSkill):
            raise TypeError(f"Expected BaseSkill instance, got {type(skill)}")
        self._skills[skill.name] = skill

    def get_skill(self, name: str) -> Optional[BaseSkill]:
        """Returns the registered BaseSkill for a given skill name."""
        return self._skills.get(name)

    def list_skills(self) -> List[str]:
        """Returns a list of registered skill names."""
        return list(self._skills.keys())

    def get_skill_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Returns serializable metadata dictionary for a specific skill."""
        skill = self.get_skill(name)
        return skill.metadata.to_dict() if skill else None

    def get_all_skill_metadata(self) -> List[Dict[str, Any]]:
        """Returns a list of serializable metadata dictionaries for all registered skills."""
        return [skill.metadata.to_dict() for skill in self._skills.values()]

    def execute_skill(
        self,
        name: str,
        args: Dict[str, Any],
        registry: ToolRegistry,
        context: Optional[InvestigationContext] = None,
    ) -> SkillResult:
        """
        Safely executes a registered skill after validating inputs.

        Args:
            name: Name of the skill to execute.
            args: Input arguments provided for the skill.
            registry: Central ToolRegistry for repository tools access.
            context: Optional InvestigationContext for evidence tracking.

        Returns:
            SkillResult: Structured execution outcome.
        """
        skill = self.get_skill(name)
        if not skill:
            allowed = ", ".join(self.list_skills()) if self._skills else "none"
            return SkillResult(
                skill_name=name,
                status="failed",
                summary=f"Unknown skill '{name}'.",
                error=f"Unknown skill '{name}'. Allowed skills are: {allowed}",
            )

        validation_error = skill.validate_args(args)
        if validation_error:
            return SkillResult(
                skill_name=name,
                status="failed",
                summary=f"Input validation failed for skill '{name}'.",
                error=validation_error,
            )

        try:
            return skill.execute(registry=registry, context=context, **args)
        except Exception as e:
            return SkillResult(
                skill_name=name,
                status="failed",
                summary=f"Execution error encountered in skill '{name}'.",
                error=f"Unexpected error executing skill '{name}': {e}",
            )

    def register_skills_to_tool_registry(self, registry: ToolRegistry) -> None:
        """
        Adapts registered Skills into ToolRegistry as model-callable capabilities.
        """
        for skill in self._skills.values():
            registry.register_skill(skill)
