import re
from typing import Mapping


MASKED_TOKEN_RE = re.compile(r"(?<!\*)\*{3,}(?!\*)")
LETTER_RE = re.compile(r"[A-Za-z\u0600-\u06FF]")


def is_masked_job(row: Mapping[str, object]) -> bool:
    visible_fields = [
        _to_text(row.get("title")),
        _to_text(row.get("company")),
        _to_text(row.get("location")),
    ]
    title, company, _location = visible_fields
    if not _has_letters(title) or not _has_letters(company):
        return True
    return any(_looks_masked(value) for value in visible_fields)


def _looks_masked(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    compact = re.sub(r"\s+", "", text)
    if not compact:
        return False
    star_count = compact.count("*")
    if MASKED_TOKEN_RE.search(text) and star_count / len(compact) >= 0.2:
        return True
    tokens = [token for token in re.split(r"[\s,.;:/\\|()\-]+", text) if token]
    masked_tokens = [token for token in tokens if set(token) == {"*"} and len(token) >= 3]
    return len(masked_tokens) >= 2


def _has_letters(value: str) -> bool:
    return bool(LETTER_RE.search(value or ""))


def _to_text(value: object) -> str:
    return str(value or "").strip()
