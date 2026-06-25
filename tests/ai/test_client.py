from __future__ import annotations

import os

import pytest

from uniqoremote.ai.client import AIClient, DeepSeekClient


class TestDeepSeekClient:
    def test_not_configured_without_key(self) -> None:
        client = DeepSeekClient(api_key="")
        assert client.is_configured is False

    def test_ask_returns_placeholder_when_disabled(self) -> None:
        client = DeepSeekClient(api_key="")
        import asyncio

        result = asyncio.run(client.ask("hello"))
        assert "[AI disabled" in result

    def test_configured_with_env_var(self) -> None:
        os.environ["UNIQOREMOTE_AI_API_KEY"] = "sk-test"
        client = DeepSeekClient()
        assert client.is_configured is True
        del os.environ["UNIQOREMOTE_AI_API_KEY"]

    def test_ocr_delegates_to_ask(self) -> None:
        client = DeepSeekClient(api_key="")
        import asyncio

        result = asyncio.run(client.ocr(b"fake"))
        assert "[AI disabled" in result

    def test_translate_delegates_to_ask(self) -> None:
        client = DeepSeekClient(api_key="")
        import asyncio

        result = asyncio.run(client.translate("hallo", "zh"))
        assert "[AI disabled" in result

    def test_summarize_delegates_to_ask(self) -> None:
        client = DeepSeekClient(api_key="")
        import asyncio

        result = asyncio.run(client.summarize("long text"))
        assert "[AI disabled" in result


class TestAIClientABC:
    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            AIClient()  # type: ignore[abstract]
