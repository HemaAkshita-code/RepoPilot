"""
Retrieval abstraction for Stage 4 (Person 1 implementation).
Connects Agent Core to RepositoryIndexer and vector store.
"""

from typing import List, Optional, Union
from backend.indexing.indexer import RepositoryIndexer
from backend.indexing.store import VectorSearchResult


class RepositoryRetriever:
    """
    Retrieves semantic repository chunks from an indexed repository.
    """

    def __init__(self, indexer: RepositoryIndexer):
        self._indexer = indexer

    @property
    def indexer(self) -> RepositoryIndexer:
        return self._indexer

    def ensure_indexed(self) -> None:
        """Ensures the repository is indexed before retrieval."""
        if not self._indexer.is_indexed():
            self._indexer.index_repository()

    def retrieve(self, query: str, top_k: int = 5) -> List[VectorSearchResult]:
        """
        Retrieves top-k relevant repository chunks for a query string.

        Args:
            query: User search query string.
            top_k: Maximum number of chunks to retrieve (default 5).

        Returns:
            List[VectorSearchResult]: Ranked list of retrieval results with source metadata.
        """
        if not query or not isinstance(query, str) or not query.strip():
            return []

        self.ensure_indexed()

        query_vec = self._indexer.embedding_provider.embed_text(query.strip())
        return self._indexer.vector_store.search(query_vec, top_k=top_k)
