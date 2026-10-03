"""
In-memory vector store supporting cosine similarity search over CodeChunk embeddings.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple
from .chunking import CodeChunk


@dataclass
class VectorSearchResult:
    """
    Represents a ranked retrieval result containing the CodeChunk and similarity score.
    """
    chunk: CodeChunk
    score: float

    def to_dict(self) -> dict:
        """Returns dictionary representation of retrieval result."""
        d = self.chunk.to_dict()
        d["score"] = round(self.score, 4)
        return d


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Calculates cosine similarity between two float vectors."""
    if len(vec_a) != len(vec_b) or not vec_a:
        return 0.0

    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


class InMemoryVectorStore:
    """
    Lightweight, deterministic in-memory vector store for CodeChunk embeddings.
    """

    def __init__(self):
        # Maps chunk_id -> (CodeChunk, vector)
        self._index: Dict[str, Tuple[CodeChunk, List[float]]] = {}

    def add_chunks(self, chunks: List[CodeChunk], embeddings: List[List[float]]) -> None:
        """
        Adds or updates chunks and their corresponding embedding vectors in the index.

        Args:
            chunks: List of CodeChunk objects.
            embeddings: List of matching float vectors.
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings lists must be of equal length.")

        for chunk, vec in zip(chunks, embeddings):
            self._index[chunk.chunk_id] = (chunk, vec)

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[VectorSearchResult]:
        """
        Performs vector similarity search against the stored index.

        Args:
            query_embedding: Float vector representing the search query.
            top_k: Maximum number of top results to return.

        Returns:
            List[VectorSearchResult]: Ranked list of search results sorted by similarity score descending.
        """
        if not self._index or not query_embedding or top_k <= 0:
            return []

        results: List[VectorSearchResult] = []

        for chunk_id, (chunk, vector) in self._index.items():
            if len(vector) != len(query_embedding):
                continue
            score = cosine_similarity(query_embedding, vector)
            results.append(VectorSearchResult(chunk=chunk, score=score))

        # Sort deterministically by score descending, then chunk_id ascending
        results.sort(key=lambda r: (-r.score, r.chunk.chunk_id))

        return results[:top_k]

    def clear(self) -> None:
        """Clears all stored entries from the index."""
        self._index.clear()

    def count(self) -> int:
        """Returns the total number of indexed chunks."""
        return len(self._index)

    def is_empty(self) -> bool:
        """Returns True if the index contains no chunks."""
        return len(self._index) == 0
