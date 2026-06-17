import json

import httpx
import pytest

from app.services.llm_handler import LLMHandler


class CaptureTransport(httpx.AsyncBaseTransport):
    def __init__(self, response_json: dict):
        self.requests: list[httpx.Request] = []
        self.response_json = response_json

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return httpx.Response(200, json=self.response_json, request=request)


@pytest.mark.asyncio
async def test_openai_compatible_text_request_includes_generation_limits():
    transport = CaptureTransport(
        {"choices": [{"message": {"content": "ok"}}], "usage": {"total_tokens": 12}}
    )
    handler = LLMHandler(
        provider="openrouter",
        model="openai/gpt-4o-mini",
        api_base="http://openrouter.test/v1",
        temperature=0.1,
        max_tokens=512,
    )
    handler._client = httpx.AsyncClient(
        base_url=handler.api_base,
        headers={"Content-Type": "application/json"},
        transport=transport,
    )

    result = await handler.complete("system", "user", json_mode=False)
    await handler.close()

    payload = json.loads(transport.requests[0].content)
    assert result == {"text": "ok"}
    assert payload["temperature"] == 0.1
    assert payload["max_tokens"] == 512


@pytest.mark.asyncio
async def test_openai_compatible_text_request_omits_max_tokens_when_unset():
    transport = CaptureTransport({"choices": [{"message": {"content": "ok"}}]})
    handler = LLMHandler(
        provider="openai",
        model="gpt-4o-mini",
        api_base="http://openai.test/v1",
    )
    handler._client = httpx.AsyncClient(
        base_url=handler.api_base,
        headers={"Content-Type": "application/json"},
        transport=transport,
    )

    await handler.complete("system", "user", json_mode=False)
    await handler.close()

    payload = json.loads(transport.requests[0].content)
    assert payload["temperature"] == 0.3
    assert "max_tokens" not in payload


@pytest.mark.asyncio
async def test_ollama_text_request_maps_max_tokens_to_num_predict():
    transport = CaptureTransport({"message": {"content": "ok"}})
    handler = LLMHandler(
        provider="ollama",
        model="qwen2.5:7b",
        api_base="http://ollama.test",
        temperature=0.2,
        max_tokens=256,
    )
    handler._client = httpx.AsyncClient(
        base_url=handler.api_base,
        headers={"Content-Type": "application/json"},
        transport=transport,
    )

    result = await handler.complete("system", "user", json_mode=False)
    await handler.close()

    payload = json.loads(transport.requests[0].content)
    assert result == {"text": "ok"}
    assert payload["options"]["temperature"] == 0.2
    assert payload["options"]["num_predict"] == 256


@pytest.mark.asyncio
async def test_ollama_text_request_maps_context_window_to_num_ctx():
    transport = CaptureTransport({"message": {"content": "ok"}})
    handler = LLMHandler(
        provider="ollama",
        model="qwen3:8b",
        api_base="http://ollama.test",
        num_ctx=16384,
    )
    handler._client = httpx.AsyncClient(
        base_url=handler.api_base,
        headers={"Content-Type": "application/json"},
        transport=transport,
    )

    await handler.complete("system", "user", json_mode=False)
    await handler.close()

    payload = json.loads(transport.requests[0].content)
    assert payload["options"]["num_ctx"] == 16384


@pytest.mark.asyncio
async def test_openai_compatible_text_request_omits_context_window():
    transport = CaptureTransport({"choices": [{"message": {"content": "ok"}}]})
    handler = LLMHandler(
        provider="openai",
        model="gpt-4o-mini",
        api_base="http://openai.test/v1",
        num_ctx=16384,
    )
    handler._client = httpx.AsyncClient(
        base_url=handler.api_base,
        headers={"Content-Type": "application/json"},
        transport=transport,
    )

    await handler.complete("system", "user", json_mode=False)
    await handler.close()

    payload = json.loads(transport.requests[0].content)
    assert "num_ctx" not in payload
    assert "options" not in payload


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("provider", "response_json"),
    [
        ("ollama", {"message": {"content": "ok"}}),
        ("openai", {"choices": [{"message": {"content": "ok"}}]}),
    ],
)
async def test_text_requests_strip_problematic_ascii_control_characters(
    provider, response_json
):
    transport = CaptureTransport(response_json)
    handler = LLMHandler(
        provider=provider,
        model="test-model",
        api_base="http://llm.test",
    )
    handler._client = httpx.AsyncClient(
        base_url=handler.api_base,
        headers={"Content-Type": "application/json"},
        transport=transport,
    )

    user_prompt = "Steuer\x11\x12bescheid\n\t\rBetrag\x1b\x7fEnde"

    await handler.complete("System\x00Prompt", user_prompt, json_mode=False)
    await handler.close()

    payload = json.loads(transport.requests[0].content)
    assert payload["messages"][0]["content"] == "SystemPrompt"
    assert payload["messages"][1]["content"] == "Steuerbescheid\n\t\rBetragEnde"


@pytest.mark.asyncio
async def test_openai_compatible_vision_request_includes_generation_limits():
    transport = CaptureTransport({"choices": [{"message": {"content": "vision text"}}]})
    handler = LLMHandler(
        provider="openrouter",
        model="openai/gpt-4o",
        api_base="http://openrouter.test/v1",
        temperature=0.0,
        max_tokens=1024,
    )
    handler._client = httpx.AsyncClient(
        base_url=handler.api_base,
        headers={"Content-Type": "application/json"},
        transport=transport,
    )

    result = await handler.vision_complete(
        system_prompt="Extract text",
        images=[b"page"],
        json_mode=False,
    )
    await handler.close()

    payload = json.loads(transport.requests[0].content)
    assert result == {"text": "vision text"}
    assert payload["temperature"] == 0.0
    assert payload["max_tokens"] == 1024


@pytest.mark.asyncio
async def test_ollama_vision_request_maps_context_window_to_num_ctx():
    transport = CaptureTransport({"message": {"content": "vision text"}})
    handler = LLMHandler(
        provider="ollama",
        model="qwen2.5vl:7b",
        api_base="http://ollama.test",
        num_ctx=32768,
    )
    handler._client = httpx.AsyncClient(
        base_url=handler.api_base,
        headers={"Content-Type": "application/json"},
        transport=transport,
    )

    result = await handler.vision_complete(
        system_prompt="Extract text",
        images=[b"page"],
        json_mode=False,
    )
    await handler.close()

    payload = json.loads(transport.requests[0].content)
    assert result == {"text": "vision text"}
    assert payload["options"]["num_ctx"] == 32768


@pytest.mark.asyncio
async def test_from_config_reads_generation_limits(monkeypatch):
    async def fake_get_config(key):
        values = {
            "llm_provider": "openrouter",
            "llm_model": "openai/gpt-4o-mini",
            "llm_api_base": "",
            "llm_api_key": "sk-test",
            "llm_timeout": "45",
            "llm_temperature": "0.15",
            "llm_max_tokens": "777",
            "llm_num_ctx": "16384",
        }
        return values.get(key)

    monkeypatch.setattr(LLMHandler, "_get_config", staticmethod(fake_get_config))

    handler = await LLMHandler.from_config(for_vision=False)

    assert handler.temperature == 0.15
    assert handler.max_tokens == 777
    assert handler.num_ctx == 16384


@pytest.mark.asyncio
async def test_vision_from_config_falls_back_to_main_generation_limits(monkeypatch):
    async def fake_get_config(key):
        values = {
            "llm_provider": "openai",
            "llm_model": "gpt-4o-mini",
            "llm_api_base": "https://api.openai.com/v1",
            "llm_api_key": "sk-test",
            "llm_timeout": "60",
            "llm_temperature": "0.25",
            "llm_max_tokens": "2048",
            "llm_num_ctx": "16384",
            "llm_provider_vision": "",
            "llm_model_vision": "gpt-4o",
            "llm_api_base_vision": "",
            "llm_api_key_vision": "",
            "llm_timeout_vision": "",
            "llm_temperature_vision": "",
            "llm_max_tokens_vision": "",
            "llm_num_ctx_vision": "",
        }
        return values.get(key)

    monkeypatch.setattr(LLMHandler, "_get_config", staticmethod(fake_get_config))

    handler = await LLMHandler.from_config(for_vision=True)

    assert handler.temperature == 0.25
    assert handler.max_tokens == 2048
    assert handler.num_ctx == 16384


@pytest.mark.asyncio
async def test_vision_from_config_reads_vision_specific_context_window(monkeypatch):
    async def fake_get_config(key):
        values = {
            "llm_provider": "ollama",
            "llm_model": "qwen3:8b",
            "llm_api_base": "http://localhost:11434",
            "llm_api_key": "",
            "llm_timeout": "60",
            "llm_temperature": "0.3",
            "llm_max_tokens": "",
            "llm_num_ctx": "16384",
            "llm_provider_vision": "ollama",
            "llm_model_vision": "qwen2.5vl:7b",
            "llm_api_base_vision": "http://localhost:11434",
            "llm_api_key_vision": "",
            "llm_timeout_vision": "120",
            "llm_temperature_vision": "0.1",
            "llm_max_tokens_vision": "4096",
            "llm_num_ctx_vision": "32768",
        }
        return values.get(key)

    monkeypatch.setattr(LLMHandler, "_get_config", staticmethod(fake_get_config))

    handler = await LLMHandler.from_config(for_vision=True)

    assert handler.model == "qwen2.5vl:7b"
    assert handler.temperature == 0.1
    assert handler.max_tokens == 4096
    assert handler.num_ctx == 32768
