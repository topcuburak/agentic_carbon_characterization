"""
Sandboxed Python code execution tool.
Runs code in an isolated subprocess with timeout.
"""

import subprocess
import tempfile
import os
from config import SANDBOX_DIR


def python_exec(code: str) -> str:
    """
    Execute Python code in an isolated subprocess.
    Returns stdout and stderr combined.
    """
    timeout_s = 30

    # Write code to a temp file in the sandbox
    os.makedirs(SANDBOX_DIR, exist_ok=True)
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", dir=SANDBOX_DIR, delete=False
    )
    try:
        tmp.write(code)
        tmp.close()

        result = subprocess.run(
            ["python3", tmp.name],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            cwd=str(SANDBOX_DIR),
        )

        output_parts = []
        if result.stdout:
            output_parts.append(result.stdout)
        if result.stderr:
            output_parts.append(f"[stderr]\n{result.stderr}")
        if result.returncode != 0:
            output_parts.append(f"[exit code: {result.returncode}]")

        output = "\n".join(output_parts) if output_parts else "(no output)"

        # Truncate very long outputs
        if len(output) > 5000:
            output = output[:5000] + "\n... [output truncated]"

        return output

    except subprocess.TimeoutExpired:
        return f"Error: Code execution timed out after {timeout_s} seconds."
    except Exception as e:
        return f"Error executing code: {e}"
    finally:
        os.unlink(tmp.name)
