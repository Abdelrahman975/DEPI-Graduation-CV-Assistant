from typing import List

from config.settings import settings
from core.text_utils import matched_terms, missing_terms
from core.vector_store import vector_store
from dto.schemas import JobRecommendation


class JobService:
    def recommend(self, cv_text: str, top_k: int | None = None) -> List[JobRecommendation]:
        top_k = top_k or settings.DEFAULT_TOP_JOBS
        results = vector_store.search_jobs(cv_text, top_k=top_k)
        recommendations = []
        for idx, result in enumerate(results, 1):
            document = result.get("document", "")
            score = result.get("_distance_score", 0.0)
            recommendations.append(
                JobRecommendation(
                    id=str(result.get("id") or idx),
                    title=result.get("title", "Untitled Job"),
                    company=result.get("company", "Unknown Company"),
                    location=result.get("location", "Unknown Location"),
                    link=result.get("link") or None,
                    source=result.get("source") or None,
                    date_posted=result.get("date_posted") or None,
                    match_score=round(float(score), 2),
                    matched_terms=matched_terms(cv_text, document),
                    missing_terms=missing_terms(cv_text, document),
                    description_preview=document[:420] if document else None,
                )
            )
        return recommendations


job_service = JobService()
