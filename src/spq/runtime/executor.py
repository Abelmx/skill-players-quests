"""Real execution of generic tools (bash, read_file, write_file)."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes tool calls using async subprocess and file I/O.

    No sandbox management -- isolation is provided externally
    (e.g. GitHub Actions container).
    """

    def __init__(self, timeout: int = 30, work_dir: str | None = None) -> None:
        self.timeout = timeout
        self.work_dir = work_dir

    _KNOWN_PARAMS: dict[str, set[str]] = {
        "read_file": {"path"},
        "bash": {"command"},
        "write_file": {"path", "content"},
    }

    async def execute(self, tool_name: str, arguments: dict) -> str:
        handler = {
            "read_file": self._read_file,
            "bash": self._bash,
            "write_file": self._write_file,
        }.get(tool_name)

        if handler is None:
            return f"Error: unknown tool '{tool_name}'"

        known = self._KNOWN_PARAMS.get(tool_name, set())
        filtered = {k: v for k, v in arguments.items() if k in known} if known else arguments

        try:
            return await handler(**filtered)
        except Exception as e:
            logger.error("Tool %s failed: %s", tool_name, e)
            return f"Error: {e}"

    async def _read_file(self, path: str) -> str:
        p = Path(path)
        if not p.exists():
            return f"Error: file not found: {path}"
        try:
            return p.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading file: {e}"

    async def _bash(self, command: str) -> str:
        logger.info("Executing: %s", command[:200])
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.work_dir,
            )
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(), timeout=self.timeout,
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                return f"Error: command timed out after {self.timeout}s"

            stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
            stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""

            output = ""
            if stdout:
                output += stdout
            if stderr:
                output += ("\n" if output else "") + stderr
            if proc.returncode and proc.returncode != 0:
                output += f"\n[exit code: {proc.returncode}]"
            return output.strip() or "(no output)"
        except Exception as e:
            return f"Error executing command: {e}"

    async def _write_file(self, path: str, content: str) -> str:
        p = Path(path)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return f"Successfully wrote {len(content)} bytes to {path}"
        except Exception as e:
            return f"Error writing file: {e}"
