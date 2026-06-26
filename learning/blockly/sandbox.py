"""
Sandbox Python isolé — exécution sécurisée (US-B04).

Le code étudiant tourne dans un subprocess séparé :
- Isolé du processus serveur
- Tué après `timeout` secondes (anti boucle infinie)
- stdout et stderr capturés séparément
"""
import subprocess
import sys
import tempfile
import os
import time


def execute_python(code: str, timeout: int = 5) -> dict:
    """
    Exécute du code Python dans un processus enfant isolé.

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
    # Écrire dans un fichier temporaire
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(code)
        tmp_path = f.name

    try:
        start = time.time()
        proc = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed_ms = round((time.time() - start) * 1000, 1)

        return {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "error": proc.stderr if proc.returncode != 0 else None,
            "timed_out": False,
            "execution_time_ms": elapsed_ms,
        }

    except subprocess.TimeoutExpired:
        return {
            "stdout": None,
            "stderr": None,
            "error": f"⏰ Délai dépassé ({timeout}s) — boucle infinie ?",
            "timed_out": True,
            "execution_time_ms": None,
        }

    except Exception as exc:
        return {
            "stdout": None,
            "stderr": None,
            "error": str(exc),
            "timed_out": False,
            "execution_time_ms": None,
        }

    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass