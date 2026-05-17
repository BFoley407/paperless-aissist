"""Optional smoke test for Vision OCR against a real Ollama instance.

Run manually with:

PAPERLESS_AISSIST_OLLAMA_SMOKE=1 \
OLLAMA_BASE_URL=http://127.0.0.1:11434 \
OLLAMA_VISION_MODEL=benhaotang/Nanonets-OCR-s:latest \
python3 -m pytest tests/test_vision_ollama_smoke.py -q
"""

import os

import fitz
import httpx
import pytest

from app.services.llm_handler import LLMHandler
from app.services.vision import VisionPipeline


SMOKE_ENABLED = os.getenv("PAPERLESS_AISSIST_OLLAMA_SMOKE") == "1"
SMOKE_TEXT = "PAPERLESS AISSIST OLLAMA SMOKE TEST 12345"


def _build_smoke_pdf() -> bytes:
    doc = fitz.open()
    try:
        page = doc.new_page()
        page.insert_text((72, 96), SMOKE_TEXT, fontsize=20)
        return doc.tobytes()
    finally:
        doc.close()


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
    reason="Set PAPERLESS_AISSIST_OLLAMA_SMOKE=1 to run the real Ollama smoke test.",
)
async def test_vision_pipeline_extracts_text_with_real_ollama():
    model = os.getenv("OLLAMA_VISION_MODEL")
    if not model:
        pytest.fail("Set OLLAMA_VISION_MODEL to the local Ollama vision model name.")

    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    timeout = float(os.getenv("OLLAMA_SMOKE_TIMEOUT", "120"))

    await _assert_ollama_model_available(base_url, model)

    handler = LLMHandler(
        provider="ollama",
        model=model,
        api_base=base_url,
        timeout=timeout,
    )
    pipeline = VisionPipeline(llm_handler=handler)

    try:
        result = await pipeline.extract_text_from_pdf(
            _build_smoke_pdf(),
            prompt=(
                "Extract all readable text from this document. "
                "Return plain text only, without commentary."
            ),
        )
    finally:
        await handler.close()

    extracted_text = (result.get("text") or result.get("raw") or "").upper()
    assert "12345" in extracted_text
    assert "PAPERLESS" in extracted_text or "AISSIST" in extracted_text
