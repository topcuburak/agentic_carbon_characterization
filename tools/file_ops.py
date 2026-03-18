"""
Sandboxed file I/O operations.
All paths are confined to the sandbox directory.
"""

import os
from pathlib import Path
from config import SANDBOX_DIR


def _resolve_sandbox_path(path: str) -> Path:
    """Resolve a relative path within the sandbox, preventing escape."""
    sandbox = Path(SANDBOX_DIR).resolve()
    target = (sandbox / path).resolve()
    if not str(target).startswith(str(sandbox)):
        raise ValueError(f"Path escapes sandbox: {path}")
    return target


def read_file(path: str) -> str:
    """
    Read a file from the sandbox directory.
    Returns file content as a string.
    """
    try:
        target = _resolve_sandbox_path(path)
        if not target.exists():
            return f"Error: File not found: {path}"
        if not target.is_file():
            return f"Error: Not a file: {path}"

        content = target.read_text(encoding="utf-8", errors="replace")

        if len(content) > 10000:
            content = content[:10000] + "\n... [file truncated, showing first 10000 chars]"

        return content

    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(path: str, content: str) -> str:
    """
    Write content to a file in the sandbox directory.
    Creates parent directories if needed.
    """
    try:
        target = _resolve_sandbox_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"File written successfully: {path} ({len(content)} bytes)"

    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error writing file: {e}"


def list_files(directory: str = ".") -> str:
    """
    List files and directories in a sandbox directory path.
    Returns a formatted listing.
    """
    try:
        target = _resolve_sandbox_path(directory)
        if not target.exists():
            return f"Error: Directory not found: {directory}"
        if not target.is_dir():
            return f"Error: Not a directory: {directory}"

        entries = sorted(os.listdir(target))
        if not entries:
            return f"Directory '{directory}' is empty."

        lines = []
        for entry in entries:
            full = target / entry
            if full.is_dir():
                lines.append(f"  {entry}/")
            else:
                size = full.stat().st_size
                lines.append(f"  {entry} ({size} bytes)")

        return f"Contents of '{directory}':\n" + "\n".join(lines)

    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error listing directory: {e}"
