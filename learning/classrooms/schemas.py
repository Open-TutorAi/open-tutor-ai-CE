"""Classroom request/response schemas."""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ClassroomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    subject: Optional[str] = Field(default=None, max_length=200)
    course: Optional[str] = Field(default=None, max_length=200)
    objectives: Optional[str] = Field(default=None, max_length=2000)
    level: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=2000)


class ClassroomUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    subject: Optional[str] = Field(default=None, max_length=200)
    course: Optional[str] = Field(default=None, max_length=200)
    objectives: Optional[str] = Field(default=None, max_length=2000)
    level: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=2000)


class ClassroomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    subject: Optional[str] = None
    course: Optional[str] = None
    objectives: Optional[str] = None
    level: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    owner_id: str
    student_count: int = 0


class EnrolledClassroomOut(ClassroomOut):
    """A classroom from the perspective of an enrolled student."""

    active_session_id: Optional[str] = None


class ActivityItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: str
    title: str
    date: datetime


class ClassroomDetail(ClassroomOut):
    objectives_list: List[str] = []
    recent_activity: List[ActivityItem] = []
    join_code: Optional[str] = None


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    enrolled_at: date
    profile_image_url: Optional[str] = None


class AddStudentRequest(BaseModel):
    email: EmailStr


class AddStudentResult(BaseModel):
    student_id: str
    student_name: str
    student_email: str


class ImportRowReport(BaseModel):
    row_number: int
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    created: bool = False
    enrolled: bool = False
    error: Optional[str] = None


class ImportResult(BaseModel):
    created: int = 0
    enrolled: int = 0
    skipped: int = 0
    rows: List[ImportRowReport] = []


class InviteCreate(BaseModel):
    expires_at: Optional[datetime] = None
    max_uses: Optional[int] = Field(default=None, ge=1)


class InviteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    classroom_id: str
    created_by: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    max_uses: Optional[int] = None
    uses: int = 0


class InviteRedeemResult(BaseModel):
    student_id: str
    enrolled: bool
