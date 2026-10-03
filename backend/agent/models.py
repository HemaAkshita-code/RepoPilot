"""
Data structures for Agent Core, Tool Registry, and Execution State.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolCall:
    """Represents a tool call request made by the model."""
    name: str
    args: Dict[str, Any]
    call_id: Optional[str] = None


@dataclass
class ToolResult:
    """Represents the outcome of executing a registered tool."""
    success: bool
    tool_name: str
    result: Any
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert ToolResult to dictionary representation."""
        return {
            "success": self.success,
            "tool_name": self.tool_name,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class AgentStep:
    """Represents one turn/step in the agent's investigation loop."""
    step_number: int
    thought: Optional[str] = None
    tool_calls: List[ToolCall] = field(default_factory=list)
    tool_results: List[ToolResult] = field(default_factory=list)


@dataclass
class AgentState:
    """
    Tracks complete execution state for a RepoPilot agent run.
    """
    question: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    steps: List[AgentStep] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    final_answer: Optional[str] = None
    iteration_count: int = 0
    max_iterations: int = 8
    status: str = "initialized"
    error: Optional[str] = None


@dataclass
class AgentResponse:
    """Final response returned to the user after agent execution."""
    question: str
    final_answer: str
    evidence: List[str]
    steps_count: int
    status: str
    error: Optional[str] = None
