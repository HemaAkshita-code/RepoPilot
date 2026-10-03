"""Stage 8 Failure-Case Evaluation Test Suite.

Verifies that RepoPilot handles invalid inputs, nonexistent paths/symbols, cyclic calls,
syntax errors, binary/oversized files, stale indexes, and iteration bounds safely without crashing or hallucinating.
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from backend.repository import load_local_repository, Repository
from backend.repository.exceptions import LocalRepositoryError
from backend.agent import ToolRegistry, RepoPilotAgent
from backend.analysis.index import StructuralIndex
from backend.skills import SkillManager


class TestFailureCases(unittest.TestCase):
    """Failure-case and resilience evaluation suite."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

        # Valid file
        (self.root / "main.py").write_text("def hello(): return 'world'\n", encoding="utf-8")
        
        # Syntax error file
        (self.root / "bad_syntax.py").write_text("def broken_func(: bad python code", encoding="utf-8")

        # Cyclic call chain
        (self.root / "cycle.py").write_text(
            "def func_a(): return func_b()\n"
            "def func_b(): return func_a()\n",
            encoding="utf-8",
        )

        # Binary file
        (self.root / "data.bin").write_bytes(bytes([0x80, 0xFF, 0x00, 0x01]))

        self.repo = Repository(root_path=self.root)
        self.registry = ToolRegistry(self.repo)
        self.registry.register_structural_tools()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_nonexistent_file_read(self):
        """Verify read_file returns structured error for missing file."""
        res = self.registry.execute("read_file", {"path": "nonexistent.py"})
        self.assertFalse(res.success)
        self.assertIn("File not found", str(res.error))

    def test_nonexistent_symbol_lookup(self):
        """Verify find_symbol gracefully returns count=0 for nonexistent symbol."""
        res = self.registry.execute("find_symbol", {"symbol_name": "nonexistent_function_xyz"})
        self.assertTrue(res.success)
        self.assertEqual(res.result["count"], 0)

    def test_nonexistent_search_query(self):
        """Verify search_code returns empty matches list without error."""
        res = self.registry.execute("search_code", {"query": "zxyzzy_absent_string_query_999"})
        self.assertTrue(res.success)
        self.assertEqual(len(res.result["matches"]), 0)

    def test_malformed_tool_arguments(self):
        """Verify tool registry rejects invalid parameter types or missing required parameters."""
        res = self.registry.execute("trace_call_flow", {"symbol": "", "depth": -5})
        self.assertFalse(res.success)
        self.assertIn("invalid type or value", str(res.error))

    def test_unknown_tool_rejection(self):
        """Verify execution of unregistered tool is cleanly rejected."""
        res = self.registry.execute("invalid_fake_tool", {})
        self.assertFalse(res.success)
        self.assertIn("Unknown tool", str(res.error))

    def test_unknown_skill_rejection(self):
        """Verify SkillManager rejects unknown skill requests."""
        manager = SkillManager()
        skill = manager.get_skill("nonexistent_skill_name")
        self.assertIsNone(skill)

    def test_syntax_error_parsing_resilience(self):
        """Verify AST indexer captures parse error for bad syntax file without crashing."""
        index = StructuralIndex(self.repo)
        index.build_index()
        self.assertIn("bad_syntax.py", index.parse_errors)

    def test_cyclic_call_flow_safety(self):
        """Verify call flow tracer handles cycles without infinite recursion."""
        index = StructuralIndex(self.repo)
        index.build_index()
        
        res = self.registry.execute("trace_call_flow", {"symbol": "func_a", "depth": 5})
        self.assertTrue(res.success)
        self.assertTrue(res.result.get("cycles_detected", False))

    def test_binary_file_handling(self):
        """Verify read_file safely handles binary files."""
        res = self.registry.execute("read_file", {"path": "data.bin"})
        self.assertTrue(res.success)
        self.assertTrue(res.result.get("is_binary", False))

    def test_invalid_repository_path(self):
        """Verify invalid repository path raises LocalRepositoryError."""
        nonexistent_path = self.root / "nonexistent_dir_123"
        with self.assertRaises(LocalRepositoryError):
            load_local_repository(nonexistent_path)

    def test_stale_index_detection(self):
        """Verify structural index detects staleness when repository files change."""
        index = StructuralIndex(self.repo)
        index.build_index()
        self.assertFalse(index.is_stale())

        # Modify a python file mtime/size
        (self.root / "main.py").write_text("def hello(): return 'updated world'\n", encoding="utf-8")
        self.assertTrue(index.is_stale())

    def test_agent_max_iterations_exhaustion(self):
        """Verify RepoPilotAgent terminates safely when max iteration limit is reached."""
        mock_gemma = MagicMock()
        # Keep returning tool call forever
        mock_gemma.generate_with_tools.return_value = {
            "text": "Searching code again...",
            "function_calls": [{"name": "search_code", "args": {"query": "hello"}}],
        }

        agent = RepoPilotAgent(registry=self.registry, gemma_client=mock_gemma, max_iterations=3)
        resp = agent.run("Infinite loop test")

        self.assertEqual(resp.status, "max_iterations_reached")
        self.assertEqual(resp.steps_count, 3)


if __name__ == "__main__":
    unittest.main()
