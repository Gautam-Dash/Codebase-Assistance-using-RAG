"""Configuration management for the RAG system."""
import os
from pathlib import Path
from typing import Optional
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(env_file=".env", case_sensitive=False)

    # LLM Configuration
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    llm_model: str = Field(default="gpt-4", env="LLM_MODEL")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")

    # System Configuration
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    max_workers: int = Field(default=4, env="MAX_WORKERS")
    batch_size: int = Field(default=32, env="BATCH_SIZE")

    # Retrieval Configuration
    faiss_index_path: Path = Field(default=Path("./data/faiss_index"), env="FAISS_INDEX_PATH")
    chunk_size: int = Field(default=512, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, env="CHUNK_OVERLAP")
    top_k_retrieval: int = Field(default=10, env="TOP_K_RETRIEVAL")
    top_k_ranking: int = Field(default=5, env="TOP_K_RANKING")

    # Cross-encoder Configuration
    reranker_model: str = Field(
        default="cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
        env="RERANKER_MODEL"
    )
    reranker_threshold: float = Field(default=0.5, env="RERANKER_THRESHOLD")

    # Repository Configuration
    repo_path: Path = Field(default=Path("./repo_to_index"), env="REPO_PATH")
    include_extensions: str = Field(
        default=".py,.js,.ts,.java,.cpp,.c,.go,.rs,.rb,.php",
        env="INCLUDE_EXTENSIONS"
    )
    exclude_patterns: str = Field(
        default="__pycache__,node_modules,.git,.env",
        env="EXCLUDE_PATTERNS"
    )

    # Redis Configuration
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")

    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    streamlit_port: int = Field(default=8501, env="STREAMLIT_PORT")

    @property
    def included_extensions(self) -> list[str]:
        """Get list of included file extensions."""
        return [ext.strip() for ext in self.include_extensions.split(",")]

    @property
    def excluded_patterns_list(self) -> list[str]:
        """Get list of excluded directory patterns."""
        return [pattern.strip() for pattern in self.exclude_patterns.split(",")]


# Global settings instance
settings = Settings()
