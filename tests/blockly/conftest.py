import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """
    TestClient FastAPI pour les tests d'endpoints.
    Appelle create_app() depuis gateway.http.app.
    """
    from gateway.http.app import create_app
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_code():
    """Code Python valide pour les tests."""
    return "print(42)"


@pytest.fixture
def invalid_code():
    """Code Python avec erreur de syntaxe."""
    return "print("
