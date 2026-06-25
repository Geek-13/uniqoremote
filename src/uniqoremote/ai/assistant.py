from __future__ import annotations

from uniqoremote.ai.client import DeepSeekClient


class AIAssistant:
    def __init__(self, client: DeepSeekClient) -> None:
        self._client = client

    async def answer_question(self, screen_text: str, question: str) -> str:
        prompt = f"基于以下屏幕内容回答问题:\n\n[屏幕内容]\n{screen_text}\n\n[问题]\n{question}"
        return await self._client.ask(prompt)

    async def generate_summary(self, screen_text: str) -> str:
        return await self._client.summarize(screen_text)

    async def suggest_action(self, screen_text: str) -> str:
        prompt = f"用户看到以下屏幕内容，请给出建议的下一步操作:\n\n{screen_text}"
        return await self._client.ask(prompt)


class AITranslator:
    def __init__(self, client: DeepSeekClient) -> None:
        self._client = client
        self._cache: dict[str, str] = {}

    async def translate(self, text: str, target_lang: str = "zh") -> str:
        cache_key = f"{text}:{target_lang}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        result = await self._client.translate(text, target_lang)
        self._cache[cache_key] = result
        return result

    async def translate_batch(self, texts: list[str], target_lang: str = "zh") -> list[str]:
        combined = "\n---\n".join(texts)
        result = await self._client.translate(combined, target_lang)
        return result.split("\n---\n")

    def clear_cache(self) -> None:
        self._cache.clear()
