"""Model providers. Model ids look like `provider:model`, e.g. `anthropic:claude-sonnet-5-5`."""
import os
import httpx

TIMEOUT = 120


def complete(model_id: str, prompt: str) -> str:
    provider, _, model = model_id.partition(":")
    if provider == "mock":
        return mock(model, prompt)
    if provider == "anthropic":
        r = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"},
            json={"model": model, "max_tokens": 2048, "messages": [{"role": "user", "content": prompt}]},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return "".join(b.get("text", "") for b in r.json()["content"])
    if provider == "openai":  # also any OpenAI-compatible server via OPENAI_BASE_URL
        base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        r = httpx.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}]},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    raise ValueError(f"Unknown provider '{provider}'. Use mock:, anthropic: or openai:")


def mock(model: str, prompt: str) -> str:
    """Deterministic offline models for demos and tests."""
    if model == "judge":
        return "PASS"
    if model == "empty":
        return ""
    return f"Mock answer to: {prompt}"
