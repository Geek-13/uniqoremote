from __future__ import annotations

from pathlib import Path

from uniqoremote.session.recording import RecordState, RecordingManager, RecordingSession


class TestRecording:
    def test_start_recording(self) -> None:
        mgr = RecordingManager()
        rec = mgr.start("s1", Path("output.mp4"))
        assert rec.session_id == "s1"
        assert rec.output_path == Path("output.mp4")
        assert rec.state == RecordState.RECORDING

    def test_stop_recording(self) -> None:
        mgr = RecordingManager()
        mgr.start("s1", Path("output.mp4"))
        mgr.stop("s1")
        rec = mgr.get_recording("s1")
        assert rec is not None
        assert rec.state == RecordState.FINALIZED

    def test_get_missing(self) -> None:
        mgr = RecordingManager()
        assert mgr.get_recording("nonexistent") is None

    def test_initial_state(self) -> None:
        session = RecordingSession(session_id="s1", output_path=Path("x.mp4"))
        assert session.state == RecordState.IDLE
