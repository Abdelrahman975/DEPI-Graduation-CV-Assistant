import re
from typing import List

from core.job_service import job_service
from core.text_utils import extract_email, extract_known_skills, extract_phone, score_label
from dto.schemas import ATSResult, JobRecommendation


class ATSService:
    def evaluate(self, cv_text: str, top_jobs: int = 8) -> ATSResult:
        jobs = job_service.recommend(cv_text, top_k=top_jobs)
        breakdown = self._score_breakdown(cv_text, jobs)
        final_score = self._final_score(breakdown)
        label = score_label(final_score)
        matched = self._collect_terms(jobs, "matched_terms")
        missing = self._collect_terms(jobs, "missing_terms")
        explanation = self._explain(final_score, label, jobs, breakdown)
        return ATSResult(
            score=final_score,
            label=label,
            explanation=explanation,
            score_breakdown=breakdown,
            matched_skills=matched,
            missing_skills=missing,
            top_jobs=jobs,
        )

    def _blend_score(self, jobs: List[JobRecommendation]) -> float:
        if not jobs:
            return 0.0
        scores = [job.match_score for job in jobs[:5]]
        best = max(scores)
        average = sum(scores) / len(scores)
        return round((0.7 * best) + (0.3 * average), 2)

    def _score_breakdown(self, cv_text: str, jobs: List[JobRecommendation]) -> dict[str, float]:
        return {
            "job_alignment": self._job_alignment_score(jobs),
            "skills_coverage": self._skills_coverage_score(cv_text),
            "cv_structure": self._structure_score(cv_text),
            "impact_evidence": self._impact_score(cv_text),
        }

    def _final_score(self, breakdown: dict[str, float]) -> float:
        weights = {
            "job_alignment": 0.40,
            "skills_coverage": 0.30,
            "cv_structure": 0.20,
            "impact_evidence": 0.10,
        }
        score = sum(breakdown[key] * weight for key, weight in weights.items())
        return round(max(0.0, min(100.0, score)), 2)

    def _job_alignment_score(self, jobs: List[JobRecommendation]) -> float:
        raw = self._blend_score(jobs)
        if raw <= 0:
            return 0.0
        # Local retrieval scores are conservative, so map them onto an ATS-style 0-100 component.
        return round(max(0.0, min(100.0, 15 + raw * 2.15)), 2)

    def _skills_coverage_score(self, cv_text: str) -> float:
        skills = extract_known_skills(cv_text)
        count_score = min(70.0, len(skills) * 5.0)
        grouped_bonus = 0.0
        lowered = cv_text.lower()
        groups = [
            ["python", "java", "javascript", "sql"],
            ["machine learning", "deep learning", "data science", "business analysis", "devops"],
            ["business analyst", "requirements analysis", "gap analysis", "sdlc", "uat"],
            ["docker", "kubernetes", "aws", "azure", "gcp", "linux"],
            ["fastapi", "flask", "django", "react", "api"],
            ["postgresql", "mysql", "mongodb", "redis"],
        ]
        for group in groups:
            if any(skill in lowered for skill in group):
                grouped_bonus += 6.0
        return round(min(100.0, count_score + grouped_bonus), 2)

    def _structure_score(self, cv_text: str) -> float:
        lowered = cv_text.lower()
        score = 0.0
        if extract_email(cv_text):
            score += 10
        if extract_phone(cv_text):
            score += 10
        sections = {
            "summary": ["summary", "profile", "objective"],
            "experience": ["experience", "employment", "work history"],
            "education": ["education", "degree", "university"],
            "skills": ["skills", "technical skills", "tech stack"],
            "projects": ["projects", "portfolio"],
            "certifications": ["certifications", "certificates", "courses"],
        }
        score += sum(10 for aliases in sections.values() if any(alias in lowered for alias in aliases))
        words = re.findall(r"[A-Za-z][A-Za-z+#.\-]{1,}", cv_text)
        if len(words) >= 350:
            score += 10
        if len(words) >= 650:
            score += 10
        return round(min(100.0, score), 2)

    def _impact_score(self, cv_text: str) -> float:
        lowered = cv_text.lower()
        metrics = len(re.findall(r"(?:\d+(?:\.\d+)?\s?%|\d{2,}\+?|\$\s?\d+)", cv_text))
        action_verbs = [
            "built", "developed", "designed", "deployed", "implemented", "improved",
            "optimized", "automated", "managed", "led", "created", "delivered",
            "analyzed", "reduced", "increased", "processed", "integrated",
        ]
        verb_hits = sum(1 for verb in action_verbs if re.search(rf"\b{verb}\b", lowered))
        return round(min(100.0, metrics * 8.0 + verb_hits * 5.0), 2)

    def _collect_terms(self, jobs: List[JobRecommendation], attr: str) -> List[str]:
        seen = set()
        values = []
        for job in jobs[:5]:
            for term in getattr(job, attr):
                key = term.lower()
                if key not in seen:
                    seen.add(key)
                    values.append(term)
        return values[:15]

    def _explain(self, score: float, label: str, jobs: List[JobRecommendation], breakdown: dict[str, float]) -> str:
        if not jobs:
            return "No local jobs were available for comparison."
        top_title = jobs[0].title
        top_company = jobs[0].company
        parts = (
            f"job alignment {breakdown['job_alignment']:.0f}, "
            f"skills coverage {breakdown['skills_coverage']:.0f}, "
            f"CV structure {breakdown['cv_structure']:.0f}, "
            f"impact evidence {breakdown['impact_evidence']:.0f}"
        )
        if label == "Good Fit":
            return f"Strong ATS profile for the current local jobs. Closest match: {top_title} at {top_company}. Breakdown: {parts}."
        if label == "Potential Fit":
            return f"Moderate ATS profile. Closest match: {top_title} at {top_company}. Improve targeted keywords and measurable achievements. Breakdown: {parts}."
        return f"Low ATS profile for the selected local jobs. Closest match: {top_title} at {top_company}. Breakdown: {parts}."


ats_service = ATSService()
