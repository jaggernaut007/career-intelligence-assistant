"""
Application Configuration.

Loads configuration from environment variables with sensible defaults.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ========================================================================
    # OpenAI Configuration
    # ========================================================================
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field("gpt-5.2", description="OpenAI model to use")

    # ========================================================================
    # Neo4j Configuration
    # ========================================================================
    neo4j_uri: str = Field(..., description="Neo4j connection URI")
    neo4j_username: str = Field("neo4j", description="Neo4j username")
    neo4j_password: str = Field(..., description="Neo4j password")

    # ========================================================================
    # HuggingFace Configuration
    # ========================================================================
    hf_token: Optional[str] = Field(None, description="HuggingFace API token")
    embedding_model: str = Field(
        "nomic-ai/nomic-embed-text-v1.5",
        description="HuggingFace embedding model"
    )
    embedding_dimension: int = Field(768, description="Embedding vector dimension")

    # ========================================================================
    # LlamaIndex Configuration
    # ========================================================================
    llamaindex_chunk_size: int = Field(512, description="Chunk size for text splitting")
    llamaindex_chunk_overlap: int = Field(50, description="Overlap between chunks")
    vector_similarity_threshold: float = Field(0.75, description="Threshold for semantic match")
    neo4j_vector_index_name: str = Field("career_vectors", description="Neo4j vector index name")

    # ========================================================================
    # Server Configuration
    # ========================================================================
    host: str = Field("0.0.0.0", description="Server host")
    port: int = Field(8000, description="Server port")

    # ========================================================================
    # Application Configuration
    # ========================================================================
    session_secret_key: str = Field(
        "dev-secret-key-change-in-prod",
        description="Secret key for session management"
    )
    rate_limit_per_minute: int = Field(10, description="Rate limit per minute per session")
    max_file_size_mb: int = Field(10, description="Maximum file size in MB")
    max_content_length: int = Field(50000, description="Maximum content length in characters")
    max_jobs_per_session: int = Field(5, description="Maximum job descriptions per session")
    cors_origins: str = Field(
        "http://localhost:5173,http://localhost:3000",
        description="Comma-separated CORS origins"
    )
    log_level: str = Field("INFO", description="Logging level")
    environment: str = Field("development", description="Environment name")

    # ========================================================================
    # Derived Properties
    # ========================================================================
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        """Maximum file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra env vars like vite_api_url


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
