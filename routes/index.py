from fastapi import APIRouter, HTTPException

from core.vector_store import vector_store
from dto.schemas import IndexBuildResponse

router = APIRouter(prefix="/index", tags=["Index"])


@router.post("/rebuild", response_model=IndexBuildResponse)
async def rebuild_index():
    try:
        counts = vector_store.build_all(reset=True)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    message = "Local Chroma index rebuilt."
    if not vector_store.chroma_available:
        message = f"Local data loaded. Chroma unavailable, lexical fallback search is active: {vector_store.init_error}"
    return IndexBuildResponse(message=message, collections=counts)
