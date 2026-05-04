# backend/tests/test_blockly.py
"""
Tests Pytest pour le module Blockly.
Couvre : exécution, évaluation, scoring, API endpoints.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from backend.services.blockly_service import PythonExecutor, BlocklyService
from backend.open_tutorai.schemas.blockly import TestCaseResult


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def executor():
    return PythonExecutor()


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def blockly_service(mock_db):
    return BlocklyService(mock_db)


# ─── Tests PythonExecutor ────────────────────────────────────────────────────

class TestPythonExecutor:

    def test_execute_simple_print(self, executor):
        """Un print simple doit retourner la bonne sortie."""
        result = asyncio.get_event_loop().run_until_complete(
            executor.execute("print('Bonjour')")
        )
        assert result.stdout.strip() == "Bonjour"
        assert result.error is None

    def test_execute_arithmetic(self, executor):
        """Calcul arithmétique basique."""
        result = asyncio.get_event_loop().run_until_complete(
            executor.execute("print(3 + 5)")
        )
        assert result.stdout.strip() == "8"

    def test_execute_sum_function(self, executor):
        """Exercice typique : somme de deux nombres."""
        code = """
a = 3
b = 5
print(a + b)
"""
        result = asyncio.get_event_loop().run_until_complete(executor.execute(code))
        assert result.stdout.strip() == "8"
        assert result.error is None

    def test_execute_syntax_error(self, executor):
        """Une erreur de syntaxe doit être capturée proprement."""
        result = asyncio.get_event_loop().run_until_complete(
            executor.execute("def broken(:")
        )
        assert result.error is not None
        assert "syntaxe" in result.error.lower() or "syntax" in result.error.lower()

    def test_execute_runtime_error(self, executor):
        """Une division par zéro doit être capturée."""
        result = asyncio.get_event_loop().run_until_complete(
            executor.execute("print(1/0)")
        )
        assert result.error is not None

    def test_execute_forbidden_import(self, executor):
        """Les imports de modules système doivent être bloqués."""
        result = asyncio.get_event_loop().run_until_complete(
            executor.execute("import os; print(os.getcwd())")
        )
        # Doit échouer car 'import' utilise __builtins__ restreints
        assert result.error is not None or result.stdout == ""

    def test_execute_loop(self, executor):
        """Les boucles doivent fonctionner correctement."""
        code = """
total = 0
for i in range(1, 6):
    total += i
print(total)
"""
        result = asyncio.get_event_loop().run_until_complete(executor.execute(code))
        assert result.stdout.strip() == "15"

    def test_execute_timeout(self, executor):
        """Un programme qui boucle indéfiniment doit être interrompu."""
        code = "while True: pass"
        result = asyncio.get_event_loop().run_until_complete(executor.execute(code))
        assert result.timed_out or result.error is not None


# ─── Tests BlocklyService ─────────────────────────────────────────────────────

class TestBlocklyService:

    def test_calculate_score_all_passed(self, blockly_service):
        """Score = 100 si tous les tests passent."""
        results = [
            TestCaseResult(index=1, passed=True, expected="8", got="8"),
            TestCaseResult(index=2, passed=True, expected="0", got="0"),
        ]
        score = blockly_service.calculate_score(results, max_score=100)
        assert score == 100

    def test_calculate_score_half_passed(self, blockly_service):
        """Score = 50 si la moitié des tests passent."""
        results = [
            TestCaseResult(index=1, passed=True, expected="8", got="8"),
            TestCaseResult(index=2, passed=False, expected="0", got="3"),
        ]
        score = blockly_service.calculate_score(results, max_score=100)
        assert score == 50

    def test_calculate_score_none_passed(self, blockly_service):
        """Score = 0 si aucun test ne passe."""
        results = [
            TestCaseResult(index=1, passed=False, expected="8", got="wrong"),
        ]
        score = blockly_service.calculate_score(results, max_score=100)
        assert score == 0

    def test_calculate_score_empty(self, blockly_service):
        """Score = 0 si aucun test défini."""
        assert blockly_service.calculate_score([], max_score=100) == 0

    def test_run_test_cases_correct(self, blockly_service):
        """Le code correct doit passer tous les cas de test."""
        code = """
a = 3
b = 5
print(a + b)
"""
        test_cases = [{"inputs": {}, "expected_output": "8"}]
        results = asyncio.get_event_loop().run_until_complete(
            blockly_service.run_test_cases(code, test_cases)
        )
        assert len(results) == 1
        assert results[0].passed is True

    def test_run_test_cases_wrong_output(self, blockly_service):
        """Un code avec mauvais résultat doit échouer les tests."""
        code = "print(42)"
        test_cases = [{"inputs": {}, "expected_output": "8"}]
        results = asyncio.get_event_loop().run_until_complete(
            blockly_service.run_test_cases(code, test_cases)
        )
        assert results[0].passed is False
        assert results[0].got == "42"
        assert results[0].expected == "8"

    def test_run_test_cases_with_inputs(self, blockly_service):
        """Les variables d'entrée doivent être injectées dans le namespace."""
        code = "print(a + b)"
        test_cases = [{"inputs": {"a": 10, "b": 20}, "expected_output": "30"}]
        results = asyncio.get_event_loop().run_until_complete(
            blockly_service.run_test_cases(code, test_cases)
        )
        assert results[0].passed is True


# ─── Tests API (Integration) ──────────────────────────────────────────────────

class TestBlocklyAPI:
    """
    Tests d'intégration pour les endpoints FastAPI.
    Nécessite une base de test configurée.
    """

    SAMPLE_PAYLOAD = {
        "assignment_id": "test-assignment-001",
        "python_code": "print(3 + 5)",
        "blocks_json": "<xml></xml>"
    }

    def test_test_endpoint_returns_200(self, client_with_auth):
        """POST /api/blockly/test doit retourner 200."""
        response = client_with_auth.post("/api/blockly/test", json=self.SAMPLE_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        assert "stdout" in data

    def test_test_endpoint_captures_output(self, client_with_auth):
        """La sortie du programme doit être capturée."""
        payload = {**self.SAMPLE_PAYLOAD, "python_code": "print('hello')"}
        response = client_with_auth.post("/api/blockly/test", json=payload)
        assert response.status_code == 200
        assert response.json()["stdout"].strip() == "hello"

    def test_test_endpoint_empty_code_fails(self, client_with_auth):
        """Un code vide doit retourner une erreur de validation."""
        payload = {**self.SAMPLE_PAYLOAD, "python_code": ""}
        response = client_with_auth.post("/api/blockly/test", json=payload)
        assert response.status_code == 422  # Validation Pydantic

    def test_test_endpoint_unauthenticated(self, client):
        """Sans token, l'accès doit être refusé (401)."""
        response = client.post("/api/blockly/test", json=self.SAMPLE_PAYLOAD)
        assert response.status_code == 401


# ─── Exemple complet bout-en-bout ────────────────────────────────────────────

class TestEndToEndExample:
    """
    Exemple complet : l'étudiant crée un programme de somme avec Blockly.
    """

    def test_complete_blockly_workflow(self):
        """
        Scénario : 
        1. Code Python généré par Blockly pour calculer a + b
        2. Exécution en sandbox
        3. Comparaison avec le résultat attendu
        4. Calcul du score
        """
        executor = PythonExecutor()
        service = BlocklyService(MagicMock())

        # Code généré par Blockly.Python (équivalent de blocs drag-and-drop)
        blockly_generated_python = """
# Code généré automatiquement par Blockly
a = 3
b = 5
print(a + b)
"""
        # Étape 1 : Exécution
        result = asyncio.get_event_loop().run_until_complete(
            executor.execute(blockly_generated_python)
        )
        assert result.stdout.strip() == "8"
        assert result.error is None

        # Étape 2 : Cas de test
        test_cases = [
            {"inputs": {}, "expected_output": "8"},
        ]
        test_results = asyncio.get_event_loop().run_until_complete(
            service.run_test_cases(blockly_generated_python, test_cases)
        )
        assert test_results[0].passed is True

        # Étape 3 : Score
        score = service.calculate_score(test_results, max_score=100)
        assert score == 100

        print(f"\n✅ Test bout-en-bout réussi ! Score : {score}/100")