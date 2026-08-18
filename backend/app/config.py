# app/config.py
import sys
import logging
from pydantic_settings import BaseSettings
from pydantic import Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("medbot.config")


class Settings(BaseSettings):
    # --- API Keys ---
    groq_api_key: str = Field(..., alias="GROQ_API_KEY")
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    cohere_api_key: str = Field(..., alias="COHERE_API_KEY")
    pinecone_api_key: str = Field(..., alias="PINECONE_API_KEY")

    # --- Model routing ---
    grading_model: str = Field("google/gemma-4-26b-a4b-it:free", alias="GRADING_MODEL")
    generation_model: str = Field("llama-3.3-70b-versatile", alias="GENERATION_MODEL")
    verifier_model: str = Field("openai/gpt-oss-120b", alias="VERIFIER_MODEL")

    openrouter_base_url: str = Field("https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL")

    # --- Embeddings ---
    cohere_embed_model: str = Field("embed-english-v3.0", alias="COHERE_EMBED_MODEL")
    embed_dimension: int = 1024

    # --- Reranker ---
    cohere_rerank_model: str = Field("rerank-english-v3.0", alias="COHERE_RERANK_MODEL")
    rerank_top_n: int = 5

    # --- Pinecone ---
    pinecone_index_name: str = Field("medbot-index", alias="PINECONE_INDEX_NAME")
    pinecone_cloud: str = Field("aws", alias="PINECONE_CLOUD")
    pinecone_region: str = Field("us-east-1", alias="PINECONE_REGION")

    # --- Retrieval ---
    retrieval_top_k: int = 15  # candidates pulled before rerank/grading

    # --- Grading thresholds (CRAG) ---
    grade_upper_threshold: float = 0.7   # >= this => CORRECT
    grade_lower_threshold: float = 0.3   # < this => INCORRECT
    min_strong_chunks_for_correct: int = 1  # require 1+ strong chunks
    context_inclusion_threshold: float = 0.5  # looser bar for what generation actually sees

    # --- Chunking (used by ingest.py) ---
    chunk_size: int = 900
    chunk_overlap: int = 150
    min_chunk_chars: int = 30  # drop near-empty chunks

    # --- App ---
    app_env: str = Field("development", alias="APP_ENV")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    
    # app/config.py — add these fields to Settings
    tavily_api_key: str = Field(..., alias="TAVILY_API_KEY")
    tavily_max_results: int = 4

    mongodb_uri: str = Field(..., alias="MONGODB_URI")
    mongodb_db_name: str = Field("medbot", alias="MONGODB_DB_NAME")

    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(10080, alias="JWT_EXPIRE_MINUTES")  # 7 days

    guest_question_limit: int = Field(10, alias="GUEST_QUESTION_LIMIT")

    google_client_id: str = Field("", alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field("", alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field("http://localhost:8000/auth/google/callback", alias="GOOGLE_REDIRECT_URI")

    frontend_url: str = Field("http://localhost:3000", alias="FRONTEND_URL")

    admin_password: str = Field(..., alias="ADMIN_PASSWORD")

    session_message_limit: int = Field(20, alias="SESSION_MESSAGE_LIMIT")

    class Config:
        env_file = ".env"
        populate_by_name = True


def load_settings() -> Settings:
    try:
        s = Settings()
        logger.info("Settings loaded successfully.")
        return s
    except Exception as e:
        logger.error(f"Missing or invalid environment variables: {e}")
        sys.exit(1)


settings = load_settings()