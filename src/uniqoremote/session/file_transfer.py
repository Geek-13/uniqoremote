from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class TransferState(StrEnum):
    PENDING = "pending"
    TRANSFERRING = "transferring"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class FileTransfer:
    transfer_id: str
    filename: str
    size: int
    state: TransferState = TransferState.PENDING
    progress: int = 0
    local_path: Path | None = None


class FileTransferManager:
    def __init__(self, chunk_size: int = 65536) -> None:
        self._transfers: dict[str, FileTransfer] = {}
        self._chunk_size = chunk_size

    def create_transfer(self, transfer_id: str, filename: str, size: int) -> FileTransfer:
        transfer = FileTransfer(transfer_id=transfer_id, filename=filename, size=size)
        self._transfers[transfer_id] = transfer
        return transfer

    def get_transfer(self, transfer_id: str) -> FileTransfer | None:
        return self._transfers.get(transfer_id)

    def update_progress(self, transfer_id: str, progress: int) -> None:
        transfer = self._transfers.get(transfer_id)
        if transfer is None:
            raise KeyError(f"Transfer {transfer_id} not found")
        transfer.progress = progress
        if progress >= transfer.size:
            transfer.state = TransferState.COMPLETED

    def remove_transfer(self, transfer_id: str) -> None:
        self._transfers.pop(transfer_id, None)
