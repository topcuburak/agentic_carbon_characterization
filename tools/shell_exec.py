"""
Sandboxed shell command execution tool.
Only whitelisted commands are allowed.
"""

import subprocess
import shlex
from config import SANDBOX_DIR, SHELL_WHITELIST


def shell_exec(command: str) -> str:
    """
    Execute a shell command in a sandboxed environment.
    Only whitelisted commands are permitted.
    Returns stdout and stderr.
    """
    timeout_s = 30

    try:
        parts = shlex.split(command)
    except ValueError as e:
        return f"Error parsing command: {e}"

    if not parts:
        return "Error: Empty command."

    base_cmd = parts[0]
    # Strip path prefix (e.g., /usr/bin/ls -> ls)
    base_cmd = base_cmd.rsplit("/", 1)[-1]

    if base_cmd not in SHELL_WHITELIST:
        return f"Error: Command '{base_cmd}' is not allowed. Permitted commands: {', '.join(sorted(SHELL_WHITELIST))}"

    try:
        result = subprocess.run(
            parts,
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

        if len(output) > 5000:
            output = output[:5000] + "\n... [output truncated]"

        return output

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout_s} seconds."
    except Exception as e:
        return f"Error executing command: {e}"
