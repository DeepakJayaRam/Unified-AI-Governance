"""Environment-only deployment configuration; no built-in credentials."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./uag.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    execution_mode: str = os.getenv("EXECUTION_MODE", "local")
    cors_origins: tuple[str, ...] = tuple(os.getenv("CORS_ORIGINS", "http://127.0.0.1:3100,http://localhost:3100").split(","))
    session_hours: int = int(os.getenv("SESSION_HOURS", "8"))
    signing_key_path: str = os.getenv("SIGNING_KEY_PATH", "")
    secure_environment: bool = os.getenv("ENVIRONMENT", "development") == "production"

    def __post_init__(self):
        if self.execution_mode not in {"local", "redis"}:
            raise ValueError("EXECUTION_MODE must be local or redis")
        if not 1 <= self.session_hours <= 24:
            raise ValueError("SESSION_HOURS must be between 1 and 24")
        if any(origin == "*" for origin in self.cors_origins):
            raise ValueError("CORS requires explicit origins")
        if self.secure_environment:
            if not self.database_url.startswith("postgresql") or self.execution_mode != "redis":
                raise ValueError("Production requires PostgreSQL and Redis execution mode")
            if any(not origin.startswith("https://") for origin in self.cors_origins):
                raise ValueError("Production CORS origins must use HTTPS")


settings = Settings()
