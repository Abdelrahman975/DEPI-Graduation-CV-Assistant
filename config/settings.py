from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "CV Assistant RAG"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_V1_STR: str = "/api/v1"

    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CONN_STR: Optional[str] = None
    SESSION_BACKEND: str = "auto"

    PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
    DATA_DIR: Path = PROJECT_ROOT / "data"
    CLEAN_JOBS_PATH: Path = DATA_DIR / "clean_jobs.csv"
    INTERVIEW_QUESTIONS_PATH: Path = DATA_DIR / "new" / "coding_interview_question_bank.csv"
    RESUME_SCREENING_PATH: Path = DATA_DIR / "new" / "AI_Resume_Screening.csv"
    ATS_TRAIN_PATH: Path = DATA_DIR / "resume-ats-score-v1-en" / "train.csv"
    ATS_VALIDATION_PATH: Path = DATA_DIR / "resume-ats-score-v1-en" / "validation.csv"

    STORAGE_DIR: Path = PROJECT_ROOT / "storage"
    CHROMA_DIR: Path = STORAGE_DIR / "chroma"
    UPLOAD_DIR: Path = STORAGE_DIR / "uploads"
    SESSION_DIR: Path = STORAGE_DIR / "sessions"

    MAX_UPLOAD_MB: int = 10
    DEFAULT_TOP_JOBS: int = 8
    DEFAULT_INTERVIEW_COUNT: int = 8

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "yes", "on", "debug", "dev", "development"}:
                return True
            if lowered in {"0", "false", "no", "off", "release", "prod", "production"}:
                return False
        return value

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
