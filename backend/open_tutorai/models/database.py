"""
Database module for OpenTutorAI

This module defines the database tables specific to OpenTutorAI while using
the same database connection as OpenWebUI to maintain compatibility.
"""

from datetime import datetime

import uuid
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    UniqueConstraint,
    func,
    ARRAY,
)
from sqlalchemy.orm import relationship, backref
from open_webui.internal.db import Base, get_db, JSONField


PREFIX = "opentutorai_"


class Support(Base):
    """
    Table for storing student support requests.
    Each support request is linked to a chat in the Open WebUI chat table.
    """

    __tablename__ = f"{PREFIX}support"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    short_description = Column(String, nullable=True)
    subject = Column(String, nullable=False)
    custom_subject = Column(String, nullable=True)
    course_id = Column(String, nullable=True)
    learning_objective = Column(Text, nullable=True)
    learning_type = Column(String, nullable=True)
    level = Column(String, nullable=False)
    content_language = Column(String, nullable=True, default="English")
    estimated_duration = Column(String, nullable=True)
    access_type = Column(String, nullable=True, default="Private")
    keywords = Column(String, nullable=True)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    avatar_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default="open")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    meta_data = Column(JSONField, nullable=True)

    chat_id = Column(
        String, ForeignKey("chat.id", ondelete="CASCADE"), index=True, nullable=True
    )

    def __repr__(self):
        return f"<Support(id={self.id}, user_id={self.user_id}, title={self.title})>"


class SupportFile(Base):
    """
    Table for storing files attached to support requests.
    """

    __tablename__ = f"{PREFIX}support_file"

    id = Column(String, primary_key=True, index=True)
    support_id = Column(
        String, ForeignKey(f"{PREFIX}support.id", ondelete="CASCADE"), nullable=False
    )
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    support = relationship("Support", backref="files")

    def __repr__(self):
        return f"<SupportFile(id={self.id}, support_id={self.support_id}, filename={self.filename})>"


class Course(Base):
    """
    Table for storing teacher-created courses.
    """

    __tablename__ = f"{PREFIX}course"

    id = Column(String, primary_key=True, index=True)
    teacher_id = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    language = Column(String, nullable=False)
    category = Column(String, nullable=True)
    custom_category = Column(String, nullable=True)
    level = Column(String, nullable=False)
    objectives = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="draft")
    model_used = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    meta_data = Column(JSONField, nullable=True)
    chat_id = Column(
        String, ForeignKey("chat.id", ondelete="SET NULL"), index=True, nullable=True
    )

    def __repr__(self):
        return (
            f"<Course(id={self.id}, teacher_id={self.teacher_id}, title={self.title})>"
        )


class CourseFile(Base):
    __tablename__ = f"{PREFIX}course_file"

    id = Column(String, primary_key=True, index=True)
    course_id = Column(
        String, ForeignKey(f"{PREFIX}course.id", ondelete="CASCADE"), nullable=False
    )
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    course = relationship("Course", backref="files")

    def __repr__(self):
        return f"<CourseFile(id={self.id}, course_id={self.course_id}, filename={self.filename})>"


class CoursePlan(Base):
    """
    Stores the generated course plan (JSON).
    """

    __tablename__ = f"{PREFIX}course_plan"

    id = Column(String, primary_key=True, index=True)
    course_id = Column(
        String,
        ForeignKey(f"{PREFIX}course.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_json = Column(JSONField, nullable=False)  # full plan (chapters, sections)
    generated_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())

    course = relationship("Course", backref="plans")

    def __repr__(self):
        return f"<CoursePlan(id={self.id}, course_id={self.course_id})>"


class CourseEnrollment(Base):
    """
    Tracks which students are enrolled in which courses.
    The course_id IS the participation code the student enters.
    """

    __tablename__ = f"{PREFIX}course_enrollment"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    course_id = Column(
        String,
        ForeignKey(f"{PREFIX}course.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(String, nullable=False, index=True)
    enrolled_at = Column(DateTime, nullable=False, server_default=func.now())
    status = Column(String, nullable=False, default="active")

    course = relationship("Course", backref="enrollments")

    __table_args__ = (
        UniqueConstraint(
            "course_id", "student_id", name=f"uq_{PREFIX}enrollment_course_student"
        ),
    )

    def __repr__(self):
        return f"<CourseEnrollment(course_id={self.course_id}, student_id={self.student_id})>"


class Quiz(Base):
    """
    Table for storing teacher-created quizzes.
    """

    __tablename__ = f"{PREFIX}quiz"

    id = Column(String, primary_key=True, index=True)
    teacher_id = Column(String, index=True, nullable=False)
    course_id = Column(
        String, ForeignKey(f"{PREFIX}course.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title = Column(String, nullable=False)
    time_limit = Column(Integer, nullable=True)  # in minutes
    total_questions = Column(Integer, nullable=False, default=0)
    limit_date = Column(String, nullable=True)
    model_used = Column(String, nullable=True)
    quiz_code = Column(String, unique=True, index=True, nullable=True)  # 6-char uppercase code
    status = Column(String, nullable=False, default="draft")  # draft, published
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())

    course = relationship("Course", backref="quizzes")

    def __repr__(self):
        return f"<Quiz(id={self.id}, title={self.title}, status={self.status})>"


class QuizQuestion(Base):
    """
    Table for storing questions associated with a quiz.
    """

    __tablename__ = f"{PREFIX}quiz_question"

    id = Column(String, primary_key=True, index=True)
    quiz_id = Column(
        String, ForeignKey(f"{PREFIX}quiz.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_type = Column(String, nullable=False)  # "QCM", "True/False", "Short Answer"
    question_text = Column(Text, nullable=False)
    options = Column(JSONField, nullable=True)  # choices for QCM as array
    correct_answer = Column(String, nullable=False)

    quiz = relationship("Quiz", backref=backref("questions", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<QuizQuestion(id={self.id}, quiz_id={self.quiz_id}, question_type={self.question_type})>"


class QuizSubmission(Base):
    """
    Table for storing student submissions for a quiz.
    """

    __tablename__ = f"{PREFIX}quiz_submission"

    id = Column(String, primary_key=True, index=True)
    quiz_id = Column(
        String, ForeignKey(f"{PREFIX}quiz.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id = Column(String, index=True, nullable=False)
    answers = Column(JSONField, nullable=False)  # JSON payload of student responses
    score = Column(Integer, nullable=False)  # graded score
    submitted_at = Column(DateTime, nullable=False, server_default=func.now())

    quiz = relationship("Quiz", backref=backref("submissions", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<QuizSubmission(id={self.id}, quiz_id={self.quiz_id}, student_id={self.student_id}, score={self.score})>"


def init_database():
    """
    Initialize the database tables for OpenTutorAI.
    Call this function when your app starts to ensure all tables exist.
    """
    from open_webui.internal.db import engine
    from open_tutorai.models.migrations import run_migrations

    Base.metadata.create_all(bind=engine, checkfirst=True)
    print("OpenTutorAI database tables initialized successfully")

    # Run migrations for schema updates
    run_migrations(engine)

    return engine
