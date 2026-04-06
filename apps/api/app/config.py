import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# Tu dong nap bien moi truong tu file .env o root repo de tranh sai khac giua terminal va app.
REPO_ROOT = Path(__file__).resolve().parents[3]
# Dung override=True de gia tri trong .env duoc uu tien, tranh bi bien cu trong shell de.
load_dotenv(REPO_ROOT / ".env", override=True)


@dataclass
class Settings:
    # Cau hinh chinh cho API backend (application settings).
    app_name: str = os.getenv("API_APP_NAME", "Travel Chat API")
    app_env: str = os.getenv("API_ENV", "dev")
    # File SQLite mac dinh nam trong thu muc hien tai khi chay uvicorn tu `apps/api` (working-directory relative DB).
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")

    llm_provider: str = os.getenv("DEFAULT_PROVIDER", "mock")
    llm_model: str = os.getenv("DEFAULT_LLM_MODEL", "gpt-4o-mini")
    llm_api_key: str | None = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")

    react_max_steps_default: int = int(os.getenv("REACT_MAX_STEPS_DEFAULT", "8"))
    enable_tool_invocation_table: bool = os.getenv(
        "ENABLE_TOOL_INVOCATION_TABLE", "false"
    ).lower() in {"1", "true", "yes", "on"}


settings = Settings()
