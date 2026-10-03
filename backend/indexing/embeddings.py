"""
Embedding provider abstraction and implementations for RepoPilot Stage 4.
"""

import math
import hashlib
from typing import List, Optional


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""
    pass


class EmbeddingProvider:
    """Base interface for generating text embeddings."""

    def embed_text(self, text: str) -> List[float]:
        """Embeds a single string into a float vector."""
        raise NotImplementedError

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embeds a list of strings into a list of float vectors."""
        return [self.embed_text(t) for t in texts]


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic, offline embedding provider for testing and default local operation.
    Generates unit-normalized float vectors using character n-gram feature hashing.
    """

    def __init__(self, dimension: int = 64):
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> List[float]:
        """Generates a deterministic, normalized vector from text features."""
        if not text:
            return [0.0] * self._dimension

        vec = [0.0] * self._dimension
        words = text.lower().split()

        for word in words:
            for i in range(len(word) - 2):
                ngram = word[i : i + 3]
                h = int(hashlib.md5(ngram.encode("utf-8")).hexdigest(), 16)
                idx = h % self._dimension
                val = 1.0 if (h % 2 == 0) else -1.0
                vec[idx] += val

        # Normalize to unit length
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0:
            return [0.0] * self._dimension
        return [v / norm for v in vec]


class GoogleGenAIEmbeddingProvider(EmbeddingProvider):
    """
    Embedding provider powered by the Google GenAI SDK (e.g. text-embedding-004).
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-004"):
        self._api_key = api_key
        self._model = model
        self._fallback = MockEmbeddingProvider()

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding using Google GenAI SDK if available, else fallback cleanly."""
        try:
            from google import genai
            from backend.config import get_settings
            
            key = self._api_key or get_settings().api_key
            client = genai.Client(api_key=key)
            
            response = client.models.embed_content(
                model=self._model,
                contents=text,
            )
            if hasattr(response, "embedding") and hasattr(response.embedding, "values"):
                return list(response.embedding.values)
            if isinstance(response, dict) and "embedding" in response:
                return list(response["embedding"])
        except Exception:
            pass

        # Clean fallback if credentials/SDK are absent in offline environments
        return self._fallback.embed_text(text)
