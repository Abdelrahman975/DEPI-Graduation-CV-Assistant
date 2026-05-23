import re
from collections import Counter
from typing import Iterable, List


COMMON_SKILLS = {
    "python", "sql", "excel", "tableau", "power bi", "machine learning",
    "deep learning", "nlp", "tensorflow", "pytorch", "scikit-learn",
    "pandas", "numpy", "matplotlib", "seaborn", "statistics",
    "data analysis", "data visualization", "data engineering", "etl",
    "spark", "hadoop", "aws", "azure", "gcp", "docker", "kubernetes",
    "linux", "git", "java", "javascript", "typescript", "react",
    "node", "django", "flask", "fastapi", "api", "mongodb",
    "postgresql", "mysql", "cybersecurity", "network security",
    "data science", "communication", "leadership", "agile", "scrum",
    "rag", "llm", "generative ai", "langchain", "vector database",
    "computer vision", "opencv", "hugging face", "transformers",
    "mlops", "ci/cd", "github actions", "terraform", "ansible",
    "jenkins", "nginx", "prometheus", "grafana", "redis",
    "business analysis", "requirements gathering", "stakeholder management",
    "process mapping", "user stories", "jira", "confluence", "oracle",
    "salesforce", "sap", "looker", "qlik", "spss", "sas",
    "business analyst", "data analyst", "requirements analysis", "gap analysis",
    "sdlc", "waterfall", "rup", "uml", "ms visio", "uat",
}

STOP_WORDS = {
    "the", "and", "for", "with", "that", "this", "from", "are", "you",
    "your", "will", "our", "has", "have", "not", "can", "all", "any",
    "job", "work", "team", "role", "skills", "experience", "years",
    "using", "use", "show", "more", "less", "about", "into", "their",
    "they", "them", "its", "such", "within", "across", "based",
    "developer", "development", "candidate", "required", "preferred",
    "responsibilities", "qualifications", "including", "strong", "excellent",
    "ability", "knowledge", "tools", "systems", "platform", "modern",
    "help", "through", "both", "join", "looking", "seeking", "current",
    "what", "build", "opportunity", "working", "include", "includes",
    "daily", "various", "new", "support", "creating", "created",
}

GENERIC_MISSING_TERMS = {
    "Ability", "Both", "Candidate", "Current", "Developer", "Development",
    "Build", "Help", "Join", "Knowledge", "Modern", "Opportunity", "Platform", "Preferred",
    "Qualifications", "Required", "Responsibilities", "Strong", "Systems",
    "Through", "Tools", "What", "Working", "Work", "Team", "Role", "Job",
}


def normalize_text(text: str) -> str:
    text = (text or "").replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_email(text: str) -> str | None:
    match = re.search(r"[\w.\-+]+@[\w.\-]+\.\w+", text or "")
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    match = re.search(r"(?:\+?\d[\d\s().-]{7,}\d)", text or "")
    return match.group(0).strip() if match else None


def extract_known_skills(text: str) -> List[str]:
    lowered = (text or "").lower()
    found = []
    for skill in sorted(COMMON_SKILLS, key=len, reverse=True):
        if re.search(rf"(?<![a-z0-9]){re.escape(skill)}(?![a-z0-9])", lowered):
            found.append(skill.title())
    return dedupe_keep_order(found)


def top_keywords(text: str, limit: int = 30) -> List[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z+#.\-]{2,}", (text or "").lower())
    words = [w.strip(".-") for w in words if w not in STOP_WORDS and len(w) > 2]
    return [word for word, _ in Counter(words).most_common(limit)]


def lexical_score(query: str, document: str) -> float:
    query_terms = set(top_keywords(query, limit=60))
    doc_terms = set(top_keywords(document, limit=120))
    if not query_terms or not doc_terms:
        return 0.0
    overlap = query_terms & doc_terms
    recall = len(overlap) / max(len(query_terms), 1)
    precision = len(overlap) / max(len(doc_terms), 1)
    return round((0.75 * recall + 0.25 * precision) * 100, 2)


def matched_terms(left: str, right: str, limit: int = 12) -> List[str]:
    known = [s for s in extract_known_skills(left) if s.lower() in (right or "").lower()]
    keyword_matches = [kw.title() for kw in top_keywords(left, 40) if kw in top_keywords(right, 120)]
    return dedupe_keep_order([*known, *keyword_matches])[:limit]


def missing_terms(cv_text: str, job_text: str, limit: int = 12) -> List[str]:
    cv_lower = (cv_text or "").lower()
    job_skills = extract_known_skills(job_text)
    missing = [skill for skill in job_skills if skill.lower() not in cv_lower and skill not in GENERIC_MISSING_TERMS]
    if len(missing) < limit:
        for kw in top_keywords(job_text, 60):
            titled = kw.title()
            if kw not in cv_lower and titled not in missing and titled not in GENERIC_MISSING_TERMS:
                missing.append(titled)
            if len(missing) >= limit:
                break
    return missing[:limit]


def dedupe_keep_order(items: Iterable[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        clean = normalize_text(str(item))
        key = clean.lower()
        if clean and key not in seen:
            seen.add(key)
            result.append(clean)
    return result


def score_label(score: float) -> str:
    if score >= 70:
        return "Good Fit"
    if score >= 40:
        return "Potential Fit"
    return "No Fit"
