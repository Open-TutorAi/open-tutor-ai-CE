import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from open_webui.utils.auth import get_current_user
from open_webui.internal.db import get_db

# Import models from our database file
from open_tutorai.models.database import (
    DiscussionRoom,
    DiscussionMessage,
    Course,
    CourseEnrollment,
)

router = APIRouter()


# ── SCHEMAS ──────────────────────────────────────────────────
class SendMessageForm(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    sender_id: str
    sender_role: str
    sender_name: str
    content: str
    timestamp: str

    class Config:
        from_attributes = True


class RoomResponse(BaseModel):
    id: str
    course_id: str
    student_name: str  # Represents course name in this layout for compatibility
    last_message: str = ""
    members_count: int = 1

    class Config:
        from_attributes = True


# ── ENDPOINTS FOR TEACHER ─────────────────────────────────────


@router.get("/courses", response_model=List[RoomResponse])
async def get_teacher_courses(
    user=Depends(get_current_user), db: Session = Depends(get_db)
):
    # Authorization check for teachers and admins
    if user.role != "teacher" and user.role != "admin":
        raise HTTPException(status_code=401, detail="Access Prohibited")

    with db as session:
        # Fetch courses taught by the current teacher ordered by creation date
        courses = (
            session.query(Course)
            .filter(Course.teacher_id == user.id)
            .order_by(Course.created_at.desc())
            .all()
        )

        result = []
        for course in courses:
            # Check if discussion room exists, if not, create it dynamically
            room = (
                session.query(DiscussionRoom)
                .filter(DiscussionRoom.id == course.id)
                .first()
            )
            if not room:
                room = DiscussionRoom(
                    id=course.id,
                    course_id=course.id,
                    student_id="group",
                    student_name=course.title,
                    created_at=datetime.utcnow(),
                )
                session.add(room)
                session.commit()

            # Fetch the latest message for the course channel
            last_msg = (
                session.query(DiscussionMessage)
                .filter(DiscussionMessage.room_id == course.id)
                .order_by(DiscussionMessage.timestamp.desc())
                .first()
            )

            # Modern and efficient count query using SQLAlchemy select statement
            stmt = select(func.count()).where(CourseEnrollment.course_id == course.id)
            students_count = session.execute(stmt).scalar() or 0

            result.append(
                {
                    "id": course.id,
                    "course_id": course.id,
                    "student_name": course.title,
                    "last_message": (
                        last_msg.content if last_msg else "Pas de message..."
                    ),
                    "members_count": students_count
                    + 1,  # Total members including the teacher
                }
            )

        return result


## ── ENDPOINTS FOR STUDENT ─────────────────────────────────────


@router.get("/student/courses", response_model=List[RoomResponse])
async def get_student_courses(
    user=Depends(get_current_user), db: Session = Depends(get_db)
):
    # ✅ FLEXIBLE GUARD: Allow access if the user is a student, a regular user, or admin
    if user.role == "teacher":
        raise HTTPException(
            status_code=401, detail="Access Prohibited for Teachers here"
        )

    with db as session:
        # Fetch all enrollments for the logged-in student (explicit string cast for safety)
        enrollments = (
            session.query(CourseEnrollment)
            .filter(CourseEnrollment.student_id == str(user.id))
            .all()
        )
        course_ids = [str(e.course_id) for e in enrollments]

        # If student is not enrolled in any course, return an empty list immediately
        if not course_ids:
            return []

        # Fetch all courses the student is enrolled in
        courses = (
            session.query(Course)
            .filter(Course.id.in_(course_ids))
            .order_by(Course.created_at.desc())
            .all()
        )

        result = []
        for course in courses:
            last_msg = (
                session.query(DiscussionMessage)
                .filter(DiscussionMessage.room_id == str(course.id))
                .order_by(DiscussionMessage.timestamp.desc())
                .first()
            )

            stmt = select(func.count()).where(
                CourseEnrollment.course_id == str(course.id)
            )
            students_count = session.execute(stmt).scalar() or 0

            result.append(
                {
                    "id": str(course.id),
                    "course_id": str(course.id),
                    "student_name": course.title,
                    "last_message": (
                        last_msg.content if last_msg else "Pas de message..."
                    ),
                    "members_count": students_count + 1,
                }
            )

        return result


# ── COMMON CHAT ENDPOINTS ─────────────────────────────────────


@router.get("/rooms/{room_id}/messages", response_model=List[MessageResponse])
async def get_room_messages(
    room_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)
):
    with db as session:
        # Verify the course channel existence
        course = session.query(Course).filter(Course.id == room_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        # Permission guard: user must be admin, the teacher of the course, or an enrolled student
        if user.role != "admin" and course.teacher_id != user.id:
            enrolled = (
                session.query(CourseEnrollment)
                .filter(
                    CourseEnrollment.course_id == room_id,
                    CourseEnrollment.student_id == user.id,
                )
                .first()
            )
            if not enrolled:
                raise HTTPException(status_code=403, detail="Access Prohibited")

        # Fetch all messages for this room ordered chronologically
        messages = (
            session.query(DiscussionMessage)
            .filter(DiscussionMessage.room_id == room_id)
            .order_by(DiscussionMessage.timestamp.asc())
            .all()
        )

        return [
            {
                "id": m.id,
                "sender_id": str(m.sender_id),
                "sender_role": m.sender_role,
                "sender_name": m.sender_name,
                "content": m.content,
                "timestamp": m.timestamp.isoformat(),
            }
            for m in messages
        ]


@router.post("/rooms/{room_id}/send")
async def send_discussion_message(
    room_id: str,
    form_data: SendMessageForm,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    with db as session:
        # Verify the course channel existence
        course = session.query(Course).filter(Course.id == room_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        # Permission check: ensure the sender belongs to the course channel
        if user.role != "teacher" and user.role != "admin":
            enrolled = (
                session.query(CourseEnrollment)
                .filter(
                    CourseEnrollment.course_id == room_id,
                    CourseEnrollment.student_id == user.id,
                )
                .first()
            )
            if not enrolled:
                raise HTTPException(
                    status_code=403,
                    detail="You are not enrolled in this course channel",
                )
        elif user.role == "teacher" and course.teacher_id != user.id:
            raise HTTPException(status_code=403, detail="You do not teach this course")

        # Save the new message dynamically capturing user role and name
        new_msg = DiscussionMessage(
            room_id=room_id,
            sender_id=user.id,
            sender_role=user.role,  # Saves "student" or "teacher" dynamically
            sender_name=(
                user.name
                if (hasattr(user, "name") and user.name)
                else ("Professeur" if user.role == "teacher" else "Étudiant")
            ),
            content=form_data.content,
            timestamp=datetime.utcnow(),
        )
        session.add(new_msg)
        session.commit()
        return {"status": "success", "message_id": new_msg.id}


# ── UPDATE MESSAGE ENDPOINT (STRICT CASTING + TEACHER GUARD) ──


@router.put("/messages/{message_id}")
async def update_message(
    message_id: str,  # Read as string from URL to prevent routing/casting mismatch
    form_data: SendMessageForm,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    with db as session:
        try:
            db_id = int(message_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid message ID format")

        message = (
            session.query(DiscussionMessage)
            .filter(DiscussionMessage.id == db_id)
            .first()
        )
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        # 🔒 STRICT RULE: Only the absolute original author can EDIT their own text
        # (Pedagogically, a teacher cannot modify a student's actual words)
        if str(message.sender_id).strip() != str(user.id).strip():
            raise HTTPException(
                status_code=403, detail="You can only edit your own messages"
            )

        message.content = form_data.content.strip()
        session.commit()

        return {"status": "success", "message": "Message updated successfully"}


# ── DELETE MESSAGE ENDPOINT (TEACHER MODERATION ALLOWED) ──────


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,  # Read as string from URL to prevent routing/casting mismatch
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    with db as session:
        try:
            db_id = int(message_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid message ID format")

        message = (
            session.query(DiscussionMessage)
            .filter(DiscussionMessage.id == db_id)
            .first()
        )
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        # 🔑 FLEXIBLE GUARD: Author can delete their own message OR a teacher/admin can delete ANY message for moderation
        is_author = str(message.sender_id).strip() == str(user.id).strip()
        is_moderator = user.role == "teacher" or user.role == "admin"

        if not is_author and not is_moderator:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to delete this message",
            )

        session.delete(message)
        session.commit()

        return {"status": "success", "message": "Message deleted successfully"}


# ── REMOVE STUDENT FROM COURSE CHANNEL (KICK ENDPOINT) ────────


@router.delete("/rooms/{room_id}/students/{student_id}")
async def remove_student_from_course(
    room_id: str,
    student_id: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Security check: Only teachers or admins can access this orchestration
    if user.role != "teacher" and user.role != "admin":
        raise HTTPException(status_code=401, detail="Unauthorized action")

    with db as session:
        # Verify that the current teacher actually owns this specific course
        course = (
            session.query(Course)
            .filter(Course.id == room_id, Course.teacher_id == user.id)
            .first()
        )
        if not course and user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to manage this course",
            )

        # Find the enrollment record and remove it completely from database
        enrollment = (
            session.query(CourseEnrollment)
            .filter(
                CourseEnrollment.course_id == room_id,
                CourseEnrollment.student_id == student_id,
            )
            .first()
        )

        if not enrollment:
            raise HTTPException(status_code=404, detail="Student enrollment not found")

        session.delete(enrollment)
        session.commit()

        return {
            "status": "success",
            "message": "Student successfully removed from course channel",
        }
