"""Model provider interfaces for optional AI-capable responses."""

from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from typing import Any, Protocol


class ModelProvider(Protocol):
    """Thin interface for text generation providers."""

    name: str

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 512,
    ) -> str:
        """Return model output for a prompt."""


class OfflineProvider:
    """Sentinel provider used when no remote model is configured."""

    name = "offline"

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 512,
    ) -> str:
        raise RuntimeError("No model provider is configured.")


class OllamaProvider:
    """Calls a local Ollama server via the CLI."""

    name = "ollama"

    def __init__(self, model: str = "llama3.1", *, timeout: int = 60) -> None:
        self.model = model
        self.timeout = timeout

    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 512,
    ) -> str:
        if not self.is_available():
            raise RuntimeError("Ollama is not installed or not reachable.")

        command = ["ollama", "run", self.model]
        payload = prompt if system_prompt is None else f"{system_prompt}\n\n{prompt}"
        result = subprocess.run(
            command,
            input=payload,
            text=True,
            capture_output=True,
            timeout=self.timeout,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "ollama call failed").strip()
            raise RuntimeError(f"Ollama request failed: {detail}")
        response = (result.stdout or "").strip()
        if not response:
            raise RuntimeError("Ollama returned an empty response.")
        return response


class OpenAICompatibleProvider:
    """Generic OpenAI-compatible HTTP provider for local or hosted models."""

    name = "openai-compatible"

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        *,
        api_base: str | None = None,
        api_key: str | None = None,
        timeout: int = 60,
    ) -> None:
        self.model = model
        self.api_base = api_base or os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.timeout = timeout

    def _endpoint(self) -> str:
        base = self.api_base.rstrip("/")
        return f"{base}/chat/completions"

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 512,
    ) -> str:
        if not self.api_key and not self.api_base.lower().startswith("http://"):
            raise RuntimeError("OPENAI_API_KEY is not configured for the selected provider.")

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [],
            "max_tokens": max_tokens,
        }
        if system_prompt:
            payload["messages"].append({"role": "system", "content": system_prompt})
        payload["messages"].append({"role": "user", "content": prompt})

        request = urllib.request.Request(
            self._endpoint(),
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        if self.api_key:
            request.add_header("Authorization", f"Bearer {self.api_key}")

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Model request failed ({exc.code}): {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Model endpoint is unreachable: {exc}") from exc

        choices = body.get("choices") or []
        if not choices:
            raise RuntimeError("Model returned no completion choices.")
        message = choices[0].get("message", {})
        content = message.get("content") or ""
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Model returned an empty completion.")
        return content.strip()


def build_provider(
    provider_name: str | None,
    *,
    model: str | None = None,
    api_base: str | None = None,
    api_key: str | None = None,
) -> ModelProvider | None:
    """Build a configured provider, or return None for offline-only mode."""
    name = (provider_name or "offline").strip().casefold()
    if name in {"", "offline", "none"}:
        return None
    if name in {"ollama", "local-ollama", "local_ollama"}:
        return OllamaProvider(model or "llama3.1")
    if name in {"openai", "openai-compatible", "openai_compatible", "openai-compatible-http"}:
        return OpenAICompatibleProvider(
            model or "gpt-4o-mini",
            api_base=api_base,
            api_key=api_key,
        )
    return None
