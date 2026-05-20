import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime
from open_webui.internal.db import Base


class BlocklySubmission(Base):
    __tablename__ = "blockly_submissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, nullable=False)
    assignment_id = Column(String, nullable=False)
    blocks_json = Column(Text, nullable=True)
    python_code = Column(Text, nullable=True)
    execution_stdout = Column(Text, nullable=True)
    execution_error = Column(Text, nullable=True)
    test_results_json = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)


class BlocklyWorkspaceDraft(Base):
    __tablename__ = "blockly_workspace_drafts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, nullable=False)
    assignment_id = Column(String, nullable=False)
    blocks_json = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)