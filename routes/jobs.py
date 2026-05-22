from fastapi import APIRouter, HTTPException

from config.settings import settings
from core.job_service import job_service
from core.session_store import session_store
from dto.schemas import JobRecommendation

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/recommendations/{session_id}", response_model=list[JobRecommendation])
async def recommendations(session_id: str, top_k: int = settings.DEFAULT_TOP_JOBS):
    try:
        session = session_store.require(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return job_service.recommend(session.get("cv_text", ""), top_k=top_k)
