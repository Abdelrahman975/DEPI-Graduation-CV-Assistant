import csv
import hashlib
import logging
import math
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from config.settings import settings
from core.text_utils import lexical_score, normalize_text

logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)


class VectorStore:
    JOBS = "jobs"
    INTERVIEW = "interview_questions"
    ATS = "ats_examples"
    SCREENING = "resume_screening"

    def __init__(self):
        self.chroma_available = False
        self.client = None
        self.embedding_function = None
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=str(settings.CHROMA_DIR),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self.embedding_function = self._create_embedding_function()
            self.chroma_available = True
        except Exception as exc:
            self.init_error = str(exc)
        else:
            self.init_error = None

    def build_all(self, reset: bool = True) -> Dict[str, int]:
        counts = {
            self.JOBS: self._build_jobs(reset=reset),
            self.INTERVIEW: self._build_interview_questions(reset=reset),
            self.ATS: self._build_ats_examples(reset=reset),
            self.SCREENING: self._build_resume_screening(reset=reset),
        }
        return counts

    def search_jobs(self, query: str, top_k: int = 8) -> List[Dict[str, Any]]:
        if self.chroma_available and self._collection_exists(self.JOBS):
            return self._query_collection(self.JOBS, query, top_k)
        return self._fallback_jobs(query, top_k)

    def search_interview_questions(
        self, query: str, top_k: int = 8, difficulty: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if self.chroma_available and self._collection_exists(self.INTERVIEW):
            where = {"difficulty": difficulty} if difficulty else None
            return self._query_collection(self.INTERVIEW, query, top_k, where=where)
        rows = self._read_csv(settings.INTERVIEW_QUESTIONS_PATH)
        if difficulty:
            rows = [row for row in rows if row.get("difficulty", "").lower() == difficulty.lower()]
        scored = []
        for row in rows:
            document = f"{row.get('question', '')} {row.get('category', '')}"
            row["_distance_score"] = lexical_score(query, document)
            row["document"] = row.get("question", "")
            scored.append(row)
        return sorted(scored, key=lambda item: item["_distance_score"], reverse=True)[:top_k]

    def search_context(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        results = []
        results.extend(self.search_jobs(query, max(2, top_k // 2)))
        results.extend(self.search_interview_questions(query, max(2, top_k // 2)))
        return results[:top_k]

    def _build_jobs(self, reset: bool) -> int:
        rows = self._read_csv(settings.CLEAN_JOBS_PATH)
        if not self.chroma_available:
            return len(rows)
        collection = self._get_collection(self.JOBS, reset=reset)
        documents, ids, metadatas = [], [], []
        for row in rows:
            job_id = row.get("id") or str(len(ids) + 1)
            document = normalize_text(
                f"{row.get('title', '')}\n{row.get('company', '')}\n{row.get('location', '')}\n{row.get('description', '')}"
            )
            if not document:
                continue
            ids.append(f"job-{job_id}")
            documents.append(document[:12000])
            metadatas.append(
                {
                    "kind": "job",
                    "id": str(job_id),
                    "title": row.get("title", ""),
                    "company": row.get("company", ""),
                    "location": row.get("location", ""),
                    "link": row.get("link", ""),
                    "source": row.get("source", ""),
                    "date_posted": row.get("date_posted", ""),
                }
            )
        self._add_in_batches(collection, ids, documents, metadatas)
        return len(ids)

    def _build_interview_questions(self, reset: bool) -> int:
        rows = self._read_csv(settings.INTERVIEW_QUESTIONS_PATH)
        if not self.chroma_available:
            return len(rows)
        collection = self._get_collection(self.INTERVIEW, reset=reset)
        ids, documents, metadatas = [], [], []
        for row in rows:
            question_id = row.get("id") or str(len(ids) + 1)
            question = normalize_text(row.get("question", ""))
            if not question:
                continue
            ids.append(f"question-{question_id}")
            documents.append(question)
            metadatas.append(
                {
                    "kind": "interview_question",
                    "id": str(question_id),
                    "category": row.get("category", ""),
                    "difficulty": row.get("difficulty", ""),
                    "date": row.get("date", ""),
                }
            )
        self._add_in_batches(collection, ids, documents, metadatas)
        return len(ids)

    def _build_ats_examples(self, reset: bool) -> int:
        rows = [*self._read_csv(settings.ATS_TRAIN_PATH), *self._read_csv(settings.ATS_VALIDATION_PATH)]
        if not self.chroma_available:
            return len(rows)
        collection = self._get_collection(self.ATS, reset=reset)
        ids, documents, metadatas = [], [], []
        for idx, row in enumerate(rows, 1):
            document = normalize_text(row.get("text", ""))
            if not document:
                continue
            ids.append(f"ats-{idx}")
            documents.append(document[:12000])
            metadatas.append(
                {
                    "kind": "ats_example",
                    "ats_score": float(row.get("ats_score") or 0),
                    "original_label": row.get("original_label", ""),
                }
            )
        self._add_in_batches(collection, ids, documents, metadatas)
        return len(ids)

    def _build_resume_screening(self, reset: bool) -> int:
        rows = self._read_csv(settings.RESUME_SCREENING_PATH)
        if not self.chroma_available:
            return len(rows)
        collection = self._get_collection(self.SCREENING, reset=reset)
        ids, documents, metadatas = [], [], []
        for row in rows:
            resume_id = row.get("Resume_ID") or str(len(ids) + 1)
            document = normalize_text(
                f"{row.get('Job Role', '')}. Skills: {row.get('Skills', '')}. "
                f"Education: {row.get('Education', '')}. Certifications: {row.get('Certifications', '')}."
            )
            if not document:
                continue
            ids.append(f"screening-{resume_id}")
            documents.append(document)
            metadatas.append(
                {
                    "kind": "resume_screening",
                    "resume_id": str(resume_id),
                    "job_role": row.get("Job Role", ""),
                    "skills": row.get("Skills", ""),
                    "ai_score": float(row.get("AI Score (0-100)") or 0),
                    "decision": row.get("Recruiter Decision", ""),
                }
            )
        self._add_in_batches(collection, ids, documents, metadatas)
        return len(ids)

    def _query_collection(
        self, name: str, query: str, top_k: int, where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        collection = self._get_collection(name, reset=False)
        kwargs = {"query_texts": [query], "n_results": top_k}
        if where:
            kwargs["where"] = where
        response = collection.query(**kwargs)
        documents = response.get("documents", [[]])[0]
        metadatas = response.get("metadatas", [[]])[0]
        distances = response.get("distances", [[]])[0]
        results = []
        for document, metadata, distance in zip(documents, metadatas, distances):
            item = dict(metadata or {})
            item["document"] = document
            item["distance"] = distance
            item["_distance_score"] = round(max(0.0, 1.0 - float(distance)) * 100, 2)
            results.append(item)
        return results

    def _fallback_jobs(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        rows = self._read_csv(settings.CLEAN_JOBS_PATH)
        scored = []
        for row in rows:
            document = normalize_text(
                f"{row.get('title', '')} {row.get('company', '')} {row.get('location', '')} {row.get('description', '')}"
            )
            row["document"] = document
            row["_distance_score"] = lexical_score(query, document)
            scored.append(row)
        return sorted(scored, key=lambda item: item["_distance_score"], reverse=True)[:top_k]

    def _get_collection(self, name: str, reset: bool):
        if not self.chroma_available or self.client is None:
            raise RuntimeError(f"Chroma is not available: {self.init_error}")
        if reset and self._collection_exists(name):
            self.client.delete_collection(name)
        return self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"},
        )

    def _collection_exists(self, name: str) -> bool:
        if not self.chroma_available or self.client is None:
            return False
        try:
            self.client.get_collection(name)
            return True
        except Exception:
            return False

    def _add_in_batches(self, collection, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]]) -> None:
        batch_size = 100
        for start in range(0, len(ids), batch_size):
            end = start + batch_size
            collection.add(
                ids=ids[start:end],
                documents=documents[start:end],
                metadatas=metadatas[start:end],
            )

    def _read_csv(self, path: Path) -> List[Dict[str, str]]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))

    def _create_embedding_function(self):
        try:
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

            return SentenceTransformerEmbeddingFunction(model_name=settings.EMBEDDING_MODEL)
        except Exception:
            return HashEmbeddingFunction()


class HashEmbeddingFunction:
    """Small deterministic fallback when sentence-transformers is not installed yet."""

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions

    def __call__(self, input):
        return [self._embed(text) for text in input]

    def _embed(self, text: str) -> List[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.\-]{1,}", (text or "").lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "little") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


vector_store = VectorStore()
