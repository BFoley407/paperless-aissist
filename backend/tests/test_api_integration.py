from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def test_config_crud(client):
    """Test full CRUD cycle for config values."""
    response = client.post(
        "/api/config",
        json={"key": "test_integration_key", "value": "test_value"},
    )
    assert response.status_code == 200
    assert response.json()["key"] == "test_integration_key"
    assert response.json()["value"] == "test_value"

    response = client.get("/api/config/test_integration_key")
    assert response.status_code == 200
    assert response.json()["value"] == "test_value"

    response = client.post(
        "/api/config",
        json={"key": "test_integration_key", "value": "updated_value"},
    )
    assert response.status_code == 200
    assert response.json()["value"] == "updated_value"

    response = client.delete("/api/config/test_integration_key")
    assert response.status_code == 200

    response = client.get("/api/config/test_integration_key")
    assert response.status_code == 404


def test_config_list_masks_secrets(client):
    """Sensitive keys are excluded from GET /api/config and listed in secrets_set."""
    client.post(
        "/api/config", json={"key": "llm_api_key", "value": "sk-super-secret-key-12345"}
    )
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "llm_api_key" not in data["data"]
    assert "secrets_set" in data
    assert "llm_api_key" in data["secrets_set"]


def test_config_sensitive_key_not_accessible(client):
    """GET /api/config/{key} returns 404 for sensitive keys."""
    for key in ["paperless_token", "llm_api_key", "llm_api_key_vision"]:
        response = client.get(f"/api/config/{key}")
        assert response.status_code == 404, (
            f"Expected 404 for {key}, got {response.status_code}"
        )


def test_stats_endpoints(client):
    """Stats endpoints return valid data."""
    response = client.get("/api/stats")
    assert response.status_code == 200
    assert "total_processed" in response.json()

    response = client.get("/api/stats/daily?days=7")
    assert response.status_code == 200

    response = client.get("/api/stats/recent?limit=10")
    assert response.status_code == 200


def test_stats_bounds(client):
    """Stats endpoints enforce parameter bounds."""
    response = client.get("/api/stats/daily?days=500")
    assert response.status_code == 200

    response = client.get("/api/stats/recent?limit=5000")
    assert response.status_code == 200


def test_auth_status_endpoint(client):
    """Auth status returns auth_enabled flag."""
    response = client.get("/api/auth/status")
    assert response.status_code == 200
    assert "auth_enabled" in response.json()


def test_app_info_endpoint(client):
    """App info endpoint exposes the runtime version string."""
    response = client.get("/api/app-info")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert isinstance(data["version"], str)
    assert data["version"]


def test_prompts_list(client):
    """Prompts endpoint returns a list."""
    response = client.get("/api/prompts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_scheduler_status_endpoint(client):
    """Scheduler status endpoint returns JSON."""
    response = client.get("/api/scheduler")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data or "is_processing" in data
    assert "interval_minutes" in data or "interval" in data


def test_stats_log_stream_asyncio_imported(client):
    """Verify asyncio is imported in stats.py so event_gen does not NameError."""
    import ast
    import inspect
    from app.routers.stats import stream_logs

    source = inspect.getsource(stream_logs)
    tree = ast.parse(source)
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    assert "asyncio" in names


def test_tagged_documents_uses_tag_filtered_requests_and_deduplicates(client):
    client.post("/api/config", json={"key": "process_tag", "value": "ai-process"})
    paperless = MagicMock()
    paperless.reset_metrics = MagicMock()
    paperless.get_metrics = MagicMock(return_value={"requests": 3, "paged_requests": 2})
    paperless.get_tags = AsyncMock(
        return_value=[
            {"id": 5, "name": "ai-process"},
            {"id": 7, "name": "ai-title"},
        ]
    )
    paperless.list_documents = AsyncMock(
        side_effect=[
            [
                {"id": 1, "title": "Legacy", "created": "2026-01-01", "tags": [5]},
                {"id": 2, "title": "Both", "created": "2026-01-02", "tags": [5, 7]},
            ],
            [
                {"id": 2, "title": "Both", "created": "2026-01-02", "tags": [5, 7]},
                {"id": 3, "title": "Title", "created": "2026-01-03", "tags": [7]},
            ],
        ]
    )

    with (
        patch(
            "app.routers.documents.PaperlessClientManager.get_client",
            AsyncMock(return_value=paperless),
        ),
        patch(
            "app.routers.documents.DocumentProcessor._get_modular_tag_map",
            AsyncMock(return_value={"title": "ai-title"}),
        ),
    ):
        response = client.get("/api/documents/tagged")

    assert response.status_code == 200
    data = response.json()
    assert [doc["id"] for doc in data["documents"]] == [1, 2, 3]
    assert data["process_tag_id"] == 5
    assert paperless.list_documents.call_count == 2
    tag_filters = {
        tuple(call.kwargs["tags"]) for call in paperless.list_documents.call_args_list
    }
    assert tag_filters == {(5,), (7,)}


def test_tagged_documents_no_trigger_tags_does_not_scan_documents(client):
    client.post("/api/config", json={"key": "process_tag", "value": "missing-process"})
    paperless = MagicMock()
    paperless.reset_metrics = MagicMock()
    paperless.get_tags = AsyncMock(return_value=[{"id": 10, "name": "unrelated"}])
    paperless.list_documents = AsyncMock(return_value=[])

    with (
        patch(
            "app.routers.documents.PaperlessClientManager.get_client",
            AsyncMock(return_value=paperless),
        ),
        patch(
            "app.routers.documents.DocumentProcessor._get_modular_tag_map",
            AsyncMock(return_value={"title": "missing-title"}),
        ),
    ):
        response = client.get("/api/documents/tagged")

    assert response.status_code == 200
    assert response.json()["documents"] == []
    paperless.list_documents.assert_not_called()


def test_metadata_routes_pass_refresh_to_paperless_client(client):
    paperless = MagicMock()
    paperless.get_tags = AsyncMock(return_value=[{"id": 1, "name": "ai-process"}])
    paperless.get_correspondents = AsyncMock(return_value=[])
    paperless.get_document_types = AsyncMock(return_value=[])

    with patch(
        "app.routers.documents.PaperlessClientManager.get_client",
        AsyncMock(return_value=paperless),
    ):
        tags_response = client.get("/api/documents/tags?refresh=true")
        test_response = client.get("/api/documents/test-connection?refresh=true")

    assert tags_response.status_code == 200
    assert test_response.status_code == 200
    assert paperless.get_tags.call_args_list[0].kwargs == {"force_refresh": True}
    assert paperless.get_correspondents.call_args_list[0].kwargs == {
        "force_refresh": True
    }
    assert paperless.get_document_types.call_args_list[0].kwargs == {
        "force_refresh": True
    }
    assert paperless.get_tags.call_args_list[1].kwargs == {"force_refresh": True}
