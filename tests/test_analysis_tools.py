"""
Unit tests for Stage 6 Structural Tools & ToolRegistry Integration (Person 2 Stage 6).
Tests find_symbol, find_references, get_symbol_relationships, get_file_dependencies, security bounds, and ToolRegistry binding.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from backend.agent.registry import ToolRegistry
from backend.analysis.tools import (
    find_references,
    find_symbol,
    get_file_dependencies,
    get_symbol_relationships,
    trace_call_flow,
)
from backend.repository import Repository


class TestStructuralTools(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

        (self.root / "README.md").write_text("# Test Service\n", encoding="utf-8")

        auth_py = self.root / "auth.py"
        auth_py.write_text(
            "def verify_password(p):\n"
            "    return True\n\n"
            "def authenticate_user(u, p):\n"
            "    return verify_password(p)\n",
            encoding="utf-8",
        )

        routes_py = self.root / "routes.py"
        routes_py.write_text(
            "import auth\n\n"
            "def login_handler():\n"
            "    return auth.authenticate_user('user', 'pass')\n",
            encoding="utf-8",
        )

        self.repo = Repository(root_path=self.root)
        self.registry = ToolRegistry(self.repo)
        self.registry.register_structural_tools()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_find_symbol_tool(self):
        res = self.registry.execute("find_symbol", {"symbol_name": "authenticate_user"})
        self.assertTrue(res.success)
        self.assertEqual(res.result["count"], 1)
        self.assertEqual(res.result["symbols"][0]["name"], "authenticate_user")
        self.assertEqual(res.result["symbols"][0]["file_path"], "auth.py")

    def test_find_references_tool(self):
        res = self.registry.execute("find_references", {"symbol_name": "authenticate_user"})
        self.assertTrue(res.success)
        self.assertTrue(len(res.result["definitions"]) > 0)
        self.assertTrue(len(res.result["ast_references"]) > 0 or len(res.result["textual_matches"]) > 0)

    def test_get_symbol_relationships_tool(self):
        res = self.registry.execute("get_symbol_relationships", {"symbol_name": "authenticate_user"})
        self.assertTrue(res.success)
        self.assertTrue(res.result["count"] > 0)

    def test_get_file_dependencies_tool(self):
        res = self.registry.execute("get_file_dependencies", {"file_path": "routes.py"})
        self.assertTrue(res.success)
        self.assertEqual(res.result["file_path"], "routes.py")
        self.assertTrue(len(res.result["imports"]) > 0)

    def test_security_path_traversal_rejection(self):
        res = self.registry.execute("get_file_dependencies", {"file_path": "../outside.py"})
        self.assertFalse(res.success)
        self.assertIn("Security boundary violation", res.error)

    def test_rejection_of_model_supplied_repo_root(self):
        res = self.registry.execute("find_symbol", {"symbol_name": "authenticate_user", "repo_root": "/etc"})
        self.assertFalse(res.success)
        self.assertIn("Security violation", res.error)


if __name__ == "__main__":
    unittest.main()
