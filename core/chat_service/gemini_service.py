from typing import Dict, Iterable, List, Optional

from config.settings import settings
from prompts.cv_assistant import CV_ASSISTANT_SYSTEM_PROMPT, CV_IMPROVEMENT_PROMPT


class GeminiService:
    def __init__(self):
        self.genai = None
        self.model = None
        self.model_name = None
        self.model_candidates = self._model_candidates(settings.GEMINI_MODEL)
        self._models = {}
        self.init_error = None
        if not settings.GOOGLE_API_KEY:
            self.init_error = "GOOGLE_API_KEY is not configured."
            return
        try:
            import google.generativeai as genai

            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.genai = genai
            self.model_name = self.model_candidates[0]
            self.model = self._get_model(self.model_name)
        except Exception as exc:
            self.init_error = str(exc)

    @property
    def available(self) -> bool:
        return self.model is not None

    def suggest_cv_improvements(self, cv_text: str, ats_payload: Dict) -> List[str]:
        if not self.available:
            return self._fallback_suggestions(ats_payload)
        prompt = f"""
{CV_ASSISTANT_SYSTEM_PROMPT}

{CV_IMPROVEMENT_PROMPT}

ATS result:
{ats_payload}

CV text:
{cv_text[:12000]}

Return only a bullet list.
Use exactly this format for each item:
- **Short action title:** one clear practical recommendation.
Do not include an introduction or closing sentence.
"""
        text = self._generate(prompt)
        suggestions = self._lines_to_list(text)
        return suggestions or self._fallback_suggestions(ats_payload)

    def stream_chat(
        self,
        cv_text: str,
        user_message: str,
        retrieved_context: List[Dict],
        history: Optional[List[Dict]] = None,
    ) -> Iterable[str]:
        if not self.genai:
            yield from self._chunk_text(self._fallback_chat(user_message, retrieved_context))
            return

        prompt = self._build_chat_prompt(cv_text, user_message, retrieved_context, history)
        last_error = None
        for model_name in self.model_candidates:
            try:
                model = self._get_model(model_name)
                response = model.generate_content(prompt, stream=True)
                self.model = model
                self.model_name = model_name
                emitted = False
                for chunk in response:
                    text = getattr(chunk, "text", "") or ""
                    if text:
                        emitted = True
                        yield text
                if not emitted:
                    text = self._generate(prompt).strip() or self._fallback_chat(user_message, retrieved_context)
                    yield from self._chunk_text(text)
                return
            except Exception as exc:
                last_error = exc
                continue
        self.init_error = str(last_error) if last_error else "Gemini streaming failed."
        yield from self._chunk_text(self._fallback_chat(user_message, retrieved_context))

    def _generate(self, prompt: str) -> str:
        if not self.genai:
            return ""
        last_error = None
        for model_name in self.model_candidates:
            try:
                model = self._get_model(model_name)
                response = model.generate_content(prompt)
                self.model = model
                self.model_name = model_name
                return getattr(response, "text", "") or ""
            except Exception as exc:
                last_error = exc
                continue
        self.init_error = str(last_error) if last_error else "Gemini generation failed."
        return ""

    def _build_chat_prompt(
        self,
        cv_text: str,
        user_message: str,
        retrieved_context: List[Dict],
        history: Optional[List[Dict]] = None,
    ) -> str:
        context_text = "\n\n".join(
            f"Source {idx}: {item.get('title') or item.get('category') or item.get('kind', 'local data')}\n"
            f"{item.get('document', '')[:1800]}"
            for idx, item in enumerate(retrieved_context, 1)
        )
        history_text = "\n".join(
            f"{item.get('role', 'user')}: {item.get('content', '')[:1200]}"
            for item in (history or [])[-14:]
        )
        return f"""
{CV_ASSISTANT_SYSTEM_PROMPT}

Conversation memory:
{history_text or "No previous messages in this conversation."}

User CV:
{cv_text[:10000] if cv_text else "No CV uploaded in this conversation yet."}

Retrieved local context:
{context_text or "No retrieved local context."}

Current user message:
{user_message}

Instructions:
- Answer in the same language as the user's message when possible.
- Use the conversation memory to resolve references like "ده", "الوظيفة دي", "نفس الكلام", or follow-up questions.
- If a CV is attached or already uploaded, use it as the primary source.
- Use Markdown formatting for headings, bullets, tables, and code when helpful.
- Do not invent job links. Only mention links from retrieved local context.
"""

    def _chunk_text(self, text: str, size: int = 48) -> Iterable[str]:
        for start in range(0, len(text), size):
            yield text[start:start + size]

    def _get_model(self, model_name: str):
        if model_name not in self._models:
            self._models[model_name] = self.genai.GenerativeModel(model_name)
        return self._models[model_name]

    def _model_candidates(self, configured_model: str) -> List[str]:
        preferred = (configured_model or "gemini-2.5-flash-lite").strip().lower()
        candidates = [
            preferred,
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-flash-latest",
        ]
        seen = set()
        result = []
        for model in candidates:
            if model and model not in seen:
                seen.add(model)
                result.append(model)
        return result

    def _lines_to_list(self, text: str) -> List[str]:
        import re

        cleaned = []
        for line in (text or "").splitlines():
            line = line.strip()
            line = re.sub(r"^\s*(?:[-•*]|\d+[.)])\s+", "", line)
            if line and not self._is_non_action_line(line):
                cleaned.append(line)
        return cleaned

    def _is_non_action_line(self, line: str) -> bool:
        lowered = line.strip().lower().rstrip(":")
        prefixes = (
            "here are",
            "here is",
            "below are",
            "these are",
            "certainly",
            "of course",
        )
        endings = (
            "hope this helps",
            "let me know",
        )
        return lowered.startswith(prefixes) or any(ending in lowered for ending in endings)

    def _fallback_suggestions(self, ats_payload: Dict) -> List[str]:
        missing = ats_payload.get("missing_skills", [])[:6] if isinstance(ats_payload, dict) else []
        suggestions = [
            "Add a short professional summary that names your target role and strongest technical skills.",
            "Rewrite experience bullets with action verbs, business impact, and measurable results.",
            "Create a dedicated skills section using exact keywords from the strongest matching jobs.",
            "Keep formatting simple: clear section headers, consistent dates, and no complex tables for ATS parsing.",
        ]
        if missing:
            suggestions.append("Consider adding or strengthening these missing local-job keywords: " + ", ".join(missing) + ".")
        suggestions.append("Move the most relevant projects and achievements closer to the top of the CV.")
        return suggestions

    def _fallback_chat(self, user_message: str, retrieved_context: List[Dict]) -> str:
        if retrieved_context:
            top = retrieved_context[0]
            title = top.get("title") or top.get("category") or "the retrieved local data"
            return (
                "Gemini is not configured yet, so I can only answer with local retrieval. "
                f"The closest context I found is related to {title}. "
                "Set GOOGLE_API_KEY in .env for full CV coaching responses."
            )
        return (
            "Gemini is not configured yet. Set GOOGLE_API_KEY in .env, then ask again for full CV coaching."
        )


gemini_service = GeminiService()
