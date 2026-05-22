from typing import List

from core.job_service import job_service
from core.text_utils import extract_known_skills, score_label
from dto.schemas import ATSResult, JobRecommendation


class ATSService:
    def evaluate(self, cv_text: str, top_jobs: int = 8) -> ATSResult:
        jobs = job_service.recommend(cv_text, top_k=top_jobs)
        best_score = self._blend_score(jobs)
        label = score_label(best_score)
        matched = self._collect_terms(jobs, "matched_terms")
        missing = self._collect_terms(jobs, "missing_terms")
        explanation = self._explain(best_score, label, jobs)
        return ATSResult(
            score=best_score,
            label=label,
            explanation=explanation,
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

    def _explain(self, score: float, label: str, jobs: List[JobRecommendation]) -> str:
        if not jobs:
            return "No local jobs were available for comparison."
        top_title = jobs[0].title
        top_company = jobs[0].company
        if label == "Good Fit":
            return f"Strong local-market match. Your CV aligns best with {top_title} at {top_company}."
        if label == "Potential Fit":
            return f"Moderate match. Your CV has useful overlap with roles like {top_title}, but targeted keywords and clearer achievements would improve the score."
        return f"Low match against the current local jobs. The closest role found was {top_title}, but the CV needs stronger relevant skills and role-specific experience."


ats_service = ATSService()
