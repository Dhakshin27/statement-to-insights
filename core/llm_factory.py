"""
Unified LLM factory.

Supported providers
-------------------
- Gemini  : Google Gemini via google-genai SDK  (Interactions API)
- Grok    : xAI Grok via OpenAI-compatible REST (openai SDK)
- Ollama  : Local Ollama server                  (ollama SDK)

All three are wrapped in a single ``LLMClient`` class that exposes one
method: ``generate(prompt: str) -> str``.  This keeps the rest of the
codebase provider-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ── Defaults ──────────────────────────────────────────────────────────────────

PROVIDER_DEFAULTS: dict[str, dict] = {
    "Gemini": {
        "model": "gemini-3.8-flash",
        "api_key_label": "Gemini API Key",
        "needs_api_key": True,
        "needs_base_url": False,
        "base_url": "",
    },
    "Grok": {
        "model": "grok-3-mini",
        "api_key_label": "Grok (xAI) API Key",
        "needs_api_key": True,
        "needs_base_url": False,
        "base_url": "https://api.x.ai/v1",
    },
    "Ollama": {
        "model": "qwen3:4b",
        "api_key_label": "",           # no key needed
        "needs_api_key": False,
        "needs_base_url": True,
        "base_url": "http://localhost:11434",
    },
}

PROVIDERS = list(PROVIDER_DEFAULTS.keys())


# ── Wrapper ───────────────────────────────────────────────────────────────────

@dataclass
class LLMClient:
    """Provider-agnostic LLM wrapper.

    Parameters
    ----------
    provider   : one of "Gemini", "Grok", "Ollama"
    model_name : model identifier string
    _client    : raw provider client (internal)
    _base_url  : Ollama server URL (Ollama only)
    """

    provider: str
    model_name: str
    _client: Any = field(repr=False)
    _base_url: str = ""

    # ------------------------------------------------------------------
    def generate(self, prompt: str, timeout: int = 90) -> str:
        """Generate text from *prompt* and return the response string."""

        if self.provider == "Gemini":
            try:
                interaction = self._client.interactions.create(
                    model=self.model_name,
                    input=prompt,
                    timeout=timeout,
                )
                if interaction.output_text:
                    return interaction.output_text
            except Exception:
                pass

            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return response.text or ""

        elif self.provider == "Grok":
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                timeout=timeout,
            )
            return response.choices[0].message.content or ""

        elif self.provider == "Ollama":
            response = self._client.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            # ollama SDK returns a dict-like object
            msg = response.get("message") or response.message
            if hasattr(msg, "content"):
                return msg.content or ""
            return str(msg.get("content", ""))

        raise ValueError(f"Unsupported provider: {self.provider!r}")

    # ------------------------------------------------------------------
    def test_connection(self) -> str:
        """Send a minimal ping and return the model's reply."""
        return self.generate("Reply with exactly: Connection successful!", timeout=30)


# ── Factory ───────────────────────────────────────────────────────────────────

def create_llm(
    provider: str,
    model_name: str,
    api_key: str = "",
    base_url: str = "",
) -> LLMClient:
    """Construct and return an ``LLMClient`` for *provider*.

    Parameters
    ----------
    provider   : "Gemini" | "Grok" | "Ollama"
    model_name : model identifier
    api_key    : API key (required for Gemini and Grok, ignored for Ollama)
    base_url   : Ollama server URL (default ``http://localhost:11434``)
    """

    provider = provider.strip()
    model_name = model_name.strip()

    if not model_name:
        raise ValueError("model_name cannot be empty.")

    defaults = PROVIDER_DEFAULTS.get(provider, {})

    # ── Gemini ────────────────────────────────────────────────────────
    if provider == "Gemini":
        if not api_key.strip():
            raise ValueError("A Gemini API key is required.")
        from google import genai
        from google.genai import types as gtypes

        raw = genai.Client(
            api_key=api_key.strip(),
            http_options=gtypes.HttpOptions(timeout=120_000),
        )
        return LLMClient(provider=provider, model_name=model_name, _client=raw)

    # ── Grok (xAI) ────────────────────────────────────────────────────
    elif provider == "Grok":
        if not api_key.strip():
            raise ValueError("A Grok API key is required.")
        import openai

        raw = openai.OpenAI(
            api_key=api_key.strip(),
            base_url=base_url.strip() or defaults["base_url"],
            timeout=120.0,
        )
        return LLMClient(provider=provider, model_name=model_name, _client=raw)

    # ── Ollama (local) ────────────────────────────────────────────────
    elif provider == "Ollama":
        import ollama

        effective_url = base_url.strip() or defaults["base_url"]
        raw = ollama.Client(host=effective_url)
        return LLMClient(
            provider=provider,
            model_name=model_name,
            _client=raw,
            _base_url=effective_url,
        )

    raise ValueError(
        f"Unknown provider {provider!r}. Choose from: {', '.join(PROVIDERS)}"
    )


# ── Legacy shim (keeps old call-sites working) ────────────────────────────────

def test_llm_connection(client: LLMClient, model_name: str) -> str:  # noqa: ARG001
    """Thin shim so existing imports still work."""
    return client.test_connection()
