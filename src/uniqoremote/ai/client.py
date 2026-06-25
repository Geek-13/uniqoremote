from __future__ import annotations

import os
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


class DeepSeekClient(AIClient):
    def __init__(self, api_key: str | None = None, model: str = "deepseek-chat") -> None:
        self._api_key = api_key or os.environ.get("UNIQOREMOTE_AI_API_KEY", "")
        self._model = model
        self._base_url = "https://api.deepseek.com"

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    async def ask(self, prompt: str, image: bytes | None = None) -> str:
        if not self.is_configured:
            return "[AI disabled: no API key configured]"
        try:
            import litellm  # type: ignore[import-not-found]

            messages: list[dict[str, str]] = [{"role": "user", "content": prompt}]
            response = await litellm.acompletion(
                model=f"openai/{self._model}",
                messages=messages,
                api_key=self._api_key,
                api_base=self._base_url,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[AI error: {e}]"

    async def ocr(self, image: bytes) -> str:
        return await self.ask("请提取并输出这张图片中的所有文字，只输出文字内容。")

    async def translate(self, text: str, target_lang: str = "zh") -> str:
        return await self.ask(f"请将以下文本翻译为{target_lang}，只输出翻译结果:\n{text}")

    async def summarize(self, context: str) -> str:
        return await self.ask(f"请用简短的语言总结以下内容:\n{context}")
