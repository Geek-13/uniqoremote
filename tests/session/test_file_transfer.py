from __future__ import annotations

from pathlib import Path

import pytest

from uniqoremote.session.file_transfer import FileTransfer


@pytest.mark.asyncio
async def test_file_transfer_on_chunk(tmp_path: Path) -> None:
    FileTransfer.on_chunk(
        {"filename": "test.txt", "data": b"hello world"},
        str(tmp_path),
    )
    result = (tmp_path / "test.txt").read_bytes()
    assert result == b"hello world"


def test_file_transfer_on_chunk_creates_dirs(tmp_path: Path) -> None:
    FileTransfer.on_chunk(
        {"filename": "sub/dir/test.txt", "data": b"nested"},
        str(tmp_path),
    )
    result = (tmp_path / "sub" / "dir" / "test.txt").read_bytes()
    assert result == b"nested"
