from __future__ import annotations


class OCRClient:
    def __init__(self) -> None:
        self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    async def recognize(self, image: bytes) -> str:
        return "[OCR: PaddleOCR not installed]"
