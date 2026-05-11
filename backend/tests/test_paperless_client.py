from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.paperless import PaperlessClient


BASE_URL = "http://paperless.test"


def make_response(results, next_url=None):
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "count": len(results),
        "next": next_url,
        "previous": None,
        "results": results,
    }
    return response


@pytest.mark.parametrize(
    ("method_name", "path"),
    [
        ("get_tags", "tags"),
        ("get_correspondents", "correspondents"),
        ("get_document_types", "document_types"),
        ("get_custom_fields", "custom_fields"),
    ],
)
@pytest.mark.asyncio
async def test_metadata_collections_request_configured_fetch_size(method_name, path):
    client = PaperlessClient(base_url=BASE_URL, token="token")
    client.client.get = AsyncMock(return_value=make_response([]))

    await getattr(client, method_name)()

    requested_url = client.client.get.call_args.args[0]
    assert requested_url == f"{BASE_URL}/api/{path}/?page_size=1000"

    await client.close()


@pytest.mark.asyncio
async def test_metadata_collections_are_cached_between_calls():
    client = PaperlessClient(base_url=BASE_URL, token="token")
    client.client.get = AsyncMock(
        return_value=make_response([{"id": 1, "name": "ai-process"}])
    )

    first = await client.get_tags()
    second = await client.get_tags()

    assert first == second
    assert client.client.get.call_count == 1

    await client.close()
