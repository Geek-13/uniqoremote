from __future__ import annotations

import pytest

from uniqoremote.ai.client import AIClient


class MockAIClient(AIClient):
    async def ask(self, prompt: str, image: bytes | None = None) -> str:
        return f"answer: {prompt}"

    async def ocr(self, image: bytes) -> str:
        return "extracted text"

    async def translate(self, text: str, target_lang: str = "zh") -> str:
        return f"[{target_lang}] {text}"

    async def summarize(self, context: str) -> str:
        return f"summary: {context[:50]}"


class TestAIClient:
    def test_cannot_instantiate_abc(self) -> None:
        with pytest.raises(TypeError):
            AIClient()  # type: ignore[abstract]

    @pytest.mark.asyncio
    async def test_mock_ask(self) -> None:
        client = MockAIClient()
        result = await client.ask("what is this?")
        assert result == "answer: what is this?"

    @pytest.mark.asyncio
    async def test_mock_ocr(self) -> None:
        client = MockAIClient()
        result = await client.ocr(b"fake image data")
        assert result == "extracted text"

    @pytest.mark.asyncio
    async def test_mock_translate(self) -> None:
        client = MockAIClient()
        result = await client.translate("hello", "zh")
        assert result == "[zh] hello"

    @pytest.mark.asyncio
    async def test_mock_summarize(self) -> None:
        client = MockAIClient()
        result = await client.summarize("long context " * 100)
        assert result.startswith("summary:")
