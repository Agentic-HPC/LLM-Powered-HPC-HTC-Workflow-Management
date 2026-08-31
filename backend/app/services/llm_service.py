"""
Provider-agnostic LLM facade used by all agents.

Set LLM_PROVIDER=groq (default) to use Groq's hosted inference API. Set
LLM_PROVIDER=openai to use OpenAI's API instead (requires
OPENAI_API_KEY). Groq is a good fit for a student project
because it's fast and has a generous free tier. Agents only ever call
`llm_service.generate_json(...)` /
`llm_service.generate(...)` and don't need to know which provider is active.
"""
from typing import Any, Dict, Optional

from app.core.config import settings
class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER

    async def generate(self, prompt: str, system: Optional[str] = None) -> str:
        if self.provider == "openai":
            return await self._openai_generate(prompt, system=system)
        elif self.provider == "groq":
            return await self._groq_generate(prompt, system=system)
        raise ValueError(f"Unknown LLM_PROVIDER: {self.provider}")

    async def generate_json(self, prompt: str, system: Optional[str] = None) -> Dict[str, Any]:
        if self.provider == "openai":
            return await self._openai_generate_json(prompt, system=system)
        elif self.provider == "groq":
            return await self._groq_generate_json(prompt, system=system)
        raise ValueError(f"Unknown LLM_PROVIDER: {self.provider}")

    async def health_check(self) -> Dict[str, Any]:
        if self.provider == "groq":
            return {"reachable": bool(settings.GROQ_API_KEY), "provider": "groq", "model": settings.GROQ_MODEL}
        return {"reachable": bool(settings.OPENAI_API_KEY), "provider": "openai"}

    # --- Groq path (OpenAI-compatible chat completions API) ---
    def _groq_client(self):
        try:
            from groq import AsyncGroq
        except ImportError as exc:
            raise RuntimeError("groq package not installed; add it to requirements.txt") from exc
        if not settings.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to backend/.env "
                "(never commit it or paste it in chat/code)."
            )
        return AsyncGroq(api_key=settings.GROQ_API_KEY)

    async def _groq_generate(self, prompt: str, system: Optional[str] = None) -> str:
        client = self._groq_client()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            temperature=0.2,
        )
        return resp.choices[0].message.content or ""

    async def _groq_generate_json(self, prompt: str, system: Optional[str] = None) -> Dict[str, Any]:
        import json
        import re

        client = self._groq_client()
        json_system = (
            (system or "")
            + "\nYou must respond with ONLY valid JSON. No markdown fences, "
            "no commentary, no explanation before or after the JSON object."
        ).strip()
        messages = [{"role": "system", "content": json_system}, {"role": "user", "content": prompt}]
        resp = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or ""
        text = raw.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise ValueError(f"Groq did not return valid JSON: {raw[:300]}")

    # --- OpenAI fallback path (optional, only used if LLM_PROVIDER=openai) ---
    async def _openai_generate(self, prompt: str, system: Optional[str] = None) -> str:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise RuntimeError("openai package not installed; add it to requirements.txt") from exc

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = await client.chat.completions.create(model=settings.OPENAI_MODEL, messages=messages)
        return resp.choices[0].message.content or ""

    async def _openai_generate_json(self, prompt: str, system: Optional[str] = None) -> Dict[str, Any]:
        import json
        raw = await self._openai_generate(
            prompt, system=(system or "") + "\nRespond with ONLY valid JSON."
        )
        return json.loads(raw)


llm_service = LLMService()

__all__ = ["llm_service", "LLMService"]
