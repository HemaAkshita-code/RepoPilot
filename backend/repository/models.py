"""
Repository abstraction representing a loaded codebase on the local filesystem.
"""

from pathlib import Path
from typing import Optional
from .exceptions import LocalRepositoryError


class Repository:
    """
    Abstraction representing a repository available on the local filesystem.

    Attributes:
        root_path (Path): The normalized, validated local filesystem path to the repository root.
        source_type (str): The origin of the repository ("local" or "github").
        url (Optional[str]): The original GitHub URL if cloned from GitHub, else None.
    """

    def __init__(
        self,
        root_path: str | Path,
        source_type: str = "local",
        url: Optional[str] = None,
    ):
        if not root_path:
            raise LocalRepositoryError("Repository root path cannot be empty.")

        try:
            path_obj = Path(root_path).resolve()
        except Exception as e:
            raise LocalRepositoryError(f"Invalid repository root path format: {e}")

        if not path_obj.exists():
            raise LocalRepositoryError(f"Repository root path does not exist: '{path_obj}'")

        if not path_obj.is_dir():
            raise LocalRepositoryError(f"Repository root path is not a directory: '{path_obj}'")

        self._root_path: Path = path_obj
        self._source_type: str = source_type
        self._url: Optional[str] = url

    @property
    def root_path(self) -> Path:
        """Returns the normalized root Path of the repository."""
        return self._root_path

    @property
    def source_type(self) -> str:
        """Returns the repository source type ('local' or 'github')."""
        return self._source_type

    @property
    def url(self) -> Optional[str]:
        """Returns the source URL if available."""
        return self._url

    def __repr__(self) -> str:
        return f"Repository(root_path='{self._root_path}', source_type='{self._source_type}')"

    def __str__(self) -> str:
        return f"Repository[{self._source_type}] at {self._root_path}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Repository):
            return False
        return self._root_path == other._root_path and self._source_type == other._source_type
