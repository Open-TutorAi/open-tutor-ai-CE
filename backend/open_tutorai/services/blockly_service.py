import uuid
import json
import requests
from typing import AsyncGenerator, Optional, List
from sqlalchemy.orm import Session

from open_tutorai.schemas.blockly import (
    ExecutionResult, TestCaseResult, BlocklyTestResponse
)
from open_tutorai.models.blockly_submission import BlocklySubmission, BlocklyWorkspaceDraft
from open_tutorai.services.executor import Judge0Executor


class BlocklyService:

    def __init__(self, db: Session):
        self.db = db
        self.executor = Judge0Executor()

    def get_assignment(self, assignment_id: str, student_id: str) -> Optional[dict]:
        return {
            "id": assignment_id,
            "title": "Calcul de la somme",
            "description": "Créez un programme qui affiche la somme de deux nombres.",
            "allowed_blocks": None,
            "test_cases": [
                {"inputs": {}, "expected_output": "8"},
            ],
            "max_score": 100,
            "hints": [
                "Utilisez un bloc de variable pour stocker chaque nombre.",
                "Le bloc 'Additionner' se trouve dans la catégorie Math.",
            ],
        }

    async def execute_code(self, python_code: str) -> ExecutionResult:
        return await self.executor.execute(python_code)

    async def run_test_cases(self, python_code: str, test_cases: list) -> List[TestCaseResult]:
        results = []
        for i, tc in enumerate(test_cases):
            inputs = tc.get("inputs", {})
            stdin_lines = "\n".join(str(v) for v in inputs.values()) if inputs else ""
            result = await self.executor.execute(python_code, stdin=stdin_lines)
            actual_output = (result.stdout or "").strip()
            expected = str(tc["expected_output"]).strip()
            results.append(TestCaseResult(
                index=i + 1,
                passed=(actual_output == expected),
                expected=expected,
                got=actual_output,
                description=tc.get("description"),
                error=result.error,
            ))
        return results

    def calculate_score(self, test_results: List[TestCaseResult], max_score: int = 100) -> int:
        if not test_results:
            return 0
        passed = sum(1 for r in test_results if r.passed)
        return round((passed / len(test_results)) * max_score)

    async def test_code(self, python_code: str, assignment_id: str, student_id: str) -> BlocklyTestResponse:
        assignment = self.get_assignment(assignment_id, student_id)
        if not assignment:
            return BlocklyTestResponse(error="Exercice introuvable")
        exec_result = await self.executor.execute(python_code)
        test_results = None
        if assignment.get("test_cases"):
            test_results = await self.run_test_cases(python_code, assignment["test_cases"])
        return BlocklyTestResponse(
            stdout=exec_result.stdout,
            stderr=exec_result.stderr,
            error=exec_result.error,
            test_results=test_results,
            execution_time_ms=exec_result.execution_time_ms,
        )

    async def generate_feedback_stream(
        self,
        python_code: str,
        execution_result,
        test_results,
        score: int,
        assignment: dict,
        student_level: str = "débutant",
        **kwargs
    ) -> AsyncGenerator[str, None]:
        passed_count = sum(1 for r in test_results if r.passed)
        total_count = len(test_results)
        prompt = f"""Tu es un tuteur Python. Réponds en français uniquement.

L'étudiant a soumis ce code pour l'exercice "{assignment['title']}":
{python_code}

Score : {score}/100. Tests réussis : {passed_count}/{total_count}.

En 3 phrases maximum :
- Félicite si score >= 80, encourage si score < 80
- Dis ce qui est correct dans le code
- Donne UN conseil précis et concret"""

        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    "model": "qwen2.5:0.5b",
                    "prompt": prompt,
                    "stream": True,
                    "options": {"temperature": 0.7, "num_predict": 200}
                },
                stream=True,
                timeout=120
            )
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if 'response' in data:
                            yield data['response']
                        if data.get('done'):
                            break
                    except Exception:
                        continue
        except Exception as e:
            yield f"Feedback non disponible : {str(e)}"

    def save_submission(self, student_id, assignment_id, blocks_json, python_code,
                        execution_result, test_results, score):
        submission = BlocklySubmission(
            id=str(uuid.uuid4()),
            student_id=student_id,
            assignment_id=assignment_id,
            blocks_json=blocks_json,
            python_code=python_code,
            execution_stdout=execution_result.stdout,
            execution_error=execution_result.error,
            test_results_json=json.dumps([r.dict() for r in test_results]),
            score=score,
        )
        self.db.add(submission)
        self.db.commit()
        return submission.id

    def save_workspace_draft(self, student_id, assignment_id, blocks_json):
        draft = self.db.query(BlocklyWorkspaceDraft).filter_by(
            student_id=student_id, assignment_id=assignment_id
        ).first()
        if draft:
            draft.blocks_json = blocks_json
        else:
            draft = BlocklyWorkspaceDraft(
                student_id=student_id,
                assignment_id=assignment_id,
                blocks_json=blocks_json
            )
            self.db.add(draft)
        self.db.commit()

    def get_workspace_draft(self, student_id, assignment_id):
        draft = self.db.query(BlocklyWorkspaceDraft).filter_by(
            student_id=student_id, assignment_id=assignment_id
        ).first()
        if not draft:
            return None
        return {"blocks_json": draft.blocks_json, "updated_at": draft.updated_at}

    def get_history(self, student_id, assignment_id=None, limit=20):
        query = self.db.query(BlocklySubmission).filter_by(student_id=student_id)
        if assignment_id:
            query = query.filter_by(assignment_id=assignment_id)
        return query.order_by(BlocklySubmission.submitted_at.desc()).limit(limit).all()