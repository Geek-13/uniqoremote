from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class TerminalResult:
    stdout: str
    stderr: str
    exit_code: int


class RemoteTerminal:
    def __init__(self, shell: str = "cmd.exe") -> None:
        self._shell = shell

    def execute(self, command: str, timeout: int = 30) -> TerminalResult:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=None,
            )
            return TerminalResult(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
            )
        except subprocess.TimeoutExpired as e:
            return TerminalResult(
                stdout=e.stdout or "",
                stderr=e.stderr or "",
                exit_code=-1,
            )

    async def execute_async(self, command: str, timeout: int = 30) -> TerminalResult:
        import asyncio

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            assert isinstance(stdout_b, bytes)
            assert isinstance(stderr_b, bytes)
            return TerminalResult(
                stdout=stdout_b.decode("utf-8", errors="replace") if stdout_b else "",
                stderr=stderr_b.decode("utf-8", errors="replace") if stderr_b else "",
                exit_code=proc.returncode or 0,
            )
        except TimeoutError:
            return TerminalResult(stdout="", stderr="Command timed out", exit_code=-1)
