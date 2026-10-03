"""
Entry point for executing RepoPilot Stage 3 Agent investigations.
"""

import sys
from pathlib import Path

# Add project root to sys.path to support running as script or module
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.config import get_settings, ConfigurationError
from backend.repository import load_local_repository
from backend.agent import ToolRegistry, RepoPilotAgent


def main() -> None:
    """Execute Stage 3 RepoPilot investigation demo."""
    try:
        settings = get_settings()
        print(f"Loaded RepoPilot configuration for model: {settings.model}")
    except ConfigurationError as e:
        print(f"Configuration warning: {e}", file=sys.stderr)
        print("Note: Set GEMMA_API_KEY and GEMMA_MODEL in .env to run with real LLM endpoints.\n")

    # Step 1: Load repository
    repo_path = project_root
    print(f"Loading local repository at: {repo_path}")
    repository = load_local_repository(repo_path)

    # Step 2: Initialize Tool Registry
    registry = ToolRegistry(repository)
    print(f"Registered tools: {', '.join(registry.list_tools())}")

    # Step 3: Initialize Agent
    agent = RepoPilotAgent(registry=registry, verbose=True)

    # Step 4: Run Question
    question = "Where are the repository investigation tools implemented?"
    print(f"\nUser Question: {question}\n")

    response = agent.run(question)

    print("\n" + "=" * 50)
    print("INVESTIGATION COMPLETE")
    print("=" * 50)
    print(f"Status: {response.status}")
    print(f"Steps taken: {response.steps_count}")
    print(f"Evidence gathered: {', '.join(response.evidence) if response.evidence else 'None'}")
    print("\nFinal Answer:")
    print(response.final_answer)


if __name__ == "__main__":
    main()
