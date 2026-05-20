from pydantic import BaseModel
from typing import Optional, List


class ExecutionResult(BaseModel):
    stdout: Optional[str] = ""
    stderr: Optional[str] = ""
    error: Optional[str] = None
    timed_out: bool = False
    execution_time_ms: Optional[float] = None


class TestCaseResult(BaseModel):
    index: int
    passed: bool
    expected: str
    got: str
    description: Optional[str] = None
    error: Optional[str] = None


class BlocklyTestResponse(BaseModel):
    stdout: Optional[str] = ""
    stderr: Optional[str] = ""
    error: Optional[str] = None
    test_results: Optional[List[TestCaseResult]] = None
    execution_time_ms: Optional[float] = None
