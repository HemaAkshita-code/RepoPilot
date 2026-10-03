"""
RepoPilot Repository Indexing Package (Stage 4 - Person 2).
"""

from .chunking import CodeChunk, chunk_file, infer_language
from .embeddings import EmbeddingProvider, MockEmbeddingProvider, GoogleGenAIEmbeddingProvider, EmbeddingError
from .store import InMemoryVectorStore, VectorSearchResult, cosine_similarity
from .indexer import RepositoryIndexer, is_binary_file

__all__ = [
    "CodeChunk",
    "chunk_file",
    "infer_language",
    "EmbeddingProvider",
    "MockEmbeddingProvider",
    "GoogleGenAIEmbeddingProvider",
    "EmbeddingError",
    "InMemoryVectorStore",
    "VectorSearchResult",
    "cosine_similarity",
    "RepositoryIndexer",
    "is_binary_file",
]
