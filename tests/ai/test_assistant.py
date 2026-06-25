from __future__ import annotations

import asyncio
import os

import pytest

from uniqoremote.ai.assistant import AIAssistant, AITranslator
from uniqoremote.ai.client import DeepSeekClient


@pytest.fixture
def disabled_client() -> DeepSeekClient:
    return DeepSeekClient(api_key="")


class TestAIAssistant:
    @pytest.mark.asyncio
    async def test_answer_question_placeholder(self, disabled_client) -> None:
        assistant = AIAssistant(disabled_client)
        result = await assistant.answer_question("screen text", "what is this?")
        assert "[AI disabled" in result

    @pytest.mark.asyncio
    async def test_generate_summary_placeholder(self, disabled_client) -> None:
        assistant = AIAssistant(disabled_client)
        result = await assistant.generate_summary("long screen content")
        assert "[AI disabled" in result

    @pytest.mark.asyncio
    async def test_suggest_action_placeholder(self, disabled_client) -> None:
        assistant = AIAssistant(disabled_client)
        result = await assistant.suggest_action("error dialog")
        assert "[AI disabled" in result


class TestAITranslator:
    @pytest.mark.asyncio
    async def test_translate_placeholder(self, disabled_client) -> None:
        translator = AITranslator(disabled_client)
        result = await translator.translate("hello", "zh")
        assert "[AI disabled" in result

    def test_cache_clear(self, disabled_client) -> None:
        translator = AITranslator(disabled_client)
        translator._cache["key"] = "val"
        translator.clear_cache()
        assert len(translator._cache) == 0
