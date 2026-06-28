"""Diagnostic test service."""

import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ai.providers.proxy import proxy_json
from ai.providers.service import ProvidersService
from common.exceptions import AuthorizationError, NotFoundError
from data.models import DiagnosticResult, Support
from learning.diagnostics.repository import DiagnosticRepository
from learning.supports.repository import SupportRepository

log = logging.getLogger(__name__)


def _parse_questions_json(raw: str) -> List[Dict[str, Any]]:
    """Extract and parse the JSON array from a raw LLM response."""
    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Fallback: slice from first '[' to last ']'
    start = cleaned.find("[")
    end = cleaned.rfind("]") + 1
    if start == -1 or end == 0:
        log.error("No JSON array found in LLM response:\n%s", raw[:500])
        raise ValueError("LLM did not return a JSON array")

    try:
        return json.loads(cleaned[start:end])
    except json.JSONDecodeError as exc:
        log.error(
            "JSON parse failed after extraction (char %d):\n%s",
            exc.colno,
            cleaned[start:end][:500],
        )
        raise


_LEVEL_THRESHOLDS = [
    (71, "avancé"),
    (41, "intermédiaire"),
    (0, "débutant"),
]

_QUESTION_COUNT = 10

_GENERATE_SYSTEM = (
    "You are an expert pedagogical evaluator who generates multiple-choice assessment questions. "
    "Your ONLY job is to assess the learner's knowledge on the EXACT topic given in the prompt. "
    "You MUST generate questions exclusively about that topic — never about related subjects, prerequisites, or other domains. "
    "You MUST respond with ONLY a valid JSON array — no introduction, no explanation, no markdown fences. "
    "Each choice must be a complete phrase or sentence. NEVER use single letters (A, B, C, D) as choices."
)


class DiagnosticsService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = DiagnosticRepository(session, DiagnosticResult)
        self.support_repo = SupportRepository(session, Support)

    def get(self, diagnostic_id: str) -> Optional[DiagnosticResult]:
        return self.repo.get_by_id(diagnostic_id)

    def get_by_support(self, support_id: str) -> Optional[DiagnosticResult]:
        return self.repo.get_by_support(support_id)

    async def generate(
        self, support_id: str, user_id: str, model_id: str
    ) -> DiagnosticResult:
        support = self.support_repo.get_by_id(support_id)
        if not support:
            raise NotFoundError("Support", support_id)
        if support.user_id != user_id:
            raise AuthorizationError("You do not own this support request")

        language = support.content_language or "English"
        title = support.title

        context_lines: List[str] = [f'TOPIC: "{title}"']

        if support.short_description:
            context_lines.append(f"DESCRIPTION: {support.short_description}")

        if support.learning_objective:
            context_lines.append(f"LEARNING OBJECTIVE: {support.learning_objective}")

        if support.keywords:
            context_lines.append(f"KEY CONCEPTS TO COVER: {support.keywords}")

        learning_type = support.learning_type or ""
        if learning_type == "exam":
            context_lines.append(
                "CONTEXT: This is exam preparation — questions should test precise recall "
                "and application of concepts likely to appear in a formal assessment."
            )
        elif learning_type == "skill":
            context_lines.append(
                "CONTEXT: This is skill-based learning — questions should test practical "
                "knowledge and real-world application rather than pure theory."
            )
        elif learning_type == "course":
            context_lines.append(
                "CONTEXT: This is a course — questions should assess prerequisite knowledge "
                "the learner needs before engaging with the course content."
            )

        if support.level:
            context_lines.append(
                f"DECLARED EDUCATION LEVEL: {support.level} — calibrate question difficulty accordingly."
            )

        file_names = [f.filename for f in (support.files or [])]
        if file_names:
            context_lines.append(
                "UPLOADED MATERIALS: "
                + ", ".join(file_names)
                + " — questions may reference concepts likely covered in these materials."
            )

        context_block = "\n".join(context_lines)

        user_prompt = (
            f"Generate exactly {_QUESTION_COUNT} multiple-choice questions in {language} "
            f"to assess the initial knowledge level of a learner. "
            f"Use ALL the context below to make the questions as relevant and targeted as possible.\n\n"
            f"{context_block}\n\n"
            "IMPORTANT: ALL questions must be strictly and exclusively about the topic above. "
            "Do NOT include questions about other subjects, chapters, or unrelated domains.\n\n"
            "Strict rules:\n"
            f"- Write ALL text (questions, choices, explanations) in {language}\n"
            "- Each question must have exactly 4 choices with complete answer text\n"
            "- The correct_answer must be the exact text of one of the choices\n"
            "- Never use single letters (A, B, C, D) as choices — always write the full answer text\n"
            "- Include a brief explanation for why the correct answer is right\n\n"
            "Return ONLY this JSON array (no other text, no markdown fences):\n"
            '[{"id":1,"question":"...","choices":["First complete answer","Second complete answer",'
            '"Third complete answer","Fourth complete answer"],'
            '"correct_answer":"First complete answer","explanation":"..."}]'
        )

        base_url, api_key, path = await ProvidersService(self.session).resolve_provider(
            model_id
        )

        llm_body = {
            "model": model_id,
            "stream": False,
            "messages": [
                {"role": "system", "content": _GENERATE_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
        }

        response = await proxy_json(
            base_url, api_key, "POST", path, body=llm_body, timeout=120.0
        )
        raw_text = response["choices"][0]["message"]["content"]
        questions = _parse_questions_json(raw_text)

        return self.repo.create(
            id=str(uuid.uuid4()),
            support_id=support_id,
            user_id=user_id,
            questions=questions,
            answers=None,
            score=None,
            determined_level=None,
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def submit(
        self, diagnostic_id: str, user_id: str, answers: List[Dict[str, Any]]
    ) -> DiagnosticResult:
        diagnostic = self.repo.get_by_id(diagnostic_id)
        if not diagnostic:
            raise NotFoundError("DiagnosticResult", diagnostic_id)
        if diagnostic.user_id != user_id:
            raise AuthorizationError("You do not own this diagnostic")
        if diagnostic.status == "completed":
            return diagnostic

        questions = diagnostic.questions or []
        correct_map = {str(q["id"]): q["correct_answer"] for q in questions}
        correct_count = sum(
            1
            for a in answers
            if str(a.get("question_id")) in correct_map
            and a.get("answer") == correct_map[str(a.get("question_id"))]
        )
        total = len(questions) or 1
        score = round((correct_count / total) * 100)

        determined_level = "débutant"
        for threshold, label in _LEVEL_THRESHOLDS:
            if score >= threshold:
                determined_level = label
                break

        result = self.repo.update(
            diagnostic_id,
            answers=answers,
            score=score,
            determined_level=determined_level,
            status="completed",
            updated_at=datetime.utcnow(),
        )

        self.support_repo.update(
            diagnostic.support_id,
            level=determined_level,
            updated_at=datetime.utcnow(),
        )

        return result
