"""
RepoPilot Agent Skills package (Stage 5).
Provides reusable investigation skills, execution management, and data models.
"""

from .models import Finding, SkillResult, SkillMetadata
from .base import BaseSkill
from .manager import SkillManager
from .architecture import ArchitectureSkill
from .feature_trace import FeatureTraceSkill
from .api_flow import APIFlowSkill
from .auth import AuthSkill


def get_default_skill_manager() -> SkillManager:
    """
    Factory function that creates and returns a SkillManager
    pre-registered with all Stage 5 built-in Agent Skills.
    """
    manager = SkillManager()
    manager.register(ArchitectureSkill())
    manager.register(FeatureTraceSkill())
    manager.register(APIFlowSkill())
    manager.register(AuthSkill())
    return manager


__all__ = [
    "Finding",
    "SkillResult",
    "SkillMetadata",
    "BaseSkill",
    "SkillManager",
    "ArchitectureSkill",
    "FeatureTraceSkill",
    "APIFlowSkill",
    "AuthSkill",
    "get_default_skill_manager",
]
