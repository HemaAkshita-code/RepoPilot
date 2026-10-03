"""
RepoPilot Repository Management & Acquisition Package (Stage 2).
"""

from .models import Repository
from .exceptions import (
    RepositoryError,
    LocalRepositoryError,
    InvalidGitHubURLError,
    GitHubCloneError,
    WorkspaceError,
)
from .local import load_local_repository
from .github import load_github_repository, validate_github_url, parse_github_url
from .workspace import WorkspaceManager

__all__ = [
    "Repository",
    "RepositoryError",
    "LocalRepositoryError",
    "InvalidGitHubURLError",
    "GitHubCloneError",
    "WorkspaceError",
    "load_local_repository",
    "load_github_repository",
    "validate_github_url",
    "parse_github_url",
    "WorkspaceManager",
]
