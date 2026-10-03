"""
BaseSkill abstract class for RepoPilot Agent Skills (Person 1 Stage 5).
Provides input validation, security checks, and standard interface for concrete skills.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from backend.agent.context import InvestigationContext
from backend.agent.registry import ToolRegistry
from .models import SkillMetadata, SkillResult


class BaseSkill(ABC):
    """
    Abstract Base Class for RepoPilot Agent Skills.
    A Skill is a structured, reusable, bounded investigation capability.
    """

    name: str
    description: str
    version: str = "1.0.0"
    parameters: Dict[str, Any]
    param_validators: Dict[str, Callable[[Any], bool]] = {}

    @property
    def metadata(self) -> SkillMetadata:
        """Returns the public metadata declaration for this skill."""
        return SkillMetadata(
            name=self.name,
            description=self.description,
            version=self.version,
            parameters=self.parameters,
        )

    def validate_args(self, args: Dict[str, Any]) -> Optional[str]:
        """
        Validates input arguments against the skill parameter schema and validators.

        Returns:
            Optional[str]: Error message if invalid, or None if arguments are valid.
        """
        # 1. Reject forbidden model-supplied repo_root
        if "repo_root" in args:
            return f"Security violation: Model is not permitted to specify 'repo_root' for skill '{self.name}'."

        required_params = self.parameters.get("required", [])
        allowed_props = self.parameters.get("properties", {})

        # 2. Check required parameters
        for req in required_params:
            if req not in args or args[req] is None:
                return f"Skill '{self.name}' missing required argument '{req}'."

        # 3. Check for unexpected arguments
        for k in args:
            if k not in allowed_props:
                return f"Skill '{self.name}' received unexpected argument '{k}'."

        # 4. Check custom type/value validators
        for k, v in args.items():
            if k in self.param_validators:
                try:
                    if not self.param_validators[k](v):
                        return f"Skill '{self.name}' argument '{k}' has invalid type or value: {v!r}."
                except Exception as e:
                    return f"Validation error for argument '{k}' in skill '{self.name}': {e}"

        return None

    @abstractmethod
    def execute(
        self,
        registry: ToolRegistry,
        context: Optional[InvestigationContext] = None,
        **kwargs: Any,
    ) -> SkillResult:
        """
        Executes bounded skill investigation using registered tools and retrieval.

        Args:
            registry: Central ToolRegistry for accessing repository tools.
            context: Optional InvestigationContext to accumulate evidence.
            **kwargs: Skill-specific keyword arguments.

        Returns:
            SkillResult: Structured investigation output with findings and evidence.
        """
        pass
