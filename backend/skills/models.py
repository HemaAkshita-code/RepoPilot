"""
Data models for Stage 5 RepoPilot Agent Skills.
Defines structured findings, skill execution outcomes, and metadata.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Finding:
    """
    Represents an individual finding discovered during skill execution.

    Attributes:
        description: Textual description of the observation or inference.
        finding_type: Classification of finding ("observed" or "inference").
        evidence_locations: List of source file line ranges or paths supporting the finding.
    """
    description: str
    finding_type: str = "observed"
    evidence_locations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converts Finding to a serializable dictionary representation."""
        return {
            "description": self.description,
            "finding_type": self.finding_type,
            "evidence_locations": self.evidence_locations,
        }


@dataclass
class SkillResult:
    """
    Structured outcome returned by an Agent Skill execution.

    Attributes:
        skill_name: Name of the executed skill.
        status: Execution status ("completed", "failed", "limit_reached").
        summary: High-level summary of the skill investigation results.
        findings: List of structured findings (dicts or Finding instances).
        evidence: List of cited source locations (e.g. 'backend/api.py:10-25').
        unresolved_questions: List of unresolved questions or missing evidence areas.
        metadata: Optional skill execution metadata.
        error: Error message string if execution failed.
    """
    skill_name: str
    status: str
    summary: str
    findings: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    unresolved_questions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converts SkillResult to a serializable dictionary representation."""
        return {
            "skill_name": self.skill_name,
            "status": self.status,
            "summary": self.summary,
            "findings": self.findings,
            "evidence": list(dict.fromkeys(self.evidence)),
            "unresolved_questions": self.unresolved_questions,
            "metadata": self.metadata,
            "error": self.error,
        }


@dataclass
class SkillMetadata:
    """
    Public metadata schema for an Agent Skill.

    Attributes:
        name: Unique identifier string for the skill.
        description: Human-readable description of what the skill investigates.
        version: Semantic version string.
        parameters: JSON Schema dictionary defining accepted input arguments.
    """
    name: str
    description: str
    version: str
    parameters: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Converts SkillMetadata to a serializable dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "parameters": self.parameters,
        }
