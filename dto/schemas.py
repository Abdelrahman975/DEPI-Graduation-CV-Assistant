from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class CVSummary(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    likely_roles: List[str] = Field(default_factory=list)
    years_experience_hint: Optional[str] = None
    text_length: int = 0


class JobRecommendation(BaseModel):
    id: str
    title: str
    company: str
    location: str
    link: Optional[str] = None
    source: Optional[str] = None
    date_posted: Optional[str] = None
    match_score: float = 0.0
    matched_terms: List[str] = Field(default_factory=list)
    missing_terms: List[str] = Field(default_factory=list)
    description_preview: Optional[str] = None


class ATSResult(BaseModel):
    score: float
    label: Literal["No Fit", "Potential Fit", "Good Fit"]
    explanation: str
    score_breakdown: Dict[str, float] = Field(default_factory=dict)
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    top_jobs: List[JobRecommendation] = Field(default_factory=list)


class CVAnalyzeResponse(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    filename: str
    summary: CVSummary
    ats: ATSResult
    improvement_suggestions: List[str] = Field(default_factory=list)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    session_id: str
    message: str
    top_k: int = Field(default=5, ge=1, le=15)


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)


class UserCreateRequest(BaseModel):
    user_id: Optional[str] = None
    display_name: Optional[str] = None


class UserResponse(BaseModel):
    user_id: str
    display_name: str
    created_at: str


class ChatCreateRequest(BaseModel):
    user_id: str
    title: Optional[str] = None


class ChatSummary(BaseModel):
    session_id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    has_cv: bool = False
    filename: Optional[str] = None
    messages_count: int = 0


class ChatSessionResponse(ChatSummary):
    messages: List[ChatMessage] = Field(default_factory=list)
    summary: Optional[CVSummary] = None
    ats: Optional[ATSResult] = None
    improvement_suggestions: List[str] = Field(default_factory=list)


class InterviewQuestionRequest(BaseModel):
    session_id: str
    difficulty: Optional[Literal["Easy", "Medium", "Hard"]] = None
    count: int = Field(default=8, ge=1, le=20)


class InterviewQuestion(BaseModel):
    question: str
    category: Optional[str] = None
    difficulty: Optional[str] = None
    source: Literal["retrieved", "generated"] = "retrieved"


class InterviewQuestionResponse(BaseModel):
    session_id: str
    questions: List[InterviewQuestion]


class IndexBuildResponse(BaseModel):
    message: str
    collections: Dict[str, int]
