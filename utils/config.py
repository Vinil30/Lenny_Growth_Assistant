import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


def _database_url() -> str:
    raw = os.getenv("DATABASE_URL", "sqlite:///data/app.db")
    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql+psycopg://", 1)
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+psycopg://", 1)
    return raw


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    secret_key: str = os.getenv("SECRET_KEY", "dev-only")
    database_url: str = _database_url()
    llm_provider: str = os.getenv("LLM_PROVIDER", "ollama").lower()
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_base_url: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    groq_fast_model: str = os.getenv("GROQ_FAST_MODEL", "openai/gpt-oss-120b")
    groq_main_model: str = os.getenv("GROQ_MAIN_MODEL", "openai/gpt-oss-120b")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_fast_model: str = os.getenv("OLLAMA_FAST_MODEL", "llama3.2:3b")
    ollama_main_model: str = os.getenv("OLLAMA_MAIN_MODEL", "llama3.1:8b")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "local-hash-384")
    transcript_dir: str = os.getenv("TRANSCRIPT_DIR", "podcasts")
    rag_data_dir: str = os.getenv("RAG_DATA_DIR", "data/faiss")
    top_k_dense: int = _int("TOP_K_DENSE", 8)
    top_k_bm25: int = _int("TOP_K_BM25", 8)
    max_context_chars: int = _int("MAX_CONTEXT_CHARS", 12000)
    request_timeout_seconds: int = _int("REQUEST_TIMEOUT_SECONDS", 60)
    auto_create_db: bool = _bool("AUTO_CREATE_DB", False)
    db_connect_timeout_seconds: int = _int("DB_CONNECT_TIMEOUT_SECONDS", 3)


settings = Settings()
