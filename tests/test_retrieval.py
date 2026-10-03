"""
Unit tests for Person 1 Stage 4 Retrieval, InvestigationContext, and RAG Agent Integration.
Runs 100% offline with mocked Gemma model responses.
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from backend.repository import Repository
from backend.indexing import RepositoryIndexer, MockEmbeddingProvider, InMemoryVectorStore
from backend.agent import (
    RepositoryRetriever,
    InvestigationContext,
    EvidenceItem,
    ToolRegistry,
    RepoPilotAgent,
    AgentResponse,
)


class TestRetrievalAndContext(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

        # Create source files
        (self.root / "README.md").write_text("# Project\nRepo documentation", encoding="utf-8")
        src = self.root / "src"
        src.mkdir(parents=True, exist_ok=True)
        (src / "auth.py").write_text("def authenticate_user(username, password):\n    # Validate user credentials\n    return True\n", encoding="utf-8")
        (src / "middleware.py").write_text("from src.auth import authenticate_user\n\ndef auth_middleware(req):\n    return authenticate_user('user', 'pass')\n", encoding="utf-8")

        self.repo = Repository(root_path=self.root)
        self.indexer = RepositoryIndexer(self.repo, embedding_provider=MockEmbeddingProvider())
        self.retriever = RepositoryRetriever(self.indexer)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_repository_retriever(self):
        results = self.retriever.retrieve("authenticate_user", top_k=2)
        self.assertGreater(len(results), 0)
        self.assertLessEqual(len(results), 2)

        first_res = results[0]
        self.assertTrue(hasattr(first_res.chunk, "chunk_id"))
        self.assertIn("src/", first_res.chunk.path)

    def test_investigation_context_distinction(self):
        ctx = InvestigationContext()
        ctx.add_retrieved_chunk("src/auth.py", 1, 40, "def authenticate_user():", 0.92)
        ctx.add_inspected_file("src/auth.py", "full text")

        self.assertEqual(len(ctx.retrieved_chunks), 1)
        self.assertEqual(len(ctx.inspected_files), 1)
        self.assertEqual(ctx.retrieved_chunks[0].evidence_type, "retrieved_chunk")
        self.assertEqual(ctx.inspected_files[0].evidence_type, "inspected_file")

        # Citation formatting
        locs = ctx.get_all_source_locations()
        self.assertIn("src/auth.py:1-40", locs)
        self.assertIn("src/auth.py", locs)

    def test_search_repository_tool_registration(self):
        registry = ToolRegistry(self.repo, retriever=self.retriever)
        tools = registry.list_tools()
        self.assertIn("search_repository", tools)

        # Execute search_repository via registry
        res = registry.execute("search_repository", {"query": "authenticate"})
        self.assertTrue(res.success)
        self.assertIn("chunks", res.result)
        self.assertGreater(len(res.result["chunks"]), 0)


class TestRAGAgentIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

        src = self.root / "src"
        src.mkdir(parents=True, exist_ok=True)
        (src / "auth.py").write_text("def authenticate_user(username, password):\n    return True\n", encoding="utf-8")
        (src / "routes.py").write_text("from src.auth import authenticate_user\n\ndef login_route():\n    return authenticate_user('admin', 'secret')\n", encoding="utf-8")

        self.repo = Repository(root_path=self.root)
        self.indexer = RepositoryIndexer(self.repo, embedding_provider=MockEmbeddingProvider())
        self.retriever = RepositoryRetriever(self.indexer)
        self.registry = ToolRegistry(self.repo, retriever=self.retriever)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_agent_rag_multi_step_investigation_scenario(self):
        """
        Required scenario:
        1. Agent calls search_repository("authentication") -> receives vector chunks
        2. Agent calls read_file("src/auth.py") -> verifies full file
        3. Agent produces final grounded answer with citation references
        """
        mock_gemma = MagicMock()
        mock_gemma.generate_with_tools.side_effect = [
            # Step 1: Semantic search_repository
            {
                "text": "Searching repository semantically for authentication.",
                "function_calls": [{"name": "search_repository", "args": {"query": "authentication"}}],
            },
            # Step 2: Read specific file for confirmation
            {
                "text": "Retrieved chunk from src/auth.py. Reading full file.",
                "function_calls": [{"name": "read_file", "args": {"path": "src/auth.py"}}],
            },
            # Step 3: Final answer citing evidence
            {
                "text": "Authentication is implemented in src/auth.py:1-40 via authenticate_user().",
                "function_calls": [],
            },
        ]

        agent = RepoPilotAgent(registry=self.registry, gemma_client=mock_gemma)
        resp = agent.run("Where is authentication implemented and how does it work?")

        self.assertEqual(resp.status, "completed")
        self.assertEqual(resp.steps_count, 3)
        self.assertIn("src/auth.py", resp.evidence)
        self.assertTrue(any("src/auth.py" in ev for ev in resp.evidence))
        self.assertIn("authenticate_user()", resp.final_answer)


if __name__ == "__main__":
    unittest.main()
