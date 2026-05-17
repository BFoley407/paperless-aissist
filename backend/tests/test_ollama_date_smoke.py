"""Optional smoke test for date detection against a real Ollama instance.

Run manually with:

PAPERLESS_AISSIST_OLLAMA_DATE_SMOKE=1 \
OLLAMA_BASE_URL=http://127.0.0.1:11434 \
OLLAMA_TEXT_MODEL=qwen2.5:7b \
python3 -m pytest tests/test_ollama_date_smoke.py -q
"""

import json
import os
from pathlib import Path

import httpx
import pytest

from app.services.llm_handler import LLMHandler


SMOKE_ENABLED = os.getenv("PAPERLESS_AISSIST_OLLAMA_DATE_SMOKE") == "1"
PROMPT_PATH = Path(__file__).resolve().parents[2] / "examples" / "prompts" / "date-detection.json"


async def _assert_ollama_model_available(base_url: str, model: str) -> None:
    async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as client:
        response = await client.get("/api/tags")
        response.raise_for_status()

    models = response.json().get("models", [])
    model_names = {entry.get("name") for entry in models}
    if model not in model_names:
        available = ", ".join(sorted(name for name in model_names if name)) or "none"
        pytest.fail(f"Ollama model '{model}' is not available. Found: {available}")


@pytest.mark.asyncio
@pytest.mark.skipif(
    not SMOKE_ENABLED,
    reason=(
        "Set PAPERLESS_AISSIST_OLLAMA_DATE_SMOKE=1 to run the real Ollama date "
        "smoke test."
    ),
)
async def test_date_prompt_extracts_issue_date_with_real_ollama():
    model = os.getenv("OLLAMA_TEXT_MODEL")
    if not model:
        pytest.fail("Set OLLAMA_TEXT_MODEL to the local Ollama text model name.")

    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    timeout = float(os.getenv("OLLAMA_SMOKE_TIMEOUT", "120"))
    await _assert_ollama_model_available(base_url, model)

    with open(PROMPT_PATH, encoding="utf-8") as handle:
        prompt = json.load(handle)

    user_prompt = (
        prompt["user_template"]
        .replace("{title}", "Starlink Invoice")
        .replace("{created_date}", "2026-05-17")
        .replace(
            "{content}",
            (
                "Rechnungsdatum: Dienstag, 28. April 2026\n"
                "Servicezeitraum: 29. April 2026 - 28. Mai 2026\n"
                "Zahlungsfrist: 12. Mai 2026"
            ),
        )
    )
    handler = LLMHandler(
        provider="ollama",
        model=model,
        api_base=base_url,
        timeout=timeout,
    )

    try:
        result = await handler.complete(
            system_prompt=prompt["system_prompt"],
            user_prompt=user_prompt,
            json_mode=True,
            temperature=0.0,
        )
    finally:
        await handler.close()

    assert result["created_date"] == "2026-04-28"
    assert result["confidence"] in {"high", "medium"}
