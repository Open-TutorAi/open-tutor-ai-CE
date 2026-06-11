from pydantic import BaseModel
from typing import Optional, List

class ExecutionRequest(BaseModel):
    python_code: str
    assignment_id: Optional[str] = None
    level: Optional[str] = "beginner"

class TestCase(BaseModel):
    input: Optional[str] = None
    expected_output: str

class Assignment(BaseModel):
    id: str
    title: str
    description: str
    level: str
    test_cases: List[TestCase]
    hints: List[str]

class ExecutionResult(BaseModel):
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    error: Optional[str] = None
    timed_out: bool = False
    execution_time_ms: Optional[float] = None
