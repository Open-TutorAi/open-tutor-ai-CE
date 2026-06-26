from learning.blockly.sandbox import execute_python


class TestExecutePython:
    """Tests unitaires du sandbox Python isolé."""

    def test_print_simple(self):
        """stdout correct pour print(42)."""
        result = execute_python("print(42)")
        assert result["stdout"].strip() == "42"
        assert result["error"] is None
        assert result["timed_out"] is False
        assert result["execution_time_ms"] is not None

    def test_arithmetic(self):
        """Calcul arithmétique 3+5 = 8."""
        result = execute_python("print(3 + 5)")
        assert result["stdout"].strip() == "8"

    def test_variable_assignment(self):
        """Variables et modification (patron Blockly)."""
        code = "x = 10\nx = x + 4\nprint(x)"
        result = execute_python(code)
        assert result["stdout"].strip() == "14"
        assert result["timed_out"] is False

    def test_multiline_output(self):
        """Boucle for produit plusieurs lignes."""
        code = "for i in range(3):\n    print(i)"
        result = execute_python(code)
        lines = result["stdout"].strip().split("\n")
        assert lines == ["0", "1", "2"]

    def test_syntax_error_captured(self):
        """Erreur de syntaxe : error non None, pas de crash."""
        result = execute_python("print(")
        assert result["error"] is not None
        assert result["timed_out"] is False

    def test_runtime_error_captured(self):
        """Division par zéro : stderr capturé."""
        result = execute_python("print(1 / 0)")
        assert result["error"] is not None

    def test_infinite_loop_killed(self):
        """Boucle infinie tuée après timeout."""
        result = execute_python("while True: pass", timeout=2)
        assert result["timed_out"] is True
        assert result["error"] is not None

    def test_stderr_captured(self):
        """stderr écrit manuellement est capturé."""
        code = "import sys; sys.stderr.write('erreur_test')"
        result = execute_python(code)
        assert "erreur_test" in (result["stderr"] or "")

    def test_empty_code_no_crash(self):
        """Code vide : pas de plantage."""
        result = execute_python("")
        assert result["timed_out"] is False

    def test_execution_time_positive(self):
        """Temps d'exécution mesuré et positif."""
        result = execute_python("print('ok')")
        assert result["execution_time_ms"] >= 0

