from __future__ import annotations

import pytest

from uniqoremote.session.terminal import RemoteTerminal, TerminalResult


class TestRemoteTerminal:
    def test_execute_echo(self) -> None:
        term = RemoteTerminal()
        result = term.execute("echo hello")
        assert "hello" in result.stdout
        assert result.exit_code == 0

    def test_execute_failing_command(self) -> None:
        term = RemoteTerminal()
        result = term.execute("exit 1")
        assert result.exit_code != 0

    def test_terminal_result_fields(self) -> None:
        r = TerminalResult(stdout="out", stderr="err", exit_code=0)
        assert r.stdout == "out"
        assert r.stderr == "err"

    @pytest.mark.asyncio
    async def test_execute_async(self) -> None:
        term = RemoteTerminal()
        result = await term.execute_async("echo async")
        assert "async" in result.stdout
