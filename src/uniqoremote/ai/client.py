from __future__ import annotations

from abc import ABC, abstractmethod


class AIClient(ABC):
    @abstractmethod
    async def ask(self, prompt: str, image: bytes | None = None) -> str: ...

    @abstractmethod
    async def ocr(self, image: bytes) -> str: ...

    @abstractmethod
    async def translate(self, text: str, target_lang: str = "zh") -> str: ...

    @abstractmethod
    async def summarize(self, context: str) -> str: ...
