from pathlib import Path
from typing import Dict, List

from core.text_utils import (
    extract_email,
    extract_known_skills,
    extract_phone,
    normalize_text,
    top_keywords,
)


class CVParser:
    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

    def parse(self, file_path: Path) -> str:
        suffix = file_path.suffix.lower()
        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise ValueError("Unsupported CV format. Please upload PDF, DOCX, or TXT.")

        if suffix == ".txt":
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        elif suffix == ".pdf":
            text = self._parse_pdf(file_path)
        else:
            text = self._parse_docx(file_path)

        text = normalize_text(text)
        if len(text) < 80:
            raise ValueError(
                "Could not extract enough text from this CV. If it is scanned, please upload a text-based PDF, DOCX, or TXT file."
            )
        return text

    def summarize(self, text: str) -> Dict:
        skills = extract_known_skills(text)
        keywords = top_keywords(text, limit=20)
        likely_roles = self._infer_roles(text, keywords)
        return {
            "name": self._guess_name(text),
            "email": extract_email(text),
            "phone": extract_phone(text),
            "skills": skills[:20],
            "likely_roles": likely_roles,
            "years_experience_hint": self._experience_hint(text),
            "text_length": len(text),
        }

    def _parse_pdf(self, file_path: Path) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("PDF parsing requires pypdf. Install project requirements.") from exc

        reader = PdfReader(str(file_path))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)

    def _parse_docx(self, file_path: Path) -> str:
        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError("DOCX parsing requires python-docx. Install project requirements.") from exc

        document = Document(str(file_path))
        paragraphs = [p.text for p in document.paragraphs]
        table_cells: List[str] = []
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    table_cells.append(cell.text)
        return "\n".join([*paragraphs, *table_cells])

    def _guess_name(self, text: str) -> str | None:
        for line in text.splitlines()[:8]:
            line = normalize_text(line)
            if 2 <= len(line.split()) <= 4 and "@" not in line and not any(ch.isdigit() for ch in line):
                return line
        return None

    def _infer_roles(self, text: str, keywords: List[str]) -> List[str]:
        lowered = text.lower()
        roles = []
        role_rules = [
            ("Data Analyst", ["data analyst", "excel", "tableau", "power bi", "sql"]),
            ("Data Scientist", ["data scientist", "machine learning", "statistics", "pandas"]),
            ("Machine Learning Engineer", ["machine learning engineer", "deep learning", "tensorflow", "pytorch"]),
            ("Data Engineer", ["data engineer", "etl", "spark", "pipeline"]),
            ("Software Engineer", ["software engineer", "backend", "frontend", "api", "react"]),
            ("Cybersecurity Analyst", ["cybersecurity", "security analyst", "linux", "network security"]),
        ]
        for role, hints in role_rules:
            if any(hint in lowered for hint in hints) or any(hint in keywords for hint in hints):
                roles.append(role)
        return roles[:4] or ["General Technology Candidate"]

    def _experience_hint(self, text: str) -> str | None:
        import re

        match = re.search(r"(\d{1,2})\+?\s*(?:years|yrs)\s+(?:of\s+)?experience", text, re.I)
        return match.group(0) if match else None


cv_parser = CVParser()
