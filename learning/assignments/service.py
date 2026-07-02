"""Assignment and submission service — orchestrates repositories and AI-assisted grading."""

import io
import json
import os
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ai.providers.proxy import proxy_json
from ai.providers.service import ProvidersService
from common.exceptions import AuthorizationError, NotFoundError, ValidationError
from data.models import Assignment, Submission
from learning.assignments.repository import AssignmentRepository, SubmissionRepository

GRADING_SYSTEM_PROMPT = (
    "You are a grading assistant helping a teacher. Given a grading rubric and a "
    "student's submission, suggest a score out of 100 and specific, concrete "
    "feedback that references the submission. Respond with a single JSON object "
    'of the exact shape {"score": <integer 0-100>, "feedback": "<string>"} and '
    "nothing else."
)


def extract_pdf_text(contents: bytes) -> Optional[str]:
    """Best-effort PDF text extraction. Returns None if the file can't be read."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(contents))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        text = text.strip()
        return text or None
    except Exception:
        return None


class AssignmentService:
    """Service for assignment and submission operations, including AI-assisted grading."""

    def __init__(self, session: Session):
        self.session = session
        self.assignments = AssignmentRepository(session, Assignment)
        self.submissions = SubmissionRepository(session, Submission)

    # ── Assignments ──────────────────────────────────────────────────────
    def create_assignment(self, teacher_id: str, data: Dict[str, Any]) -> Assignment:
        return self.assignments.create(
            id=str(uuid.uuid4()),
            user_id=teacher_id,
            title=data["title"],
            description=data.get("description"),
            rubric=data["rubric"],
            due_date=data.get("due_date"),
        )

    def get_assignment(self, assignment_id: str) -> Optional[Assignment]:
        return self.assignments.get_by_id(assignment_id)

    def list_assignments_for_teacher(self, teacher_id: str) -> List[Assignment]:
        return self.assignments.get_by_user(teacher_id)

    def verify_assignment_ownership(
        self, teacher_id: str, assignment_id: str
    ) -> Assignment:
        assignment = self.assignments.get_by_id(assignment_id)
        if not assignment:
            raise NotFoundError("Assignment", assignment_id)
        if assignment.user_id != teacher_id:
            raise AuthorizationError("You do not own this assignment")
        return assignment

    # ── Submissions ──────────────────────────────────────────────────────
    def submit_work(
        self,
        student_id: str,
        assignment_id: str,
        filename: str,
        contents: bytes,
        upload_dir: str,
    ) -> Submission:
        assignment = self.assignments.get_by_id(assignment_id)
        if not assignment:
            raise NotFoundError("Assignment", assignment_id)

        os.makedirs(upload_dir, exist_ok=True)
        submission_id = str(uuid.uuid4())
        ext = os.path.splitext(filename or "")[1]
        save_path = os.path.join(upload_dir, f"{submission_id}{ext}")
        with open(save_path, "wb") as fh:
            fh.write(contents)

        extracted_text = extract_pdf_text(contents)

        return self.submissions.create(
            id=submission_id,
            assignment_id=assignment_id,
            user_id=student_id,
            filename=filename,
            file_path=save_path,
            file_size=len(contents),
            extracted_text=extracted_text,
            status="submitted" if extracted_text else "needs_manual_review",
        )

    def verify_submission_ownership(
        self, user_id: str, submission_id: str
    ) -> Submission:
        submission = self.submissions.get_by_id(submission_id)
        if not submission:
            raise NotFoundError("Submission", submission_id)
        if submission.user_id != user_id:
            raise AuthorizationError("You do not own this submission")
        return submission

    def list_submissions_for_assignment(
        self, teacher_id: str, assignment_id: str
    ) -> List[Submission]:
        self.verify_assignment_ownership(teacher_id, assignment_id)
        return self.submissions.get_by_assignment(assignment_id)

    def get_my_submission(
        self, student_id: str, assignment_id: str
    ) -> Optional[Submission]:
        return self.submissions.get_by_assignment_and_user(assignment_id, student_id)

    def _get_submission_for_assignment(
        self, assignment_id: str, submission_id: str
    ) -> Submission:
        submission = self.submissions.get_by_id(submission_id)
        if not submission or submission.assignment_id != assignment_id:
            raise NotFoundError("Submission", submission_id)
        return submission

    # ── AI-assisted grading ──────────────────────────────────────────────
    async def request_ai_grade(
        self, teacher_id: str, assignment_id: str, submission_id: str, model_id: str
    ) -> Submission:
        """Grade with the teacher-selected model — same resolution path as chat.

        Uses ProvidersService.resolve_provider(), the same routing the tutor
        chat uses, so a chosen model must actually exist on an enabled
        provider (Ollama or OpenAI-compatible) or this fails clearly instead
        of silently guessing a model name.
        """
        assignment = self.verify_assignment_ownership(teacher_id, assignment_id)
        submission = self._get_submission_for_assignment(assignment_id, submission_id)

        if not submission.extracted_text:
            raise ValidationError(
                "This submission has no readable text — grade it manually",
                field="submission",
            )

        body = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": GRADING_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Rubric:\n{assignment.rubric}\n\n"
                        f"Submission:\n{submission.extracted_text}"
                    ),
                },
            ],
        }

        try:
            base_url, api_key, path = await ProvidersService(
                self.session
            ).resolve_provider(model_id)
            result = await proxy_json(base_url, api_key, "POST", path, body=body)
            content = result["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            score = int(parsed["score"])
            feedback = str(parsed["feedback"])
        except Exception:
            return self.submissions.update(submission_id, status="ai_grade_failed")

        return self.submissions.update(
            submission_id, ai_score=score, ai_feedback=feedback, status="ai_graded"
        )

    def finalize_grade(
        self,
        teacher_id: str,
        assignment_id: str,
        submission_id: str,
        score: int,
        feedback: str,
    ) -> Submission:
        self.verify_assignment_ownership(teacher_id, assignment_id)
        self._get_submission_for_assignment(assignment_id, submission_id)
        return self.submissions.update(
            submission_id,
            teacher_score=score,
            teacher_feedback=feedback,
            status="finalized",
        )
