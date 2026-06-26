"""Service métier — Module Blockly."""
from learning.blockly.sandbox import execute_python
from ai.llm.blockly_generator import BlocklyLLMGenerator


class BlocklyService:
    """Orchestre sandbox + générateur IA."""

    def __init__(self):
        self.generator = BlocklyLLMGenerator()

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