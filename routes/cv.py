from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from core.cv_analysis_service import cv_analysis_service
from core.cv_parser import cv_parser
from dto.schemas import CVAnalyzeResponse, CVSummary

router = APIRouter(prefix="/cv", tags=["CV"])


@router.post("/analyze", response_model=CVAnalyzeResponse)
async def analyze_cv(
    file: UploadFile = File(...),
    user_id: str | None = Form(default=None),
    session_id: str | None = Form(default=None),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in cv_parser.SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Please upload a PDF, DOCX, or TXT CV.")

    try:
        result = cv_analysis_service.analyze_and_save(
            file_content=await file.read(),
            filename=file.filename or f"cv{suffix}",
            user_id=user_id,
            session_id=session_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return CVAnalyzeResponse(
        session_id=result["session_id"],
        user_id=result["user_id"],
        filename=result["filename"],
        summary=CVSummary(**result["summary"]),
        ats=result["ats"],
        improvement_suggestions=result["improvement_suggestions"],
    )
