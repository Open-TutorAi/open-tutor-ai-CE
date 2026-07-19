"""Service métier — Module Blockly."""
import json
from learning.blockly.sandbox import execute_python
from learning.blockly.models import BlocklyExercise, BlocklySubmission, BlocklyWorkspace
from ai.llm.blockly_generator import generate_exercise_stream, get_feedback_stream


class BlocklyService:
    """Orchestre sandbox + générateur IA."""

    def __init__(self, db=None):
        self.db = db

    async def execute_code(self, python_code: str) -> dict:
        """Exécute du code Python via le sandbox isolé."""
        return execute_python(python_code, timeout=5)

    def calculate_score(self, test_cases: list, results: list) -> float:
        """Calcule le score en comparant les sorties aux résultats attendus."""
        if not test_cases:
            return 0.0
        passed = sum(
            1 for tc, r in zip(test_cases, results)
            if (r.get("stdout") or "").strip()
            == tc.get("expected_output", "").strip()
        )
        return round((passed / len(test_cases)) * 100, 1)

    async def run_test_cases(self, python_code: str, test_cases: list) -> list:
        """Exécute le code contre chaque cas de test."""
        results = []
        for tc in test_cases:
            result = execute_python(python_code, timeout=5)
            results.append(result)
        return results

    def save_exercise(self, student_id: str, level: str, exercise: dict) -> str:
        """
        Sauvegarde l'exercice généré par l'IA en DB.
        Retourne l'assignment_id pour référence future.
        """
        if not self.db:
            return ""
        ex = BlocklyExercise(
            student_id=student_id,
            level=level,
            title=exercise.get("title", ""),
            description=exercise.get("description", ""),
            test_cases=json.dumps(exercise.get("test_cases", [])),
            hints=json.dumps(exercise.get("hints", [])),
        )
        self.db.add(ex)
        self.db.commit()
        self.db.refresh(ex)
        return ex.id

    def get_exercise(self, assignment_id: str, student_id: str) -> dict | None:
        """
        Récupère l'exercice depuis la DB via son ID.
        Vérifie que l'exercice appartient à l'étudiant.
        """
        if not self.db or not assignment_id:
            return None
        ex = self.db.query(BlocklyExercise).filter_by(
            id=assignment_id,
            student_id=student_id  # sécurité : un étudiant ne peut pas accéder aux exercices d'un autre
        ).first()
        if not ex:
            return None
        return {
            "id": ex.id,
            "title": ex.title,
            "description": ex.description,
            "test_cases": json.loads(ex.test_cases or "[]"),
            "hints": json.loads(ex.hints or "[]"),
            "level": ex.level,
        }

    def save_submission(self, student_id: str, assignment_id: str,
                        python_code: str, score: float, level: str) -> None:
        if not self.db:
            return
        sub = BlocklySubmission(
            student_id=student_id,
            assignment_id=assignment_id,
            python_code=python_code,
            score=score,
            level=level,
        )
        self.db.add(sub)
        self.db.commit()

    def save_workspace_draft(self, student_id: str, assignment_id: str,
                             blocks_json: str) -> None:
        if not self.db:
            return
        draft = self.db.query(BlocklyWorkspace).filter_by(
            student_id=student_id, assignment_id=assignment_id
        ).first()
        if draft:
            draft.workspace_xml = blocks_json
        else:
            draft = BlocklyWorkspace(
                student_id=student_id,
                assignment_id=assignment_id,
                workspace_xml=blocks_json,
            )
            self.db.add(draft)
        self.db.commit()

    def get_workspace_draft(self, student_id: str, assignment_id: str) -> dict | None:
        if not self.db:
            return None
        draft = self.db.query(BlocklyWorkspace).filter_by(
            student_id=student_id, assignment_id=assignment_id
        ).first()
        if not draft:
            return None
        return {"blocks_json": draft.workspace_xml}