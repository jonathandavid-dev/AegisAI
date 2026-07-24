from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Application Config
    APP_NAME: str = "AegisAI – Enterprise Agentic Knowledge Platform"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # Upload Settings
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: list[str] = ["pdf", "docx", "txt"]

    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    # JWT & Security Settings
    # Default is provided to ensure local scripts start up cleanly; overridden in compose
    SECRET_KEY: str = "94c1e48bc785536b3df58b548b2611681a95e0c5dbf5038c92f98f98a287a935"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"
    
    JWT_SECRET: str = "94c1e48bc785536b3df58b548b2611681a95e0c5dbf5038c92f98f98a287a935"
    JWT_ACCESS_TOKEN_MINUTES: int = 15
    JWT_REFRESH_TOKEN_DAYS: int = 7
    PASSWORD_HASH_ALGORITHM: str = "bcrypt"
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCK_DURATION: int = 15
    
    DEFAULT_WORKSPACE_NAME: str = "Personal Workspace"
    INVITATION_EXPIRY_DAYS: int = 7
    MAX_WORKSPACES_PER_ORGANIZATION: int = 10
    MAX_MEMBERS_PER_WORKSPACE: int = 50
    
    # Database Settings
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "aegis_secure_db_pass_2026"
    POSTGRES_DB: str = "aegis_ai"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        # Useful for migrations with Alembic which defaults to sync connection
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis Settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Celery Settings
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"
    CELERY_TASK_ALWAYS_EAGER: bool = False

    # LLM Settings
    LLM_PROVIDER: str = "mock"
    LLM_MODEL: str = "mock-model"
    LLM_API_KEY: str | None = None
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 1024
    LLM_TIMEOUT: float = 30.0

    # RAG Settings
    MAX_CONTEXT_CHUNKS: int = 5
    MAX_CONTEXT_TOKENS: int = 2048

    # Phase 3.3 Additions
    ENABLE_STREAMING: bool = True
    CACHE_TTL_SECONDS: int = 3600
    ENABLE_PROMETHEUS: bool = True
    ENABLE_OPENTELEMETRY: bool = True
    MAX_CACHE_SIZE: int = 1000
    STREAM_HEARTBEAT_SECONDS: int = 15

    # Phase 3.4 Additions
    ENABLE_EVALUATION: bool = True
    DEFAULT_TOP_K: int = 5
    QUALITY_SCORE_THRESHOLD: float = 0.70
    ENABLE_GUARDRAILS: bool = False
    MAX_HALLUCINATION_SCORE: float = 0.30

settings = Settings()


