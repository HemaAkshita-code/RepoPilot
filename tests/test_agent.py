"""
Unit tests for Person 1 Stage 3 Agent Core.
Runs entirely offline with mocked Gemma responses and temporary repositories.
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from backend.repository import Repository
from backend.agent import RepoPilotAgent, ToolRegistry, AgentResponse
from backend.gemma import GemmaAPIError


class TestRepoPilotAgent(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

        # Create sample files
        (self.root / "README.md").write_text("# Test App\nRepo description", encoding="utf-8")

        src_dir = self.root / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "auth.py").write_text("def login(user, password):\n    # Authentication logic\n    return True\n", encoding="utf-8")
        (src_dir / "main.py").write_text("from src.auth import login\n\ndef run():\n    login('admin', 'secret')\n", encoding="utf-8")

        self.repo = Repository(root_path=self.root)
        self.registry = ToolRegistry(self.repo)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_final_answer_without_tool_call(self):
        mock_gemma = MagicMock()
        mock_gemma.generate_with_tools.return_value = {
            "text": "This repository is a Python application.",
            "function_calls": [],
        }

        agent = RepoPilotAgent(registry=self.registry, gemma_client=mock_gemma)
        resp = agent.run("What is this repository?")

        self.assertIsInstance(resp, AgentResponse)
        self.assertEqual(resp.status, "completed")
        self.assertEqual(resp.final_answer, "This repository is a Python application.")
        self.assertEqual(resp.steps_count, 1)

    def test_one_tool_call(self):
        mock_gemma = MagicMock()
        mock_gemma.generate_with_tools.side_effect = [
            # Turn 1: Model requests list_files
            {
                "text": "Let me inspect the file structure first.",
                "function_calls": [{"name": "list_files", "args": {}}],
            },
            # Turn 2: Model returns final answer
            {
                "text": "The repository contains README.md, src/auth.py, and src/main.py.",
                "function_calls": [],
            },
        ]

        agent = RepoPilotAgent(registry=self.registry, gemma_client=mock_gemma)
        resp = agent.run("List the files in the repository.")

        self.assertEqual(resp.status, "completed")
        self.assertIn("src/auth.py", resp.final_answer)
        self.assertEqual(resp.steps_count, 2)
        self.assertIn("README.md", resp.evidence)

    def test_multi_step_sequential_tool_calls(self):
        """
        Required scenario:
        1. search_code("authentication")
        2. read_file("src/auth.py")
        3. Final grounded answer
        """
        mock_gemma = MagicMock()
        mock_gemma.generate_with_tools.side_effect = [
            # Step 1: Request search_code
            {
                "text": "I will search for authentication code.",
                "function_calls": [{"name": "search_code", "args": {"query": "Authentication"}}],
            },
            # Step 2: Request read_file on src/auth.py
            {
                "text": "Found match in src/auth.py. Let me read it.",
                "function_calls": [{"name": "read_file", "args": {"path": "src/auth.py"}}],
            },
            # Step 3: Provide final answer grounded in evidence
            {
                "text": "Authentication is implemented in src/auth.py via the login(user, password) function.",
                "function_calls": [],
            },
        ]

        agent = RepoPilotAgent(registry=self.registry, gemma_client=mock_gemma)
        resp = agent.run("Where is authentication implemented and how does it work?")

        self.assertEqual(resp.status, "completed")
        self.assertEqual(resp.steps_count, 3)
        self.assertIn("src/auth.py", resp.evidence)
        self.assertIn("login(user, password)", resp.final_answer)

    def test_unknown_tool_call_recovery(self):
        mock_gemma = MagicMock()
        mock_gemma.generate_with_tools.side_effect = [
            # Turn 1: Model requests unknown tool
            {
                "text": "Trying to run unknown tool.",
                "function_calls": [{"name": "execute_shell", "args": {"cmd": "ls"}}],
            },
            # Turn 2: Model handles error and calls list_files instead
            {
                "text": "Fallback to list_files.",
                "function_calls": [{"name": "list_files", "args": {}}],
            },
            # Turn 3: Final answer
            {
                "text": "Repository listing complete.",
                "function_calls": [],
            },
        ]

        agent = RepoPilotAgent(registry=self.registry, gemma_client=mock_gemma)
        resp = agent.run("Show repository files.")

        self.assertEqual(resp.status, "completed")
        self.assertEqual(resp.steps_count, 3)

    def test_malformed_arguments_handling(self):
        mock_gemma = MagicMock()
        mock_gemma.generate_with_tools.side_effect = [
            # Turn 1: Missing required argument 'path'
            {
                "text": "Reading file without path.",
                "function_calls": [{"name": "read_file", "args": {}}],
            },
            # Turn 2: Correct call with valid path
            {
                "text": "Reading with correct path.",
                "function_calls": [{"name": "read_file", "args": {"path": "README.md"}}],
            },
            # Turn 3: Final answer
            {
                "text": "README content read.",
                "function_calls": [],
            },
        ]

        agent = RepoPilotAgent(registry=self.registry, gemma_client=mock_gemma)
        resp = agent.run("Read README.")

        self.assertEqual(resp.status, "completed")
        self.assertIn("README.md", resp.evidence)

    def test_maximum_iteration_limit(self):
        mock_gemma = MagicMock()
        # Always return another tool call
        mock_gemma.generate_with_tools.return_value = {
            "text": "Still searching...",
            "function_calls": [{"name": "list_files", "args": {}}],
        }

        agent = RepoPilotAgent(registry=self.registry, gemma_client=mock_gemma, max_iterations=3)
        resp = agent.run("Loop forever question")

        self.assertEqual(resp.status, "max_iterations_reached")
        self.assertEqual(resp.steps_count, 3)
        self.assertIn("Reached maximum iteration limit", resp.final_answer)

    def test_model_api_error_handling(self):
        mock_gemma = MagicMock()
        mock_gemma.generate_with_tools.side_effect = GemmaAPIError("API connection timeout")

        agent = RepoPilotAgent(registry=self.registry, gemma_client=mock_gemma)
        resp = agent.run("Fail question")

        self.assertEqual(resp.status, "error")
        self.assertIn("API connection timeout", resp.error)

    def test_empty_question_handling(self):
        agent = RepoPilotAgent(registry=self.registry)
        resp = agent.run("   ")

        self.assertEqual(resp.status, "error")
        self.assertIn("Invalid question", resp.final_answer)

    def test_arbitrary_function_attempt(self):
        mock_gemma = MagicMock()
        mock_gemma.generate_with_tools.side_effect = [
            {
                "text": "Attempting arbitrary function",
                "function_calls": [{"name": "__import__", "args": {"name": "os"}}],
            },
            {
                "text": "Unable to execute arbitrary function.",
                "function_calls": [],
            },
        ]

        agent = RepoPilotAgent(registry=self.registry, gemma_client=mock_gemma)
        resp = agent.run("Run arbitrary code")

        self.assertEqual(resp.status, "completed")
        self.assertIn("Unable to execute", resp.final_answer)


if __name__ == "__main__":
    unittest.main()
