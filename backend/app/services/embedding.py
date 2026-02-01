"""
Embedding Service.

Generates embeddings using HuggingFace's nomic-embed-text model.
"""

import logging
from typing import List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generates embeddings using nomic-embed-text-v1.5 model."""

    def __init__(self):
        """Initialize embedding service."""
        self._model: Optional[SentenceTransformer] = None
        self._cache: dict = {}  # Simple in-memory cache

    @property
    def model_name(self) -> str:
        """Get the model name."""
        return get_settings().embedding_model

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return get_settings().embedding_dimension

    def _get_model(self) -> SentenceTransformer:
        """Lazy load the embedding model."""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(
                self.model_name,
                trust_remote_code=True  # Required for nomic model
            )
            logger.info("Embedding model loaded successfully")
        return self._model

    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            768-dimensional embedding vector

        Raises:
            ValueError: If text is empty
        """
        if not text or not text.strip():
            raise ValueError("Cannot generate embedding for empty text")

        text = text.strip()

        # Check cache
        cache_key = hash(text)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Generate embedding
        try:
            model = self._get_model()
            embedding = model.encode(text, normalize_embeddings=True)

            # Convert to list of floats
            embedding_list = embedding.tolist()

            # Validate dimension
            if len(embedding_list) != self.dimension:
                raise ValueError(
                    f"Unexpected embedding dimension: {len(embedding_list)}, "
                    f"expected {self.dimension}"
                )

            # Cache result
            self._cache[cache_key] = embedding_list

            return embedding_list

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def batch_embed(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings (None for empty texts)
        """
        if not texts:
            return []

        results: List[Optional[List[float]]] = []

        # Filter out empty texts
        valid_indices = []
        valid_texts = []

        for i, text in enumerate(texts):
            if text and text.strip():
                valid_indices.append(i)
                valid_texts.append(text.strip())
            else:
                results.append(None)

        if not valid_texts:
            return results

        try:
            model = self._get_model()
            embeddings = model.encode(valid_texts, normalize_embeddings=True)

            # Reconstruct results with None for empty inputs
            embedding_idx = 0
            final_results: List[Optional[List[float]]] = []

            for i in range(len(texts)):
                if i in valid_indices:
                    final_results.append(embeddings[embedding_idx].tolist())
                    embedding_idx += 1
                else:
                    final_results.append(None)

            return final_results

        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise

    def cosine_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Vectors should already be normalized, but normalize again to be safe
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = np.dot(vec1, vec2) / (norm1 * norm2)

        # Clamp to [0, 1] range (can be slightly outside due to floating point)
        return float(max(0.0, min(1.0, similarity)))

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._cache.clear()
        logger.info("Embedding cache cleared")


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get singleton embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
