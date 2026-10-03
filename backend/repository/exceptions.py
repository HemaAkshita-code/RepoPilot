"""
Custom exception hierarchy for RepoPilot Stage 2 repository management.
"""

class RepositoryError(Exception):
    """Base exception for all repository-related errors."""
    pass


class LocalRepositoryError(RepositoryError):
    """Raised when a local repository path cannot be loaded or is invalid."""
    pass


class InvalidGitHubURLError(RepositoryError):
    """Raised when a provided GitHub URL is malformed or unsupported."""
    pass


class GitHubCloneError(RepositoryError):
    """Raised when cloning a GitHub repository fails or Git is missing."""
    pass


class WorkspaceError(RepositoryError):
    """Raised when controlled workspace creation or isolation fails."""
    pass
