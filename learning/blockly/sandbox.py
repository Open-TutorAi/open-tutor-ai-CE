"""
Sandbox Python isolé — exécution sécurisée via Piston (US-B04).

FIX #4 : remplacement du subprocess par Piston Docker.

Ancienne version : subprocess.run() dans le processus serveur
  → timeout non garanti (le thread continue après wait_for)
  → pas d'isolation réseau ni filesystem

Nouvelle version : Piston via HTTP
  → container Docker isolé par soumission
  → timeout garanti (container tué par l'OS)
  → réseau désactivé, filesystem isolé
  → compatible cgroups v2 (Ubuntu 22+)

Configuration :
  Local dev  → PISTON_URL=http://localhost:2000 (défaut)
  Docker     → PISTON_URL=http://piston:2000 (via env var)
"""
import os
import time

import httpx

PISTON_URL = os.getenv("PISTON_URL", "http://localhost:2000")
PYTHON_VERSION = "3.10.0"
TIMEOUT_SECONDS = 5


def execute_python(code: str, timeout: int = TIMEOUT_SECONDS) -> dict:
    """
    Exécute du code Python dans un container Piston isolé.

    Args:
        code    : code Python à exécuter
        timeout : délai maximum en secondes (défaut 5)

    Returns:
        dict {
            stdout            : str | None
            stderr            : str | None
            error             : str | None   (None si succès)
            timed_out         : bool
            execution_time_ms : float | None
        }
    """
    start = time.time()
    try:
        # Appel synchrone à Piston — chaque soumission = 1 container Docker
        response = httpx.post(
            f"{PISTON_URL}/api/v2/execute",
            json={
                "language": "python",
                "version": PYTHON_VERSION,
                "files": [{"content": code}],
            },
            timeout=timeout + 5,  # timeout HTTP légèrement supérieur
        )
        response.raise_for_status()
        data = response.json()

        run = data.get("run", {})
        stdout = run.get("stdout") or ""
        stderr = run.get("stderr") or ""
        signal = run.get("signal")
        exit_code = run.get("code", 0)
        wall_time = run.get("wall_time", 0)
        elapsed_ms = round((time.time() - start) * 1000, 1)
        exec_time_ms = wall_time if wall_time else elapsed_ms

        # Timeout détecté via signal SIGKILL
        if signal == "SIGKILL" or (wall_time and wall_time > timeout * 1000):
            return {
                "stdout": None,
                "stderr": None,
                "error": f"⏰ Délai dépassé ({timeout}s) — boucle infinie ?",
                "timed_out": True,
                "execution_time_ms": exec_time_ms,
            }

        # Erreur à l'exécution
        if exit_code != 0:
            friendly = _friendly_error(stderr)
            return {
                "stdout": stdout or None,
                "stderr": stderr or None,
                "error": friendly,
                "timed_out": False,
                "execution_time_ms": exec_time_ms,
            }

        return {
            "stdout": stdout,
            "stderr": stderr or None,
            "error": None,
            "timed_out": False,
            "execution_time_ms": exec_time_ms,
        }

    except httpx.ConnectError:
        return {
            "stdout": None,
            "stderr": None,
            "error": (
                "Service d'exécution indisponible. "
                "Vérifie que Piston est lancé : "
                "docker compose -f docker-compose.piston.yml up -d"
            ),
            "timed_out": False,
            "execution_time_ms": None,
        }
    except Exception as exc:
        return {
            "stdout": None,
            "stderr": None,
            "error": str(exc),
            "timed_out": False,
            "execution_time_ms": round((time.time() - start) * 1000, 1),
        }


def _friendly_error(stderr: str) -> str:
    """Transforme un traceback brut en message lisible pour un débutant."""
    if not stderr.strip():
        return "Erreur inconnue."
    last = stderr.strip().splitlines()[-1]
    if "SyntaxError" in stderr:
        return f"Erreur de syntaxe : {last}"
    if "NameError" in stderr:
        return f"Variable non définie : {last}"
    if "MemoryError" in stderr:
        return "Mémoire insuffisante (limite : 64 Mo)."
    if "RecursionError" in stderr:
        return "Trop d'appels récursifs. Vérifie ta condition d'arrêt."
    if "ZeroDivisionError" in stderr:
        return "Division par zéro dans ton code."
    if "IndentationError" in stderr:
        return f"Erreur d'indentation : {last}"
    if "TypeError" in stderr:
        return f"Mauvais type de valeur : {last}"
    return last