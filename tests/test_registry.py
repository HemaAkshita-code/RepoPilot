"""
Unit tests for Person 2 Stage 3 Tool Registry and Adapter.
Runs entirely offline using temporary test repositories.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from backend.repository import Repository
from backend.agent.registry import ToolRegistry
from backend.agent.models import ToolResult


class TestToolRegistry(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

        # Create sample files
        (self.root / "README.md").write_text("# Sample Repo\nDocumentation content", encoding="utf-8")
        src_dir = self.root / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "auth.py").write_text("def login(username, password):\n    return True\n", encoding="utf-8")

        self.repo = Repository(root_path=self.root)
        self.registry = ToolRegistry(self.repo)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_registered_tools_list(self):
        tools = self.registry.list_tools()
        self.assertIn("list_files", tools)
        self.assertIn("read_file", tools)
        self.assertIn("search_code", tools)
        self.assertIn("search_repository", tools)
        self.assertEqual(len(tools), 4)

    def test_valid_and_invalid_tool_lookup(self):
        self.assertIsNotNone(self.registry.get_tool("read_file"))
        self.assertIsNotNone(self.registry.get_tool("search_repository"))
        self.assertIsNone(self.registry.get_tool("eval_shell"))

    def test_model_facing_tool_schemas(self):
        schemas = self.registry.get_model_tools()
        self.assertEqual(len(schemas), 4)

        tool_names = [s["name"] for s in schemas]
        self.assertIn("list_files", tool_names)
        self.assertIn("read_file", tool_names)
        self.assertIn("search_code", tool_names)

        # Ensure repo_root is NEVER exposed in model-facing parameters
        for s in schemas:
            props = s["parameters"].get("properties", {})
            self.assertNotIn("repo_root", props, f"repo_root exposed in model schema for {s['name']}")

    def test_required_argument_validation(self):
        # read_file missing 'path'
        err = self.registry.validate_args("read_file", {})
        self.assertIsNotNone(err)
        self.assertIn("missing required argument 'path'", err)

        # search_code missing 'query'
        err_query = self.registry.validate_args("search_code", {})
        self.assertIsNotNone(err_query)
        self.assertIn("missing required argument 'query'", err_query)

    def test_invalid_argument_types(self):
        # path is integer instead of string
        err = self.registry.validate_args("read_file", {"path": 123})
        self.assertIsNotNone(err)
        self.assertIn("invalid type or value", err)

    def test_unexpected_arguments(self):
        err = self.registry.validate_args("read_file", {"path": "README.md", "unknown_arg": "value"})
        self.assertIsNotNone(err)
        self.assertIn("unexpected argument 'unknown_arg'", err)

    def test_rejection_of_model_supplied_repo_root(self):
        res = self.registry.execute("read_file", {"path": "README.md", "repo_root": "/etc"})
        self.assertFalse(res.success)
        self.assertIn("Security violation", res.error)

    def test_rejection_of_unknown_tool_execution(self):
        res = self.registry.execute("arbitrary_exec", {"code": "import os"})
        self.assertFalse(res.success)
        self.assertIn("Unknown tool 'arbitrary_exec'", res.error)

    def test_actual_list_files_execution(self):
        res = self.registry.execute("list_files", {})
        self.assertTrue(res.success)
        self.assertIsInstance(res.result, dict)
        self.assertIn("README.md", res.result["files"])
        self.assertIn("src/auth.py", res.result["files"])

    def test_actual_read_file_execution(self):
        res = self.registry.execute("read_file", {"path": "src/auth.py"})
        self.assertTrue(res.success)
        self.assertIn("def login", res.result["content"])

    def test_actual_search_code_execution(self):
        res = self.registry.execute("search_code", {"query": "login"})
        self.assertTrue(res.success)
        self.assertEqual(len(res.result["matches"]), 1)
        self.assertEqual(res.result["matches"][0]["path"], "src/auth.py")

    def test_structured_tool_error_handling(self):
        # Attempt to read nonexistent file
        res = self.registry.execute("read_file", {"path": "nonexistent.txt"})
        self.assertFalse(res.success)
        self.assertIsNotNone(res.error)
        self.assertIn("File not found", res.error)


if __name__ == "__main__":
    unittest.main()
