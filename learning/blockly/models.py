from data.database import Base
from sqlalchemy import Column, String, Float, Text, DateTime
import uuid, datetime


class BlocklySubmission(Base):
    __tablename__ = "blockly_submissions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, nullable=False)
    assignment_id = Column(String, nullable=False)
    python_code = Column(Text, nullable=False)
    score = Column(Float, nullable=True)
    level = Column(String, default="beginner")
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)


class BlocklyWorkspace(Base):
    __tablename__ = "blockly_workspaces"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, nullable=False)
    assignment_id = Column(String, nullable=False)
    workspace_xml = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)


class BlocklyExercise(Base):
    __tablename__ = "blockly_exercises"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, nullable=False)
    level = Column(String, default="beginner")
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    test_cases = Column(Text, nullable=False)  # JSON string
    hints = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
