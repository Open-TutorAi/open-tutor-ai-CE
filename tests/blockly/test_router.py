
class TestExecuteEndpoint:
    """Tests de POST /api/blockly/execute."""

    def test_execute_simple_print(self, client):
        """Code print(42) → stdout='42'."""
        resp = client.post("/api/blockly/execute", json={"python_code": "print(42)"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["stdout"].strip() == "42"
        assert data["error"] is None
        assert data["timed_out"] is False

    def test_execute_no_code_returns_422(self, client):
        """Requête sans python_code → 422 Unprocessable."""
        resp = client.post("/api/blockly/execute", json={})
        assert resp.status_code == 422

    def test_execute_code_too_long_returns_422(self, client):
        """Code > 10 000 caractères → 422."""
        resp = client.post("/api/blockly/execute", json={"python_code": "x" * 10_001})
        assert resp.status_code == 422

    def test_execute_invalid_level_returns_422(self, client):
        """level non autorisé → 422."""
        resp = client.post(
            "/api/blockly/execute",
            json={"python_code": "print(1)", "level": "super_admin"},
        )
        assert resp.status_code == 422

    def test_execute_infinite_loop_timed_out(self, client):
        """Boucle infinie → timed_out=True."""
        resp = client.post("/api/blockly/execute", json={"python_code": "while True: pass"})
        assert resp.status_code == 200
        assert resp.json()["timed_out"] is True

    def test_execute_arithmetic(self, client):
        """3 + 5 = 8."""
        resp = client.post("/api/blockly/execute", json={"python_code": "print(3+5)"})
        assert resp.status_code == 200
        assert resp.json()["stdout"].strip() == "8"


class TestSubmitEndpoint:
    """Tests de POST /api/blockly/submit."""

    def test_submit_returns_event_stream(self, client):
        """Retourne content-type text/event-stream."""
        resp = client.post(
            "/api/blockly/submit",
            json={"python_code": "print(8)", "level": "beginner"},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

    def test_submit_contains_score_event(self, client):
        """Le stream contient un événement score."""
        resp = client.post(
            "/api/blockly/submit",
            json={"python_code": "print(8)", "level": "beginner"},
        )
        assert "score" in resp.text

    def test_submit_invalid_level_returns_422(self, client):
        """level invalide → 422."""
        resp = client.post(
            "/api/blockly/submit",
            json={"python_code": "print(1)", "level": "HACK"},
        )
        assert resp.status_code == 422


class TestGenerateEndpoint:
    """Tests de POST /api/blockly/generate/stream."""

    def test_generate_returns_event_stream(self, client):
        """Retourne content-type text/event-stream."""
        resp = client.post(
            "/api/blockly/generate/stream",
            json={"level": "beginner", "course": "Python"},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

    def test_generate_all_levels(self, client):
        """Chaque niveau valide retourne 200."""
        for level in ["beginner", "intermediate", "advanced"]:
            resp = client.post(
                "/api/blockly/generate/stream",
                json={"level": level, "course": "Python"},
            )
            assert resp.status_code == 200

    def test_generate_with_full_context(self, client):
        """Génération avec tous les champs → 200."""
        resp = client.post(
            "/api/blockly/generate/stream",
            json={
                "level": "beginner",
                "course": "Variables Python",
                "objectives": "Comprendre print()",
                "prerequisites": "Aucun",
            },
        )
        assert resp.status_code == 200

    def test_generate_course_too_long_returns_422(self, client):
        """course > 255 caractères → 422."""
        resp = client.post(
            "/api/blockly/generate/stream",
            json={"level": "beginner", "course": "x" * 256},
        )
        assert resp.status_code == 422

    def test_generate_invalid_level_returns_422(self, client):
        """level invalide → 422."""
        resp = client.post(
            "/api/blockly/generate/stream",
            json={"level": "master", "course": "Python"},
        )
        assert resp.status_code == 422


class TestWorkspaceEndpoints:
    """Tests de /workspace/save et /workspace/{id}."""

    def test_save_workspace_returns_saved(self, client):
        """Sauvegarde → status='saved'."""
        resp = client.post(
            "/api/blockly/workspace/save",
            json={
                "assignment_id": "abc-123",
                "workspace_xml": "<xml></xml>",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "saved"

    def test_load_workspace_returns_assignment_id(self, client):
        """Chargement → assignment_id dans la réponse."""
        resp = client.get("/api/blockly/workspace/abc-123")
        assert resp.status_code == 200
        assert resp.json()["assignment_id"] == "abc-123"

    def test_load_workspace_id_too_long_returns_422(self, client):
        """ID > 36 caractères → 422."""
        resp = client.get(f"/api/blockly/workspace/{'x' * 37}")
        assert resp.status_code == 422
