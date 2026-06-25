from __future__ import annotations

from uniqoremote.session.file_transfer import FileTransferManager, TransferState


class TestFileTransfer:
    def test_create_transfer(self) -> None:
        mgr = FileTransferManager()
        transfer = mgr.create_transfer("t1", "test.zip", 1024000)
        assert transfer.transfer_id == "t1"
        assert transfer.filename == "test.zip"
        assert transfer.size == 1024000
        assert transfer.state == TransferState.PENDING

    def test_progress_update(self) -> None:
        mgr = FileTransferManager()
        mgr.create_transfer("t1", "file.bin", 1000)
        mgr.update_progress("t1", 500)
        t = mgr.get_transfer("t1")
        assert t is not None
        assert t.progress == 500
        assert t.state == TransferState.PENDING

    def test_completion_on_full_progress(self) -> None:
        mgr = FileTransferManager()
        mgr.create_transfer("t1", "file.bin", 1000)
        mgr.update_progress("t1", 1000)
        t = mgr.get_transfer("t1")
        assert t is not None
        assert t.state == TransferState.COMPLETED

    def test_remove_transfer(self) -> None:
        mgr = FileTransferManager()
        mgr.create_transfer("t1", "x", 100)
        mgr.remove_transfer("t1")
        assert mgr.get_transfer("t1") is None


class TestTransferState:
    def test_enum_values(self) -> None:
        assert TransferState.PENDING == "pending"
        assert TransferState.TRANSFERRING == "transferring"
        assert TransferState.COMPLETED == "completed"
        assert TransferState.ERROR == "error"
