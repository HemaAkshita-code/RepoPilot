"""
Repository Indexer pipeline for RepoPilot Stage 4 (Person 2 implementation).
Safely traverses repository files, extracts deterministic chunks, and builds vector store.
"""

import os
from pathlib import Path
from typing import Optional, Union, List

from backend.repository.models import Repository
from backend.tools.security import get_canonical_root, DEFAULT_IGNORED_DIRS
from .chunking import CodeChunk, chunk_file
from .embeddings import EmbeddingProvider, MockEmbeddingProvider
from .store import InMemoryVectorStore


def is_binary_file(file_path: Path) -> bool:
    """Checks if a file contains NUL bytes indicating binary content."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            return b"\x00" in chunk
    except OSError:
        return True


class RepositoryIndexer:
    """
    Indexes a repository by reading text files, creating line-bounded chunks,
    generating embeddings, and storing them in a vector store.
    """

    def __init__(
        self,
        repository: Union[str, Path, Repository],
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[InMemoryVectorStore] = None,
        chunk_size_lines: int = 40,
        overlap_lines: int = 10,
        max_file_bytes: int = 500_000,
    ):
        if isinstance(repository, Repository):
            self._repo = repository
            self._root_path = repository.root_path
        else:
            self._repo = Repository(root_path=repository)
            self._root_path = self._repo.root_path

        self._embedding_provider = embedding_provider or MockEmbeddingProvider()
        self._vector_store = vector_store or InMemoryVectorStore()
        self._chunk_size_lines = chunk_size_lines
        self._overlap_lines = overlap_lines
        self._max_file_bytes = max_file_bytes

    @property
    def repository(self) -> Repository:
        return self._repo

    @property
    def root_path(self) -> Path:
        return self._root_path

    @property
    def embedding_provider(self) -> EmbeddingProvider:
        return self._embedding_provider

    @property
    def vector_store(self) -> InMemoryVectorStore:
        return self._vector_store

    def is_indexed(self) -> bool:
        """Returns True if the vector store contains indexed chunks."""
        return not self._vector_store.is_empty()

    def index_repository(self, clean_existing: bool = True) -> int:
        """
        Executes repository indexing pipeline.

        Args:
            clean_existing: If True, clears existing vector store entries before indexing.

        Returns:
            int: Number of total chunks successfully indexed into the vector store.
        """
        if clean_existing:
            self._vector_store.clear()

        all_chunks: List[CodeChunk] = []

        # Safe traversal using canonical root and ignore list
        canonical_root = get_canonical_root(self._root_path)

        for dirpath, dirnames, filenames in os.walk(canonical_root, followlinks=False):
            # Prune ignored directories in-place
            dirnames[:] = [
                d for d in dirnames
                if d not in DEFAULT_IGNORED_DIRS and not d.startswith(".git")
            ]

            for filename in filenames:
                file_full_path = Path(dirpath) / filename

                # Safety and symlink check
                try:
                    resolved_file = file_full_path.resolve(strict=True)
                    resolved_file.relative_to(canonical_root)
                except (ValueError, OSError):
                    continue

                if not resolved_file.is_file():
                    continue

                # Skip large files or binary files
                try:
                    if resolved_file.stat().st_size > self._max_file_bytes:
                        continue
                except OSError:
                    continue

                if is_binary_file(resolved_file):
                    continue

                rel_path = file_full_path.relative_to(canonical_root).as_posix()

                try:
                    with open(resolved_file, "r", encoding="utf-8", errors="replace") as f:
                        text_content = f.read()
                except OSError:
                    continue

                file_chunks = chunk_file(
                    relative_path=rel_path,
                    content=text_content,
                    chunk_size_lines=self._chunk_size_lines,
                    overlap_lines=self._overlap_lines,
                )
                all_chunks.extend(file_chunks)

        if not all_chunks:
            return 0

        # Generate embeddings in batch
        texts = [c.content for c in all_chunks]
        embeddings = self._embedding_provider.embed_batch(texts)

        # Store in vector store
        self._vector_store.add_chunks(all_chunks, embeddings)

        return self._vector_store.count()
