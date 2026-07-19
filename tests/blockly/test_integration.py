class TestExecuteFlows:
    """Flux d'exécution complets."""

    def test_variable_compute_and_print(self, client):
        """x=10, x+=4, print(x) → stdout='14'."""
        resp = client.post(
            "/api/blockly/execute",
            json={"python_code": "x = 10\nx = x + 4\nprint(x)", "level": "beginner"},
        )
        assert resp.status_code == 200
        assert resp.json()["stdout"].strip() == "14"
        assert resp.json()["error"] is None

    def test_execute_then_submit(self, client):
        """Exécute d'abord, puis soumet la même solution."""
        code = "print(42)"

        exec_resp = client.post("/api/blockly/execute", json={"python_code": code})
        assert exec_resp.status_code == 200
        assert exec_resp.json()["stdout"].strip() == "42"

        submit_resp = client.post(
            "/api/blockly/submit",
            json={"python_code": code, "level": "beginner"},
        )
        assert submit_resp.status_code == 200
        assert "score" in submit_resp.text

    def test_timeout_protection_sleep(self, client):
        """sleep(100) est tué par le timeout."""
        resp = client.post(
            "/api/blockly/execute",
            json={"python_code": "import time; time.sleep(100)"},
        )
        assert resp.status_code == 200
        assert resp.json()["timed_out"] is True

    def test_timeout_protection_infinite_loop(self, client):
        """while True est tué par le timeout."""
        resp = client.post(
            "/api/blockly/execute",
            json={"python_code": "while True: pass"},
        )
        assert resp.status_code == 200
        assert resp.json()["timed_out"] is True


class TestSecurityIntegration:
    """Tests de sécurité transversaux."""

    def test_invalid_level_rejected_execute(self, client):
        """level invalide rejeté par /execute."""
        resp = client.post(
            "/api/blockly/execute",
            json={"python_code": "print(1)", "level": "root"},
        )
        assert resp.status_code == 422

    def test_invalid_level_rejected_submit(self, client):
        """level invalide rejeté par /submit."""
        resp = client.post(
            "/api/blockly/submit",
            json={"python_code": "print(1)", "level": "admin"},
        )
        assert resp.status_code == 422

    def test_invalid_level_rejected_generate(self, client):
        """level invalide rejeté par /generate/stream."""
        resp = client.post(
            "/api/blockly/generate/stream",
            json={"level": "superuser", "course": "Python"},
        )
        assert resp.status_code == 422

    def test_code_max_length_rejected(self, client):
        """Code > 10 000 chars rejeté."""
        resp = client.post(
            "/api/blockly/execute",
            json={"python_code": "x" * 10_001},
        )
        assert resp.status_code == 422


class TestWorkspaceFlow:
    """Flux sauvegarde + chargement workspace (US-B07)."""

    def test_save_and_load(self, client):
        """Sauvegarde puis chargement du même workspace."""
        xml = "<xml><block type='text_print'></block></xml>"
        aid = "flow-test-001"

        save_resp = client.post(
            "/api/blockly/workspace/save",
            json={"assignment_id": aid, "workspace_xml": xml},
        )
        assert save_resp.status_code == 200
        assert save_resp.json()["status"] == "saved"

        load_resp = client.get(f"/api/blockly/workspace/{aid}")
        assert load_resp.status_code == 200
        assert load_resp.json()["assignment_id"] == aid

    def test_generate_for_all_levels(self, client):
        """Génération d'exercice pour chaque niveau valide."""
        for level in ["beginner", "intermediate", "advanced"]:
            resp = client.post(
                "/api/blockly/generate/stream",
                json={"level": level, "course": "Python"},
            )
            assert resp.status_code == 200

