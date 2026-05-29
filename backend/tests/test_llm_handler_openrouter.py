from unittest.mock import AsyncMock

import pytest

from app.services.llm_handler import LLMHandler


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


@pytest.mark.asyncio
async def test_openrouter_client_adds_app_attribution_headers():
    handler = LLMHandler(
        provider="openrouter",
        model="openai/gpt-4o-mini",
        api_base=OPENROUTER_BASE_URL,
        api_key="sk-test",
    )

    headers = handler.client.headers

    assert headers["Authorization"] == "Bearer sk-test"
    assert headers["HTTP-Referer"] == "https://github.com/nyxtron/paperless-aissist"
    assert headers["X-OpenRouter-Title"] == "Paperless-AIssist"

    await handler.close()


@pytest.mark.asyncio
async def test_openai_client_does_not_add_openrouter_headers():
    handler = LLMHandler(
        provider="openai",
        model="gpt-4o-mini",
        api_base="https://api.openai.com/v1",
        api_key="sk-test",
    )

    headers = handler.client.headers

    assert "HTTP-Referer" not in headers
    assert "X-OpenRouter-Title" not in headers

    await handler.close()


@pytest.mark.asyncio
async def test_openrouter_text_completion_uses_openai_compatible_path():
    handler = LLMHandler(
        provider="openrouter",
        model="openai/gpt-4o-mini",
        api_base=OPENROUTER_BASE_URL,
        api_key="sk-test",
    )
    handler._openai_complete = AsyncMock(return_value={"text": "ok"})

    result = await handler.complete("system", "user", json_mode=False)

    assert result == {"text": "ok"}
    handler._openai_complete.assert_awaited_once_with(
        "system", "user", False, 0.3, None
    )


@pytest.mark.asyncio
async def test_openrouter_vision_completion_uses_images_not_native_pdf():
    handler = LLMHandler(
        provider="openrouter",
        model="openai/gpt-4o",
        api_base=OPENROUTER_BASE_URL,
        api_key="sk-test",
    )
    handler._openai_vision_complete = AsyncMock(return_value={"text": "ok"})

    result = await handler.vision_complete(
        system_prompt="Extract text",
        images=[b"page"],
        pdf_bytes=b"%PDF-1.4",
        json_mode=False,
    )

    assert result == {"text": "ok"}
    call = handler._openai_vision_complete.await_args
    assert call.args[2] == [b"page"]
    assert call.kwargs["pdf_bytes"] is None


@pytest.mark.asyncio
async def test_openai_vision_completion_keeps_native_pdf_support():
    handler = LLMHandler(
        provider="openai",
        model="gpt-4o",
        api_base="https://api.openai.com/v1",
        api_key="sk-test",
    )
    handler._openai_vision_complete = AsyncMock(return_value={"text": "ok"})

    await handler.vision_complete(
        system_prompt="Extract text",
        images=[],
        pdf_bytes=b"%PDF-1.4",
        json_mode=False,
    )

    assert handler._openai_vision_complete.await_args.kwargs["pdf_bytes"] == b"%PDF-1.4"


@pytest.mark.asyncio
async def test_openrouter_from_config_uses_provider_defaults(monkeypatch):
    async def fake_get_config(key):
        values = {
            "llm_provider": "openrouter",
            "llm_model": "",
            "llm_api_base": "",
            "llm_api_key": "sk-test",
            "llm_timeout": "",
        }
        return values.get(key)

    monkeypatch.setattr(LLMHandler, "_get_config", staticmethod(fake_get_config))

    handler = await LLMHandler.from_config(for_vision=False)

    assert handler.provider == "openrouter"
    assert handler.model == "openai/gpt-4o-mini"
    assert handler.api_base == OPENROUTER_BASE_URL


@pytest.mark.asyncio
async def test_openrouter_from_config_uses_vision_provider_defaults(monkeypatch):
    async def fake_get_config(key):
        values = {
            "llm_provider_vision": "openrouter",
            "llm_model_vision": "",
            "llm_api_base_vision": "",
            "llm_api_key_vision": "sk-test",
            "llm_timeout_vision": "",
        }
        return values.get(key)

    monkeypatch.setattr(LLMHandler, "_get_config", staticmethod(fake_get_config))

    handler = await LLMHandler.from_config(for_vision=True)

    assert handler.provider == "openrouter"
    assert handler.model == "openai/gpt-4o"
    assert handler.api_base == OPENROUTER_BASE_URL
