import json

import httpx
import pytest

from app.services.llm_handler import LLMHandler
from app.services.vision import VisionPipeline


class DummyHandler:
    provider = "openai"

    def __init__(self, api_base: str):
        self.api_base = api_base
        self.calls = []

    async def vision_complete(self, **kwargs):
        self.calls.append(kwargs)
        return {"text": "ok"}


@pytest.mark.asyncio
async def test_openai_auto_uses_native_pdf_for_official_openai(monkeypatch):
    handler = DummyHandler("https://api.openai.com/v1")
    pipeline = VisionPipeline(llm_handler=handler)

    async def fake_mode():
        return "auto"

    monkeypatch.setattr(pipeline, "_get_vision_pdf_mode", fake_mode)

    result = await pipeline.extract_text_from_pdf(b"%PDF-1.4")

    assert result == {"text": "ok"}
    assert handler.calls[0]["pdf_bytes"] == b"%PDF-1.4"
    assert handler.calls[0]["images"] == []


@pytest.mark.asyncio
async def test_openai_auto_uses_page_images_for_compatible_runtime(monkeypatch):
    handler = DummyHandler("http://localhost:1234/v1")
    pipeline = VisionPipeline(llm_handler=handler)

    async def fake_mode():
        return "auto"

    async def fake_images(_pdf_bytes):
        return [b"page-1", b"page-2"]

    monkeypatch.setattr(pipeline, "_get_vision_pdf_mode", fake_mode)
    monkeypatch.setattr(pipeline, "pdf_to_images", fake_images)

    result = await pipeline.extract_text_from_pdf(b"%PDF-1.4")

    assert result == {"text": "ok"}
    assert handler.calls[0]["pdf_bytes"] is None
    assert handler.calls[0]["images"] == [b"page-1", b"page-2"]


@pytest.mark.asyncio
async def test_openai_page_images_mode_forces_page_images(monkeypatch):
    handler = DummyHandler("https://api.openai.com/v1")
    pipeline = VisionPipeline(llm_handler=handler)

    async def fake_mode():
        return "page_images"

    async def fake_images(_pdf_bytes):
        return [b"page-1"]

    monkeypatch.setattr(pipeline, "_get_vision_pdf_mode", fake_mode)
    monkeypatch.setattr(pipeline, "pdf_to_images", fake_images)

    await pipeline.extract_text_from_pdf(b"%PDF-1.4")

    assert handler.calls[0]["pdf_bytes"] is None
    assert handler.calls[0]["images"] == [b"page-1"]


@pytest.mark.asyncio
async def test_openai_native_pdf_mode_forces_native_pdf(monkeypatch):
    handler = DummyHandler("http://localhost:1234/v1")
    pipeline = VisionPipeline(llm_handler=handler)

    async def fake_mode():
        return "native_pdf"

    monkeypatch.setattr(pipeline, "_get_vision_pdf_mode", fake_mode)

    await pipeline.extract_text_from_pdf(b"%PDF-1.4")

    assert handler.calls[0]["pdf_bytes"] == b"%PDF-1.4"
    assert handler.calls[0]["images"] == []


class CaptureTransport(httpx.AsyncBaseTransport):
    def __init__(self):
        self.requests = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": f"text page {len(self.requests)}",
                        },
                    },
                ],
            },
            request=request,
        )


@pytest.mark.asyncio
async def test_openai_image_vision_sends_one_request_per_page():
    transport = CaptureTransport()
    handler = LLMHandler(
        provider="openai",
        model="vision-model",
        api_base="http://local-openai.test/v1",
        timeout=30,
    )
    handler._client = httpx.AsyncClient(
        base_url=handler.api_base,
        headers={"Content-Type": "application/json"},
        transport=transport,
    )

    result = await handler.vision_complete(
        system_prompt="Extract text.",
        images=[b"page-1", b"page-2"],
        json_mode=False,
    )

    await handler.close()

    assert result["text"] == "text page 1\n\ntext page 2"
    assert len(transport.requests) == 2
    first_payload = json.loads(transport.requests[0].content)
    second_payload = json.loads(transport.requests[1].content)
    assert len(first_payload["messages"][1]["content"]) == 1
    assert len(second_payload["messages"][1]["content"]) == 1
    assert first_payload["messages"][1]["content"][0]["type"] == "image_url"
