"""
Unit tests for Embedding Service.

TDD: These tests are written BEFORE implementation.
Tests should FAIL until embedding.py is implemented.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestEmbeddingService:
    """Test suite for embedding generation functionality."""

    # ========================================================================
    # Embedding Generation Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_generate_embedding_returns_vector(self):
        """Should generate 768-dimensional embedding vector."""
        from app.services.embedding import EmbeddingService

        service = EmbeddingService()
        text = "This is a sample resume text for embedding."

        embedding = await service.embed(text)

        assert embedding is not None
        assert isinstance(embedding, list)
        assert len(embedding) == 768
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.asyncio
    async def test_generate_embedding_for_empty_text_raises_error(self):
        """Should raise error for empty text input."""
        from app.services.embedding import EmbeddingService

        service = EmbeddingService()

        with pytest.raises(ValueError, match="empty"):
            await service.embed("")

    @pytest.mark.asyncio
    async def test_generate_embedding_for_whitespace_only_raises_error(self):
        """Should raise error for whitespace-only input."""
        from app.services.embedding import EmbeddingService

        service = EmbeddingService()

        with pytest.raises(ValueError, match="empty"):
            await service.embed("   \n\t  ")

    @pytest.mark.asyncio
    async def test_embedding_values_are_normalized(self):
        """Embedding values should be normalized (between -1 and 1)."""
        from app.services.embedding import EmbeddingService

        service = EmbeddingService()
        text = "Sample text for normalization test."

        embedding = await service.embed(text)

        assert all(-1.0 <= x <= 1.0 for x in embedding)

    # ========================================================================
    # Batch Embedding Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_batch_embed_multiple_texts(self):
        """Should generate embeddings for multiple texts."""
        from app.services.embedding import EmbeddingService

        service = EmbeddingService()
        texts = [
            "First resume text",
            "Second job description",
            "Third document content"
        ]

        embeddings = await service.batch_embed(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == 768 for emb in embeddings)

    @pytest.mark.asyncio
    async def test_batch_embed_empty_list_returns_empty(self):
        """Should return empty list for empty input."""
        from app.services.embedding import EmbeddingService

        service = EmbeddingService()

        embeddings = await service.batch_embed([])

        assert embeddings == []

    @pytest.mark.asyncio
    async def test_batch_embed_skips_empty_texts(self):
        """Should skip empty texts in batch and return None for them."""
        from app.services.embedding import EmbeddingService

        service = EmbeddingService()
        texts = ["Valid text", "", "Another valid text"]

        embeddings = await service.batch_embed(texts)

        assert len(embeddings) == 3
        assert embeddings[0] is not None
        assert embeddings[1] is None
        assert embeddings[2] is not None

    # ========================================================================
    # Model Configuration Tests
    # ========================================================================

    def test_uses_nomic_embed_model(self):
        """Should use nomic-embed-text-v1.5 model."""
        from app.services.embedding import EmbeddingService

        service = EmbeddingService()

        assert "nomic" in service.model_name.lower()

    def test_embedding_dimension_is_768(self):
        """Embedding dimension should be 768."""
        from app.services.embedding import EmbeddingService

        service = EmbeddingService()

        assert service.dimension == 768

    # ========================================================================
    # Similarity Calculation Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_cosine_similarity_identical_texts(self):
        """Identical texts should have similarity close to 1.0."""
        from app.services.embedding import EmbeddingService

        service = EmbeddingService()
        text = "Software engineer with Python experience"

        emb1 = await service.embed(text)
        emb2 = await service.embed(text)

        similarity = service.cosine_similarity(emb1, emb2)

        assert similarity > 0.99

    @pytest.mark.asyncio
    async def test_cosine_similarity_similar_texts(self):
        """Similar texts should have high similarity."""
        from app.services.embedding import EmbeddingService

        service = EmbeddingService()
        text1 = "Python developer with machine learning experience"
        text2 = "Machine learning engineer proficient in Python"

        emb1 = await service.embed(text1)
        emb2 = await service.embed(text2)

        similarity = service.cosine_similarity(emb1, emb2)

        assert similarity > 0.7

    @pytest.mark.asyncio
    async def test_cosine_similarity_different_texts(self):
        """Very different texts should have lower similarity."""
        from app.services.embedding import EmbeddingService

        service = EmbeddingService()
        text1 = "Software engineer with Python experience"
        text2 = "Professional chef specializing in French cuisine"

        emb1 = await service.embed(text1)
        emb2 = await service.embed(text2)

        similarity = service.cosine_similarity(emb1, emb2)

        # Different domain texts should have lower similarity than similar texts
        # Note: modern embedding models may still find some semantic overlap
        assert similarity < 0.7

    # ========================================================================
    # Error Handling Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_handles_model_loading_error(self):
        """Should handle model loading errors gracefully."""
        from app.services.embedding import EmbeddingService

        service = EmbeddingService()

        # Mock the model getter to raise an error
        with patch.object(service, '_get_model', side_effect=Exception("Model load error")):
            with pytest.raises(Exception):
                await service.embed("test text")

    @pytest.mark.asyncio
    async def test_handles_encoding_error(self):
        """Should handle encoding errors gracefully."""
        from app.services.embedding import EmbeddingService

        service = EmbeddingService()
        mock_model = MagicMock()
        mock_model.encode.side_effect = Exception("Encoding failed")

        with patch.object(service, '_get_model', return_value=mock_model):
            with pytest.raises(Exception):
                await service.embed("test text")

    # ========================================================================
    # Caching Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_caches_repeated_embeddings(self):
        """Should cache embeddings for repeated texts."""
        from app.services.embedding import EmbeddingService

        service = EmbeddingService()
        text = "Repeated text for caching test"

        # First call - should hit API
        emb1 = await service.embed(text)
        # Second call - should use cache
        emb2 = await service.embed(text)

        assert emb1 == emb2
