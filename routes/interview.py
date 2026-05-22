from fastapi import APIRouter, HTTPException

from core.chat_service.gemini_service import gemini_service
from core.session_store import session_store
from core.vector_store import vector_store
from dto.schemas import InterviewQuestion, InterviewQuestionRequest, InterviewQuestionResponse

router = APIRouter(prefix="/interview", tags=["Interview"])


@router.post("/questions", response_model=InterviewQuestionResponse)
async def interview_questions(request: InterviewQuestionRequest):
    try:
        session = session_store.require(request.session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    cv_text = session.get("cv_text", "")
    retrieved = vector_store.search_interview_questions(
        cv_text, top_k=request.count, difficulty=request.difficulty
    )
    questions: list[InterviewQuestion] = []
    seen = set()
    for item in retrieved:
        question = item.get("document") or item.get("question")
        if not question or question.lower() in seen:
            continue
        seen.add(question.lower())
        questions.append(
            InterviewQuestion(
                question=question,
                category=item.get("category"),
                difficulty=item.get("difficulty"),
                source="retrieved",
            )
        )

    if len(questions) < request.count:
        generated = gemini_service.generate_interview_questions(
            cv_text=cv_text,
            retrieved_questions=retrieved,
            count=request.count - len(questions),
            difficulty=request.difficulty,
        )
        for question in generated:
            if question.lower() not in seen:
                seen.add(question.lower())
                questions.append(InterviewQuestion(question=question, difficulty=request.difficulty, source="generated"))
            if len(questions) >= request.count:
                break

    return InterviewQuestionResponse(session_id=request.session_id, questions=questions[: request.count])
