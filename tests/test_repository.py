"""
Unit tests for Stage 2 repository acquisition and management layer.
These tests run entirely offline and do not require network access.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from backend.repository import (
    Repository,
    load_local_repository,
    load_github_repository,
    validate_github_url,
    parse_github_url,
    WorkspaceManager,
    LocalRepositoryError,
    InvalidGitHubURLError,
    GitHubCloneError,
    WorkspaceError,
)


class TestLocalRepository(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_valid_local_directory(self):
        repo = load_local_repository(self.temp_dir)
        self.assertIsInstance(repo, Repository)
        self.assertEqual(repo.root_path, Path(self.temp_dir).resolve())
        self.assertEqual(repo.source_type, "local")

    def test_nested_local_directory(self):
        nested_dir = Path(self.temp_dir) / "subfolder" / "nested_repo"
        nested_dir.mkdir(parents=True, exist_ok=True)

        repo = load_local_repository(nested_dir)
        self.assertEqual(repo.root_path, nested_dir.resolve())
        self.assertEqual(repo.source_type, "local")

    def test_nonexistent_path(self):
        nonexistent = Path(self.temp_dir) / "does_not_exist"
        with self.assertRaises(LocalRepositoryError) as ctx:
            load_local_repository(nonexistent)
        self.assertIn("does not exist", str(ctx.exception))

    def test_file_passed_as_repository(self):
        file_path = Path(self.temp_dir) / "sample_file.txt"
        file_path.write_text("hello world")

        with self.assertRaises(LocalRepositoryError) as ctx:
            load_local_repository(file_path)
        self.assertIn("is a file, not a directory", str(ctx.exception))

    def test_empty_path(self):
        with self.assertRaises(LocalRepositoryError):
            load_local_repository("")

    @patch("os.access", return_value=False)
    def test_inaccessible_directory(self, mock_access):
        with self.assertRaises(LocalRepositoryError) as ctx:
            load_local_repository(self.temp_dir)
        self.assertIn("not accessible", str(ctx.exception))


class TestRepositoryAbstraction(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_valid_root_path_and_normalization(self):
        # Pass path with trailing slashes / unnormalized components
        raw_path = os.path.join(self.temp_dir, ".", "")
        repo = Repository(root_path=raw_path, source_type="local")
        self.assertEqual(repo.root_path, Path(self.temp_dir).resolve())
        self.assertEqual(str(repo), f"Repository[local] at {Path(self.temp_dir).resolve()}")

    def test_invalid_root_rejected(self):
        nonexistent = Path(self.temp_dir) / "fake_dir"
        with self.assertRaises(LocalRepositoryError):
            Repository(root_path=nonexistent)

    def test_equality(self):
        repo1 = Repository(root_path=self.temp_dir, source_type="local")
        repo2 = Repository(root_path=self.temp_dir, source_type="local")
        self.assertEqual(repo1, repo2)


class TestGitHubURLValidation(unittest.TestCase):
    def test_valid_public_github_url(self):
        url = "https://github.com/psf/requests"
        self.assertTrue(validate_github_url(url))
        owner, repo, canonical = parse_github_url(url)
        self.assertEqual(owner, "psf")
        self.assertEqual(repo, "requests")
        self.assertEqual(canonical, "https://github.com/psf/requests.git")

    def test_valid_url_with_git_suffix(self):
        url = "https://github.com/psf/requests.git"
        self.assertTrue(validate_github_url(url))
        owner, repo, canonical = parse_github_url(url)
        self.assertEqual(owner, "psf")
        self.assertEqual(repo, "requests")
        self.assertEqual(canonical, "https://github.com/psf/requests.git")

    def test_valid_url_with_trailing_slash(self):
        url = "https://github.com/psf/requests/"
        self.assertTrue(validate_github_url(url))
        owner, repo, _ = parse_github_url(url)
        self.assertEqual(owner, "psf")
        self.assertEqual(repo, "requests")

    def test_malformed_urls(self):
        invalid_urls = [
            "",
            "not_a_url",
            "github.com/owner/repo",  # missing scheme
            "http://github.com/owner/repo",  # unsupported scheme http
            "ssh://git@github.com/owner/repo.git",  # unsupported scheme ssh
            "https://gitlab.com/owner/repo",  # non-github domain
            "https://github.com/",  # missing owner and repo
            "https://github.com/owner",  # missing repo
            "https://github.com/owner/repo/tree/main",  # extra path segment
            "https://user:pass@github.com/owner/repo",  # embedded credentials
            "https://github.com/../etc/passwd",  # traversal path
        ]
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(validate_github_url(url))
                with self.assertRaises(InvalidGitHubURLError):
                    parse_github_url(url)


class TestWorkspaceManagement(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.workspace = WorkspaceManager(workspace_root=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_controlled_workspace_isolation(self):
        # Ensure clone directory is strictly inside workspace_root
        target_dir = self.workspace.prepare_clone_directory("owner", "repo")
        self.assertTrue(target_dir.is_relative_to(self.workspace.workspace_root))

        # Verify clone destination is outside current repository root
        project_root = Path(__file__).resolve().parents[2]
        self.assertFalse(target_dir.is_relative_to(project_root))

    def test_prevent_directory_traversal(self):
        with self.assertRaises(WorkspaceError):
            self.workspace.cleanup_directory(Path(self.temp_dir).parent)


class TestGitHubCloningSubprocess(unittest.TestCase):
    def setUp(self):
        self.temp_workspace = tempfile.mkdtemp()
        self.workspace = WorkspaceManager(workspace_root=self.temp_workspace)

    def tearDown(self):
        shutil.rmtree(self.temp_workspace, ignore_errors=True)

    @patch("shutil.which", return_value="/usr/bin/git")
    @patch("subprocess.run")
    def test_successful_mocked_clone(self, mock_run, mock_which):
        # Setup mock subprocess run to create target directory and succeed
        def fake_clone(cmd, **kwargs):
            target_path = Path(cmd[-1])
            target_path.mkdir(parents=True, exist_ok=True)
            mock_res = MagicMock()
            mock_res.returncode = 0
            return mock_res

        mock_run.side_effect = fake_clone

        url = "https://github.com/torvalds/linux"
        repo = load_github_repository(url, workspace_manager=self.workspace)

        self.assertIsInstance(repo, Repository)
        self.assertEqual(repo.source_type, "github")
        self.assertEqual(repo.url, "https://github.com/torvalds/linux.git")
        self.assertTrue(repo.root_path.is_relative_to(self.workspace.workspace_root))
        mock_run.assert_called_once()

    @patch("shutil.which", return_value=None)
    def test_git_missing_error(self, mock_which):
        url = "https://github.com/owner/repo"
        with self.assertRaises(GitHubCloneError) as ctx:
            load_github_repository(url, workspace_manager=self.workspace)
        self.assertIn("Git executable not found", str(ctx.exception))

    @patch("shutil.which", return_value="/usr/bin/git")
    @patch("subprocess.run")
    def test_clone_failure_handling(self, mock_run, mock_which):
        mock_res = MagicMock()
        mock_res.returncode = 128
        mock_res.stderr = "fatal: repository 'https://github.com/owner/nonexistent' not found"
        mock_run.return_value = mock_res

        url = "https://github.com/owner/nonexistent"
        with self.assertRaises(GitHubCloneError) as ctx:
            load_github_repository(url, workspace_manager=self.workspace)
        self.assertIn("Git clone failed", str(ctx.exception))


class TestLiveGitHubCloning(unittest.TestCase):
    """
    Live network integration tests.
    Only runs if RUN_NETWORK_TESTS=1 environment variable is explicitly set.
    """

    @unittest.skipUnless(os.environ.get("RUN_NETWORK_TESTS") == "1", "Skipping live network tests. Set RUN_NETWORK_TESTS=1 to run.")
    def test_live_public_github_clone(self):
        url = "https://github.com/octocat/Hello-World"
        repo = load_github_repository(url)
        self.assertIsInstance(repo, Repository)
        self.assertEqual(repo.source_type, "github")
        self.assertTrue(repo.root_path.exists())
        self.assertTrue((repo.root_path / "README").exists() or (repo.root_path / "README.md").exists())
        # Clean up cloned live repo
        WorkspaceManager().cleanup_directory(repo.root_path)


if __name__ == "__main__":
    unittest.main()

