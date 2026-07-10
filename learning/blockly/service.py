"""Service métier — Module Blockly."""
from learning.blockly.sandbox import execute_python
from ai.llm.blockly_generator import generate_exercise_stream, get_feedback_stream


class BlocklyService:
    def __init__(self, db=None):
        self.db = db
    """Orchestre sandbox + générateur IA."""

    async def execute_code(self, python_code: str) -> dict:
        """Exécute du code Python via le sandbox isolé."""
        return execute_python(python_code, timeout=5)

    def calculate_score(
        self,
        test_cases: list,
        results: list
    ) -> float:
        """
        Calcule le score en comparant les sorties
        aux résultats attendus.
        """
        if not test_cases:
            return 0.0
        passed = sum(
            1 for tc, r in zip(test_cases, results)
            if (r.get("stdout") or "").strip()
            == tc.get("expected_output", "").strip()
        )
        return round((passed / len(test_cases)) * 100, 1)

    async def run_test_cases(
        self,
        python_code: str,
        test_cases: list
    ) -> list:
        """Exécute le code contre chaque cas de test."""
        results = []
        for tc in test_cases:
            result = execute_python(python_code, timeout=5)
            results.append(result)
        return results

    def get_assignment(self, assignment_id: str, student_id: str) -> dict | None:
        """Retourne l'exercice par ID — à remplacer par une vraie DB."""
        return {
            "id": assignment_id,
            "title": "Exercice Blockly",
            "test_cases": [{"expected_output": "8"}],
            "max_score": 100,
        }

    def save_submission(self, **kwargs) -> None:
        """Sauvegarde une soumission — persistance DB à implémenter."""
        pass

    def save_workspace_draft(
        self, student_id: str, assignment_id: str, blocks_json: str
    ) -> None:
        """Sauvegarde un brouillon workspace — persistance DB à implémenter."""
        pass

    def get_workspace_draft(
        self, student_id: str, assignment_id: str
    ) -> dict | None:
        """Charge un brouillon workspace — persistance DB à implémenter."""
        return None
