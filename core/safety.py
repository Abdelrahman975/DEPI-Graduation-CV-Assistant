import uuid
from pathlib import Path


def safe_identifier(value: str | None, fallback_prefix: str = "id") -> str:
    cleaned = "".join(ch for ch in str(value or "") if ch.isalnum() or ch in "-_")
    return cleaned or f"{fallback_prefix}-{uuid.uuid4()}"


def safe_filename(filename: str | None, default: str = "cv.txt") -> str:
    name = Path(filename or default).name
    cleaned = "".join(ch if ch.isalnum() or ch in "._- " else "_" for ch in name).strip()
    return cleaned or default
