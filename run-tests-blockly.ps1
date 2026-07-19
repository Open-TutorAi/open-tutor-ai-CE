Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "TESTS MODULE BLOCKLY — OpenTutorAI" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════" -ForegroundColor Cyan

# Créer conftest.py si manquant
if (-not (Test-Path tests\blockly\conftest.py)) {
    @"
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from gateway.http.app import app
    return TestClient(app)
"@ | Out-File -FilePath tests\blockly\conftest.py -Encoding utf8
    Write-Host "✅ conftest.py créé" -ForegroundColor Green
}

Write-Host "`n[ÉTAPE 4a] Tests Sandbox" -ForegroundColor Yellow
.\.venv\Scripts\python.exe -m pytest tests/blockly/test_sandbox.py -v --tb=short

Write-Host "`n[ÉTAPE 4b] Tests Progression" -ForegroundColor Yellow
.\.venv\Scripts\python.exe -m pytest tests/blockly/test_progression.py -v --tb=short

Write-Host "`n[ÉTAPE 5a] Tests Router" -ForegroundColor Yellow
.\.venv\Scripts\python.exe -m pytest tests/blockly/test_router.py -v --tb=short

Write-Host "`n[ÉTAPE 5b] Tests Intégration" -ForegroundColor Yellow
.\.venv\Scripts\python.exe -m pytest tests/blockly/test_integration.py -v --tb=short

Write-Host "`n[RÉSUMÉ] Tous les Tests" -ForegroundColor Yellow
.\.venv\Scripts\python.exe -m pytest tests/blockly/ -v --tb=short

Write-Host "`n✅ TESTS TERMINÉS" -ForegroundColor Green
