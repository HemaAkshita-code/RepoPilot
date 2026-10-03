"""
GitHub repository validator and loader for Stage 2.
"""

import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

from .models import Repository
from .exceptions import InvalidGitHubURLError, GitHubCloneError
from .workspace import WorkspaceManager


# Pattern for valid GitHub username/organization and repository names
GITHUB_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+$")


def parse_github_url(url: str) -> Tuple[str, str, str]:
    """
    Parses and validates a public GitHub repository URL.

    Args:
        url: The input URL string.

    Returns:
        Tuple[str, str, str]: (owner, repo_name, canonical_https_url)

    Raises:
        InvalidGitHubURLError: If the URL is invalid, malformed, or unsupported.
    """
    if not url or not isinstance(url, str):
        raise InvalidGitHubURLError("GitHub URL must be a non-empty string.")

    url_str = url.strip()

    try:
        parsed = urlparse(url_str)
    except Exception as e:
        raise InvalidGitHubURLError(f"Malformed URL: {e}")

    # Enforce HTTPS scheme
    if parsed.scheme.lower() != "https":
        raise InvalidGitHubURLError(f"Unsupported URL scheme '{parsed.scheme}'. Only HTTPS public GitHub URLs are supported.")

    # Enforce github.com domain
    netloc = parsed.netloc.lower()
    if netloc != "github.com":
        raise InvalidGitHubURLError(f"Invalid domain '{parsed.netloc}'. Only 'github.com' is supported.")

    # Reject URLs containing credentials (e.g. user:pass@github.com)
    if parsed.username or parsed.password:
        raise InvalidGitHubURLError("GitHub URLs containing user credentials are not supported.")

    # Clean and split path segments
    path = parsed.path.strip("/")
    if not path:
        raise InvalidGitHubURLError("URL is missing repository owner and name.")

    segments = [s for s in path.split("/") if s]

    if len(segments) != 2:
        raise InvalidGitHubURLError("GitHub URL must contain exactly owner and repository name (e.g. https://github.com/owner/repo).")

    owner, repo_name = segments[0], segments[1]

    # Handle trailing .git suffix
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    # Validate owner and repo name against allowable GitHub characters
    if not GITHUB_IDENTIFIER_PATTERN.match(owner) or owner in (".", ".."):
        raise InvalidGitHubURLError(f"Invalid GitHub repository owner name: '{owner}'")

    if not GITHUB_IDENTIFIER_PATTERN.match(repo_name) or repo_name in (".", ".."):
        raise InvalidGitHubURLError(f"Invalid GitHub repository name: '{repo_name}'")

    canonical_url = f"https://github.com/{owner}/{repo_name}.git"

    return owner, repo_name, canonical_url


def validate_github_url(url: str) -> bool:
    """
    Helper function to check if a URL is a valid public GitHub URL.

    Returns:
        bool: True if valid, False otherwise.
    """
    try:
        parse_github_url(url)
        return True
    except InvalidGitHubURLError:
        return False


def load_github_repository(
    url: str,
    workspace_manager: Optional[WorkspaceManager] = None,
    timeout: int = 120,
) -> Repository:
    """
    Clones a public GitHub repository into a controlled workspace and returns a Repository object.

    Args:
        url: Public GitHub repository HTTPS URL.
        workspace_manager: Optional WorkspaceManager instance.
        timeout: Maximum seconds allowed for git clone subprocess execution.

    Returns:
        Repository: Initialized Repository abstraction.

    Raises:
        InvalidGitHubURLError: If the GitHub URL format is invalid.
        GitHubCloneError: If Git is missing or the clone command fails.
    """
    owner, repo_name, canonical_url = parse_github_url(url)

    if workspace_manager is None:
        workspace_manager = WorkspaceManager()

    # Verify Git executable is present
    git_path = shutil.which("git")
    if not git_path:
        raise GitHubCloneError("Git executable not found on system PATH. Please install Git to clone repositories.")

    target_dir = workspace_manager.prepare_clone_directory(owner, repo_name, clean_existing=True)

    # Safe subprocess command invocation (no shell=True, arguments passed as list)
    cmd = [git_path, "clone", "--depth", "1", canonical_url, str(target_dir)]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        workspace_manager.cleanup_directory(target_dir)
        raise GitHubCloneError(f"Git clone operation timed out after {timeout} seconds.")
    except Exception as e:
        workspace_manager.cleanup_directory(target_dir)
        raise GitHubCloneError(f"Failed to execute git clone: {e}")

    if result.returncode != 0:
        workspace_manager.cleanup_directory(target_dir)
        stderr_msg = result.stderr.strip() if result.stderr else "Unknown git error"
        raise GitHubCloneError(f"Git clone failed for '{owner}/{repo_name}': {stderr_msg}")

    return Repository(root_path=target_dir, source_type="github", url=canonical_url)
