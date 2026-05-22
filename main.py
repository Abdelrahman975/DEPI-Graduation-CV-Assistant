from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from config.settings import settings
from routes import chat, conversations, cv, index, interview, jobs

app = FastAPI(
    title=settings.APP_NAME,
    description="Local CV ATS, interview, job recommendation, and RAG chatbot assistant.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cv.router, prefix=settings.API_V1_STR)
app.include_router(conversations.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(jobs.router, prefix=settings.API_V1_STR)
app.include_router(interview.router, prefix=settings.API_V1_STR)
app.include_router(index.router, prefix=settings.API_V1_STR)


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
    return {"status": "healthy", "app": settings.APP_NAME}


@app.get("/app")
async def app_ui():
    return FileResponse(str(settings.PROJECT_ROOT / "static" / "index.html"))
