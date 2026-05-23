from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config.settings import settings
from core.chat_service.gemini_service import gemini_service
from core.session_store import session_store
from core.vector_store import vector_store
from logging_config import configure_logging
from routes import chat, conversations, cv

configure_logging()

app = FastAPI(
    title=settings.APP_NAME,
    description="Local CV ATS, interview, job recommendation, and RAG chatbot assistant.",
    version="1.0.0",
)

cors_origins = settings.cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials="*" not in cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cv.router, prefix=settings.API_V1_STR)
app.include_router(conversations.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)

app.mount("/static", StaticFiles(directory=str(settings.PROJECT_ROOT / "static")), name="static")


@app.get("/")
async def root():
    return {
        "message": "Welcome to CV Assistant RAG",
        "docs": "/docs",
        "ui": "/app",
        "health": "/health",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "session_backend": session_store.backend,
        "session_backend_error": session_store.db_error,
        "vector_store": {
            "chroma_available": vector_store.chroma_available,
            "init_error": vector_store.init_error,
        },
        "model": {
            "provider": "gemini",
            "configured": gemini_service.available,
            "model": gemini_service.model_name,
            "init_error": gemini_service.init_error,
        },
    }


@app.get("/config")
async def public_config():
    return {
        "app_name": settings.APP_NAME,
        "debug": settings.DEBUG,
        "api_version": settings.API_V1_STR,
        "limits": {
            "max_upload_mb": settings.MAX_UPLOAD_MB,
            "default_top_jobs": settings.DEFAULT_TOP_JOBS,
        },
        "features": {
            "sse_streaming": "/api/v1/chat/stream",
            "cv_analysis": "/api/v1/cv/analyze",
        },
        "storage": {
            "session_backend": session_store.backend,
            "chroma_available": vector_store.chroma_available,
        },
    }


@app.get("/app")
async def app_ui():
    return FileResponse(str(settings.PROJECT_ROOT / "static" / "index.html"))
