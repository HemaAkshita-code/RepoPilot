"""
Unit tests for Stage 6 Structural Analysis Engine (Person 1 Stage 6).
Tests AST parsing, symbol extraction, inheritance, imports, structural indexing, and staleness detection.
Runs 100% offline using temporary repositories.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from backend.analysis.analyzer import parse_python_file
from backend.analysis.index import StructuralIndex
from backend.analysis.models import Relationship, Symbol
from backend.repository import Repository


class TestPythonASTAnalyzer(unittest.TestCase):
    def test_parse_python_file_symbols_and_imports(self):
        content = """import os
from backend.services import user_service

class UserHandler:
    def __init__(self, user_id: str):
        self.user_id = user_id

    def handle(self):
        return user_service.get_user(self.user_id)

def main():
    handler = UserHandler("123")
    return handler.handle()
"""
        symbols, rels, err = parse_python_file("app/main.py", content)
        self.assertIsNone(err)

        sym_names = [s.name for s in symbols]
        self.assertIn("main", sym_names)
        self.assertIn("UserHandler", sym_names)
        self.assertIn("__init__", sym_names)
        self.assertIn("handle", sym_names)
        self.assertIn("main", sym_names)

        rel_types = [r.relationship_type for r in rels]
        self.assertIn("imports", rel_types)
        self.assertIn("contains", rel_types)
        self.assertIn("calls", rel_types)

    def test_parse_syntax_error_handling(self):
        invalid_content = "def broken_syntax(:\n    pass\n"
        symbols, rels, err = parse_python_file("broken.py", invalid_content)

        self.assertIsNotNone(err)
        self.assertIn("AST parse error", err)
        self.assertEqual(len(symbols), 1)  # Module fallback symbol
        self.assertEqual(symbols[0].symbol_type, "module")

    def test_parse_class_inheritance(self):
        content = """class BaseController:
    pass

class LoginController(BaseController):
    pass
"""
        symbols, rels, err = parse_python_file("controllers.py", content)
        self.assertIsNone(err)

        inherits_rels = [r for r in rels if r.relationship_type == "inherits"]
        self.assertEqual(len(inherits_rels), 1)
        self.assertEqual(inherits_rels[0].target, "BaseController")


class TestStructuralIndex(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

        (self.root / "README.md").write_text("# Test App\n", encoding="utf-8")

        auth_py = self.root / "auth.py"
        auth_py.write_text(
            "def verify_token(token: str):\n"
            "    return True\n\n"
            "def login(user: str, passw: str):\n"
            "    return verify_token(passw)\n",
            encoding="utf-8",
        )

        routes_py = self.root / "routes.py"
        routes_py.write_text(
            "import auth\n\n"
            "def login_route():\n"
            "    return auth.login('admin', 'secret')\n",
            encoding="utf-8",
        )

        self.repo = Repository(root_path=self.root)
        self.index = StructuralIndex(self.repo)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_build_index_and_find_symbols(self):
        self.index.build_index()

        syms = self.index.find_symbols("login")
        self.assertTrue(len(syms) > 0)
        sym_names = [s.name for s in syms]
        self.assertIn("login", sym_names)

        # Check exact symbol attributes
        login_sym = [s for s in syms if s.name == "login"][0]
        self.assertEqual(login_sym.symbol_type, "function")
        self.assertEqual(login_sym.file_path, "auth.py")

    def test_fingerprint_and_staleness_detection(self):
        self.index.build_index()
        self.assertFalse(self.index.is_stale())

        # Modify a file to trigger staleness
        (self.root / "auth.py").write_text("# Updated content\ndef login(): pass\n", encoding="utf-8")
        self.assertTrue(self.index.is_stale())

        # Calling ensure_up_to_date should rebuild index and reset staleness
        self.index.ensure_up_to_date()
        self.assertFalse(self.index.is_stale())

    def test_get_file_dependencies(self):
        self.index.build_index()
        deps = self.index.get_file_dependencies("routes.py")

        self.assertEqual(deps["file_path"], "routes.py")
        self.assertTrue(len(deps["imports"]) > 0)


if __name__ == "__main__":
    unittest.main()
