"""Guardians service — the parent↔student bond.

Owns the GuardianLink lifecycle (pending → active). The teacher section initiates and
reads links through this service; a future parent portal will read the same links.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from accounts.users.service import AccountService as IdentityService
from common.exceptions import ValidationError
from data.models import GuardianLink
from guardians.repository import GuardianRepository


class GuardiansService:
    """Service for guardian-link operations."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = GuardianRepository(session, GuardianLink)
        self.identity = IdentityService(session)

    def get_links_for_student(self, student_user_id: str) -> List[dict]:
        """All guardian links (pending/active) for a student."""
        return [link.to_dict() for link in self.repo.get_for_student(student_user_id)]

    def link(self, student_user_id: str, created_by: str, email: str) -> Dict[str, Any]:
        """Link a parent to a student.

        Existing `parent` account → an **active** link. Otherwise → a **pending** link
        (the parent accepts later via the shared invitation flow → `resolve_on_accept`).
        """
        parent = self.identity.get_user_by_email(email)
        if parent and parent.role == "parent":
            if self.repo.get_active(student_user_id, parent.id):
                raise ValidationError("This parent is already linked to the student")
            link = self.repo.create(
                id=str(uuid.uuid4()),
                student_user_id=student_user_id,
                parent_user_id=parent.id,
                invited_email=email,
                status="active",
                created_by=created_by,
                created_at=datetime.utcnow(),
            )
            return {"link": link.to_dict(), "status": "active"}

        if self.repo.get_pending_by_email(student_user_id, email):
            raise ValidationError("This parent has already been invited")
        link = self.repo.create(
            id=str(uuid.uuid4()),
            student_user_id=student_user_id,
            parent_user_id=None,
            invited_email=email,
            status="pending",
            created_by=created_by,
            created_at=datetime.utcnow(),
        )
        return {"link": link.to_dict(), "status": "pending"}

    def resolve_on_accept(self, parent_user_id: str, parent_email: str) -> int:
        """Activate pending links awaiting this email; promote the user to parent.

        Called when an invitee accepts a `parent` invitation. Returns the number of
        links activated.
        """
        pendings = self.repo.list_pending_by_email(parent_email)
        for link in pendings:
            link.parent_user_id = parent_user_id
            link.status = "active"
        if pendings:
            user = self.identity.get_user(parent_user_id)
            if user and user.role in (None, "", "user"):
                self.identity.update_role(parent_user_id, "parent")
            self.session.commit()
        return len(pendings)
