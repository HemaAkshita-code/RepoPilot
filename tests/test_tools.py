"""
Unit tests for Stage 2 repository investigation tools (Person 1 implementation).
Runs entirely offline with temporary directories.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.repository import Repository
from backend.tools import (
    list_files,
    read_file,
    search_code,
    resolve_safe_path,
    PathTraversalError,
)


class TestRepositoryTools(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory structure representing a sample repository
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

        # Create sample files
        (self.root / "README.md").write_text("# Test Repo\nRepository documentation", encoding="utf-8")

        src_dir = self.root / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "main.py").write_text("def main():\n    print('Hello World')\n    login('user')", encoding="utf-8")
        (src_dir / "auth.py").write_text("def login(user):\n    return True\n", encoding="utf-8")

        # Create ignored directories and files
        git_dir = self.root / ".git"
        git_dir.mkdir(parents=True, exist_ok=True)
        (git_dir / "config").write_text("git config data", encoding="utf-8")

        node_dir = self.root / "node_modules" / "express"
        node_dir.mkdir(parents=True, exist_ok=True)
        (node_dir / "index.js").write_text("module.exports = {};", encoding="utf-8")

        pycache_dir = self.root / "src" / "__pycache__"
        pycache_dir.mkdir(parents=True, exist_ok=True)
        (pycache_dir / "main.cpython-312.pyc").write_bytes(b"\x00\x01\x02\x03pyc_data")

        # Create a binary file
        bin_dir = self.root / "assets"
        bin_dir.mkdir(parents=True, exist_ok=True)
        self.binary_file = bin_dir / "image.png"
        self.binary_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00")

        # Create a large file
        large_content = "Line of text\n" * 10_000  # ~130 KB
        self.large_file = self.root / "large_file.txt"
        self.large_file.write_text(large_content, encoding="utf-8")

        # Create external directory and symlink (if OS allows)
        self.external_dir = tempfile.mkdtemp()
        self.secret_file = Path(self.external_dir) / "secret.txt"
        self.secret_file.write_text("SUPER_SECRET_TOKEN", encoding="utf-8")

        self.symlink_created = False
        try:
            self.symlink_file = self.root / "symlink_outside.txt"
            os.symlink(self.secret_file, self.symlink_file)
            self.symlink_created = True
        except (OSError, NotImplementedError, AttributeError):
            # Symlinks might fail on Windows without elevated privileges
            self.symlink_created = False

        # Repository abstraction object for compatibility testing
        self.repo_obj = Repository(root_path=self.root)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.external_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # 1. list_files() Tests
    # -------------------------------------------------------------------------
    def test_list_files_basic_and_nested(self):
        res = list_files(self.root)
        files = res["files"]

        self.assertIn("README.md", files)
        self.assertIn("src/main.py", files)
        self.assertIn("src/auth.py", files)
        self.assertIn("assets/image.png", files)

    def test_list_files_with_repository_object(self):
        res = list_files(self.repo_obj)
        files = res["files"]
        self.assertIn("src/main.py", files)

    def test_list_files_ignored_directories(self):
        res = list_files(self.root)
        files = res["files"]

        # Ensure ignored dirs are excluded
        for f in files:
            self.assertFalse(f.startswith(".git/"), f"Found ignored path: {f}")
            self.assertFalse(f.startswith("node_modules/"), f"Found ignored path: {f}")
            self.assertFalse("__pycache__" in f, f"Found ignored path: {f}")

    def test_list_files_deterministic_ordering(self):
        res1 = list_files(self.root)
        res2 = list_files(self.root)
        self.assertEqual(res1["files"], res2["files"])
        self.assertEqual(res1["files"], sorted(res1["files"]))

    def test_list_files_excludes_symlink_outside(self):
        if not self.symlink_created:
            self.skipTest("Symlinks not supported in current environment.")
        res = list_files(self.root)
        self.assertNotIn("symlink_outside.txt", res["files"])

    # -------------------------------------------------------------------------
    # 2. read_file() Tests
    # -------------------------------------------------------------------------
    def test_read_file_normal_text(self):
        res = read_file("src/main.py", self.root)
        self.assertIsNone(res["error"])
        self.assertFalse(res["is_binary"])
        self.assertFalse(res["truncated"])
        self.assertIn("def main():", res["content"])

    def test_read_file_with_repository_object(self):
        res = read_file("README.md", self.repo_obj)
        self.assertIsNone(res["error"])
        self.assertIn("Repository documentation", res["content"])

    def test_read_file_missing_file(self):
        res = read_file("nonexistent.py", self.root)
        self.assertIsNotNone(res["error"])
        self.assertIn("File not found", res["error"])

    def test_read_file_directory_path(self):
        res = read_file("src", self.root)
        self.assertIsNotNone(res["error"])
        self.assertIn("is a directory", res["error"])

    def test_read_file_absolute_path_rejection(self):
        abs_path = os.path.abspath(self.root / "README.md")
        res = read_file(abs_path, self.root)
        self.assertIsNotNone(res["error"])
        self.assertIn("Absolute paths are forbidden", res["error"])

    def test_read_file_path_traversal_rejection(self):
        malicious_paths = [
            "../../secret.txt",
            "../.env",
            "../../../etc/passwd",
            "src/../../secret.txt",
        ]
        for path in malicious_paths:
            with self.subTest(path=path):
                res = read_file(path, self.root)
                self.assertIsNotNone(res["error"])
                self.assertIn("Access denied", res["error"])

    def test_read_file_symlink_outside_rejection(self):
        if not self.symlink_created:
            self.skipTest("Symlinks not supported in current environment.")
        res = read_file("symlink_outside.txt", self.root)
        self.assertIsNotNone(res["error"])
        self.assertIn("Access denied", res["error"])

    def test_read_file_binary(self):
        res = read_file("assets/image.png", self.root)
        self.assertIsNone(res["error"])
        self.assertTrue(res["is_binary"])
        self.assertEqual(res["content"], "")

    def test_read_file_large_truncation(self):
        res = read_file("large_file.txt", self.root, max_bytes=100)
        self.assertIsNone(res["error"])
        self.assertTrue(res["truncated"])
        self.assertEqual(len(res["content"]), 100)

    # -------------------------------------------------------------------------
    # 3. search_code() Tests
    # -------------------------------------------------------------------------
    def test_search_code_basic(self):
        res = search_code("login", self.root)
        self.assertIsNone(res["error"])
        self.assertGreaterEqual(len(res["matches"]), 2)

        paths = [m["path"] for m in res["matches"]]
        self.assertIn("src/main.py", paths)
        self.assertIn("src/auth.py", paths)

    def test_search_code_case_insensitive(self):
        res = search_code("LOGIN", self.root, case_sensitive=False)
        self.assertGreaterEqual(len(res["matches"]), 2)

    def test_search_code_case_sensitive(self):
        res = search_code("LOGIN", self.root, case_sensitive=True)
        self.assertEqual(len(res["matches"]), 0)

    def test_search_code_snippets_and_lines(self):
        res = search_code("print('Hello World')", self.root)
        self.assertEqual(len(res["matches"]), 1)
        match = res["matches"][0]
        self.assertEqual(match["path"], "src/main.py")
        self.assertEqual(match["line"], 2)
        self.assertEqual(match["snippet"], "print('Hello World')")

    def test_search_code_ignores_binary_and_ignored_dirs(self):
        res = search_code("IHDR", self.root)
        self.assertEqual(len(res["matches"]), 0)

        res_git = search_code("git config", self.root)
        self.assertEqual(len(res_git["matches"]), 0)

    def test_search_code_max_matches_limit(self):
        res = search_code("def", self.root, max_matches=1)
        self.assertTrue(res["truncated"])
        self.assertEqual(len(res["matches"]), 1)

    def test_search_code_deterministic_ordering(self):
        res1 = search_code("def", self.root)
        res2 = search_code("def", self.root)
        self.assertEqual(res1["matches"], res2["matches"])


if __name__ == "__main__":
    unittest.main()
