from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class RecordState(StrEnum):
    IDLE = "idle"
    RECORDING = "recording"
    PAUSED = "paused"
    FINALIZED = "finalized"


@dataclass
class RecordingSession:
    session_id: str
    output_path: Path
    state: RecordState = RecordState.IDLE
    duration_seconds: float = 0.0


class RecordingManager:
    def __init__(self) -> None:
        self._recordings: dict[str, RecordingSession] = {}

    def start(self, session_id: str, output_path: Path) -> RecordingSession:
        recording = RecordingSession(
            session_id=session_id,
            output_path=output_path,
            state=RecordState.RECORDING,
        )
        self._recordings[session_id] = recording
        return recording

    def stop(self, session_id: str) -> None:
        recording = self._recordings.get(session_id)
        if recording is not None:
            recording.state = RecordState.FINALIZED

    def get_recording(self, session_id: str) -> RecordingSession | None:
        return self._recordings.get(session_id)
