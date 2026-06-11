import subprocess, sys, tempfile, os, time

def execute_python(code: str, timeout: int = 5) -> dict:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        tmp_path = f.name
    try:
        start = time.time()
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True, text=True,
            timeout=timeout
        )
        elapsed = round((time.time() - start) * 1000, 1)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "error": result.stderr if result.returncode != 0 else None,
            "timed_out": False,
            "execution_time_ms": elapsed
        }
    except subprocess.TimeoutExpired:
        return {"stdout": None, "stderr": None,
                "error": f"Delai depasse ({timeout}s)",
                "timed_out": True, "execution_time_ms": None}
    except Exception as e:
        return {"stdout": None, "stderr": None,
                "error": str(e), "timed_out": False, "execution_time_ms": None}
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass
