"""CLI Entry Point and Demonstration Interface for RepoPilot Stage 8.

Executes end-to-end repository investigations using Gemma 4, ToolRegistry,
Semantic Retrieval, Structural Analysis, and Evidence Provenance tracking.
Supports deterministic offline mode when GEMMA_API_KEY is omitted.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to sys.path to support running as script or module
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.config import get_settings, ConfigurationError
from backend.repository import load_local_repository
from backend.agent import ToolRegistry, RepoPilotAgent, RepositoryRetriever
from backend.indexing import RepositoryIndexer, MockEmbeddingProvider


def main() -> None:
    """Execute RepoPilot investigation demo."""
    print("=" * 60)
    print("RepoPilot - Open-Source Repository Investigation Agent")
    print("=" * 60)

    # Step 1: Load target repository (default to deterministic fixture)
    fixture_dir = project_root / "tests" / "fixtures" / "fixture_repo"
    repo_path = fixture_dir if fixture_dir.exists() else project_root
    
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        repo_path = Path(sys.argv[1]).resolve()

    print(f"\n[1] Ingesting repository: {repo_path}")
    repository = load_local_repository(repo_path)

    # Step 2: Build indexing and Tool Registry
    indexer = RepositoryIndexer(repository, embedding_provider=MockEmbeddingProvider())
    retriever = RepositoryRetriever(indexer)
    registry = ToolRegistry(repository, retriever=retriever)
    registry.register_structural_tools()

    tools_list = registry.list_tools()
    print(f"[2] Registered Tools ({len(tools_list)}): {', '.join(tools_list)}")

    # Step 3: Configure Gemma LLM Client or Deterministic Offline Mock
    gemma_client = None
    try:
        settings = get_settings()
        print(f"[3] Initialized Gemma LLM Endpoint: model={settings.model}")
    except ConfigurationError as e:
        print(f"[3] Notice: GEMMA_API_KEY not set ({e}). Running in deterministic offline demo mode.")
        mock_client = MagicMock()
        mock_client.generate_with_tools.side_effect = [
            # Step 1: Structural call flow tracing
            {
                "text": "Tracing call flow from login_route endpoint.",
                "function_calls": [{"name": "trace_call_flow", "args": {"symbol": "login_route", "depth": 3}}],
            },
            # Step 2: Read auth.py for source verification
            {
                "text": "Inspecting app/auth.py for authentication implementation.",
                "function_calls": [{"name": "read_file", "args": {"path": "app/auth.py"}}],
            },
            # Step 3: Final evidence-backed response
            {
                "text": (
                    "Login flow investigation complete:\n"
                    "1. API Endpoint: `login_route` in `app/routes.py` receives request credentials.\n"
                    "2. Authentication: `login_route` calls `authenticate_user()` in `app/auth.py`.\n"
                    "3. Database Lookup: `authenticate_user()` calls `get_user_by_id()` in `app/database.py`.\n"
                    "4. Token Creation: Upon successful verification, `create_access_token()` generates an auth token."
                ),
                "function_calls": [],
            },
        ]
        gemma_client = mock_client

    # Step 4: Run Investigation Question
    question = (
        "Trace the login flow from the API endpoint to the database and explain where authentication occurs."
    )
    if len(sys.argv) > 2:
        question = sys.argv[2]

    print(f"\n[4] User Investigation Question:\n    \"{question}\"\n")
    print("--- Executing Agent Investigation Loop ---")

    agent = RepoPilotAgent(registry=registry, gemma_client=gemma_client, verbose=True)
    response = agent.run(question)

    print("\n" + "=" * 60)
    print("INVESTIGATION RESULTS")
    print("=" * 60)
    print(f"Status: {response.status}")
    print(f"Total Tool Steps: {response.steps_count}")
    print(f"Collected Evidence ({len(response.evidence)} items):")
    for ev in response.evidence:
        print(f"  - {ev}")

    print("\nFinal Explanation:")
    print(response.final_answer)
    print("=" * 60)


if __name__ == "__main__":
    main()
