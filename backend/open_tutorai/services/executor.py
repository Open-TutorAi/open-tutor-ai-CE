import asyncio
import time
import httpx
from open_tutorai.schemas.blockly import ExecutionResult

PISTON_URL = "http://localhost:2000"
PYTHON_VERSION = "3.10.0"


class Judge0Executor:
    """
    Exécuteur sécurisé via Piston.
    Même interface qu'avant — aucun changement dans blockly_service.py.
    """

    async def execute(self, code: str, stdin: str = "") -> ExecutionResult:
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{PISTON_URL}/api/v2/execute",
                    headers={"Content-Type": "application/json"},
                    json={
                        "language": "python",
                        "version": PYTHON_VERSION,
                        "files": [{"content": code}],
                        "stdin": stdin,
                        "run_timeout": 5000,
                        "compile_timeout": 10000,
                    }
                )
                response.raise_for_status()
                data = response.json()

            elapsed_ms = (time.time() - start) * 1000
            return self._parse_result(data, elapsed_ms)

        except httpx.ConnectError:
            return ExecutionResult(
                error="Service d'exécution indisponible. Contacte ton professeur.",
                execution_time_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ExecutionResult(
                error=f"Erreur interne : {str(e)}",
                execution_time_ms=(time.time() - start) * 1000
            )

    def _parse_result(self, data: dict, elapsed_ms: float) -> ExecutionResult:
        run = data.get("run", {})
        stdout = run.get("stdout") or ""
        stderr = run.get("stderr") or ""
        signal = run.get("signal")
        code = run.get("code", 0)
        wall_time = run.get("wall_time", 0)

        exec_time_ms = wall_time if wall_time else elapsed_ms

        # Timeout
        if signal == "SIGKILL" or wall_time and wall_time > 5000:
            return ExecutionResult(
                error="Délai dépassé : ton programme a pris plus de 5 secondes.",
                timed_out=True,
                execution_time_ms=exec_time_ms,
            )

        # Erreur runtime
        if code != 0:
            return ExecutionResult(
                stdout=stdout,
                stderr=stderr,
                error=self._friendly_error(stderr),
                execution_time_ms=exec_time_ms,
            )

        return ExecutionResult(
            stdout=stdout,
            stderr=stderr,
            execution_time_ms=exec_time_ms,
        )

    @staticmethod
    def _friendly_error(stderr: str) -> str:
        if not stderr.strip():
            return "Erreur inconnue."
        last_line = stderr.strip().splitlines()[-1]
        if "SyntaxError" in stderr:
            return f"Erreur de syntaxe : {last_line}"
        if "NameError" in stderr:
            return f"Variable non définie : {last_line}"
        if "MemoryError" in stderr:
            return "Ton code a utilisé trop de mémoire."
        if "RecursionError" in stderr:
            return "Trop d'appels récursifs. Vérifie ta condition d'arrêt."
        if "ZeroDivisionError" in stderr:
            return "Division par zéro dans ton code."
        if "IndentationError" in stderr:
            return f"Problème d'indentation : {last_line}"
        return last_line
