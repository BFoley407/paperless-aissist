import logging

from app.database import get_session
from app.models import Config
from app.services import scheduler as scheduler_service
from sqlmodel import select


def _automation_headers(client):
    response = client.post("/api/config/automation-token")
    assert response.status_code == 200
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}, token


def test_generate_automation_token_is_stored_hashed_and_masked(client):
    response = client.post("/api/config/automation-token")

    assert response.status_code == 200
    token = response.json()["token"]
    assert token.startswith("paia_")

    with get_session() as session:
        stmt = select(Config).where(Config.key == "automation_api_token_hash")
        stored = session.exec(stmt).first()
        stored_value = stored.value if stored else None

    assert stored is not None
    assert stored_value != token
    assert len(stored_value) == 64

    config_response = client.get("/api/config")
    assert config_response.status_code == 200
    config_payload = config_response.json()
    assert "automation_api_token_hash" not in config_payload["data"]
    assert "automation_api_token_hash" in config_payload["secrets_set"]
    assert token not in str(config_payload)

    direct_response = client.get("/api/config/automation_api_token_hash")
    assert direct_response.status_code == 404


def test_revoke_automation_token_removes_secret_status(client):
    headers, _ = _automation_headers(client)
    assert client.get("/api/automation/status", headers=headers).status_code == 200

    response = client.delete("/api/config/automation-token")

    assert response.status_code == 200
    config_response = client.get("/api/config")
    assert "automation_api_token_hash" not in config_response.json()["secrets_set"]
    assert client.get("/api/automation/status", headers=headers).status_code == 401


def test_automation_status_requires_dedicated_token_even_when_ui_auth_disabled(client):
    response = client.get("/api/automation/status")

    assert response.status_code == 401


def test_automation_status_rejects_invalid_token(client):
    _automation_headers(client)

    response = client.get(
        "/api/automation/status",
        headers={"Authorization": "Bearer wrong-token"},
    )

    assert response.status_code == 401


def test_automation_status_accepts_generated_token(client):
    headers, _ = _automation_headers(client)

    response = client.get("/api/automation/status", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "is_processing" in data
    assert "automation_running" in data


def test_automation_api_calls_are_logged_without_token(client, caplog):
    headers, token = _automation_headers(client)
    caplog.set_level(logging.INFO, logger="app.routers.automation")

    client.get("/api/automation/status", headers=headers)
    client.post("/api/automation/process/stop", headers=headers)
    scheduler_service._set_processing(7)
    try:
        client.post("/api/automation/process/start", headers=headers)
    finally:
        scheduler_service._clear_processing()

    log_text = caplog.text
    assert "Automation API status requested" in log_text
    assert "Automation API stop requested" in log_text
    assert "Automation API start requested" in log_text
    assert token not in log_text


def test_automation_start_is_idempotent_when_processing_is_already_running(client):
    headers, _ = _automation_headers(client)
    scheduler_service._set_processing(7)

    try:
        response = client.post("/api/automation/process/start", headers=headers)
    finally:
        scheduler_service._clear_processing()

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "already_running"
    assert "Already processing document #7" in data["message"]


def test_automation_start_returns_started_for_valid_token(client, monkeypatch):
    from app.services import automation as automation_service

    async def slow_legacy_processing():
        import asyncio

        await asyncio.sleep(1)
        return {"success": True, "processed": 0, "failed": 0, "results": []}

    async def skipped_modular_processing():
        return {"success": True, "processed": 0, "failed": 0, "results": []}

    monkeypatch.setattr(
        automation_service, "process_tagged_documents", slow_legacy_processing
    )
    monkeypatch.setattr(
        automation_service,
        "process_modular_tagged_documents",
        skipped_modular_processing,
    )
    headers, _ = _automation_headers(client)

    try:
        response = client.post("/api/automation/process/start", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "started"
    finally:
        client.post("/api/automation/process/stop", headers=headers)
        scheduler_service._clear_processing()


def test_automation_stop_without_running_task_is_idempotent(client):
    headers, _ = _automation_headers(client)

    response = client.post("/api/automation/process/stop", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "not_running"
