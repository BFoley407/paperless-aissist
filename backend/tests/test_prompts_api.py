from app.models import Prompt
from sqlmodel import Session, select


def delete_prompts_by_name(session: Session, *names: str) -> None:
    for name in names:
        prompts = session.exec(select(Prompt).where(Prompt.name == name)).all()
        for prompt in prompts:
            session.delete(prompt)
    session.commit()


def test_update_vision_ocr_prompt_allows_empty_user_template(client, session):
    prompt = Prompt(
        name="Vision OCR Empty User Template",
        prompt_type="vision_ocr",
        document_type_filter=None,
        system_prompt="Extract text from document images.",
        user_template="Previous template",
        is_active=True,
    )
    session.add(prompt)
    session.commit()
    session.refresh(prompt)

    update_response = client.put(
        f"/api/prompts/{prompt.id}",
        json={"user_template": ""},
    )
    assert update_response.status_code == 200

    get_response = client.get(f"/api/prompts/{prompt.id}")
    assert get_response.status_code == 200
    assert get_response.json()["user_template"] == ""


def test_prompt_templates_include_date_prompt_type(client):
    response = client.get("/api/prompts/templates")

    assert response.status_code == 200
    prompt_types = {item["value"] for item in response.json()["types"]}
    assert "date" in prompt_types
    variables = response.json()["variables"]
    assert {"name": "{created_date}", "description": "Current document date"} in variables
    assert {"name": "{current_date}", "description": "Current date"} in variables


def test_prompts_include_sample_status_for_legacy_sample(client, session):
    delete_prompts_by_name(session, "Date Detection")
    prompt = Prompt(
        name="Date Detection",
        prompt_type="date",
        document_type_filter=None,
        system_prompt="old date prompt",
        user_template="old template",
        is_active=True,
    )
    session.add(prompt)
    session.commit()

    response = client.get("/api/prompts")

    assert response.status_code == 200
    date_prompt = next(item for item in response.json() if item["name"] == "Date Detection")
    assert date_prompt["sample_key"] == "date-detection"
    assert date_prompt["sample_status"] == "legacy_sample"


def test_load_samples_does_not_overwrite_legacy_prompt(client, session):
    delete_prompts_by_name(session, "Date Detection")
    prompt = Prompt(
        name="Date Detection",
        prompt_type="date",
        document_type_filter=None,
        system_prompt="manual date prompt",
        user_template="manual template",
        is_active=True,
    )
    session.add(prompt)
    session.commit()
    session.refresh(prompt)

    response = client.post("/api/prompts/load-samples")

    assert response.status_code == 200
    assert response.json()["skipped"] >= 1
    get_response = client.get(f"/api/prompts/{prompt.id}")
    assert get_response.json()["system_prompt"] == "manual date prompt"
    assert get_response.json()["sample_status"] == "legacy_sample"


def test_load_single_sample_updates_only_one_prompt(client, session):
    delete_prompts_by_name(session, "Date Detection", "Title Generation")
    date_prompt = Prompt(
        name="Date Detection",
        prompt_type="date",
        document_type_filter=None,
        system_prompt="old date prompt",
        user_template="old template",
        is_active=True,
    )
    title_prompt = Prompt(
        name="Title Generation",
        prompt_type="title",
        document_type_filter=None,
        system_prompt="manual title prompt",
        user_template="manual title template",
        is_active=True,
    )
    session.add(date_prompt)
    session.add(title_prompt)
    session.commit()
    session.refresh(date_prompt)
    session.refresh(title_prompt)

    response = client.post(f"/api/prompts/{date_prompt.id}/load-sample")

    assert response.status_code == 200
    payload = response.json()
    assert payload["sample_key"] == "date-detection"
    assert payload["sample_status"] == "sample_current"
    assert "Current date: {current_date}" in payload["user_template"]

    title_response = client.get(f"/api/prompts/{title_prompt.id}")
    assert title_response.json()["system_prompt"] == "manual title prompt"


def test_get_single_sample_returns_bundled_prompt_without_saving(client, session):
    delete_prompts_by_name(session, "Date Detection")
    prompt = Prompt(
        name="Date Detection",
        prompt_type="date",
        document_type_filter=None,
        system_prompt="manual date prompt",
        user_template="manual template",
        is_active=True,
    )
    session.add(prompt)
    session.commit()
    session.refresh(prompt)

    response = client.get(f"/api/prompts/{prompt.id}/sample")

    assert response.status_code == 200
    payload = response.json()
    assert payload["sample_key"] == "date-detection"
    assert "Current date: {current_date}" in payload["user_template"]

    get_response = client.get(f"/api/prompts/{prompt.id}")
    assert get_response.json()["system_prompt"] == "manual date prompt"
    assert get_response.json()["user_template"] == "manual template"
    assert get_response.json()["sample_status"] == "legacy_sample"


def test_update_prompt_marks_exact_loaded_sample_current(client, session):
    delete_prompts_by_name(session, "Date Detection")
    prompt = Prompt(
        name="Date Detection",
        prompt_type="date",
        document_type_filter=None,
        system_prompt="manual date prompt",
        user_template="manual template",
        is_active=True,
    )
    session.add(prompt)
    session.commit()
    session.refresh(prompt)

    sample_response = client.get(f"/api/prompts/{prompt.id}/sample")
    assert sample_response.status_code == 200
    sample = sample_response.json()

    update_response = client.put(
        f"/api/prompts/{prompt.id}",
        json={
            "name": sample["name"],
            "prompt_type": sample["prompt_type"],
            "document_type_filter": sample["document_type_filter"],
            "system_prompt": sample["system_prompt"],
            "user_template": sample["user_template"],
            "is_active": not sample["is_active"],
        },
    )

    assert update_response.status_code == 200
    get_response = client.get(f"/api/prompts/{prompt.id}")
    payload = get_response.json()
    assert payload["sample_status"] == "sample_current"
    assert payload["sample_key"] == "date-detection"
    assert payload["sample_hash"] == sample["sample_hash"]
    assert payload["is_active"] is (not sample["is_active"])


def test_update_prompt_treats_empty_type_filter_as_sample_null(client, session):
    delete_prompts_by_name(session, "OCR Fix")
    prompt = Prompt(
        name="OCR Fix",
        prompt_type="ocr_fix",
        document_type_filter="",
        system_prompt="manual ocr fix prompt",
        user_template="manual template",
        is_active=True,
    )
    session.add(prompt)
    session.commit()
    session.refresh(prompt)

    sample_response = client.get(f"/api/prompts/{prompt.id}/sample")
    assert sample_response.status_code == 200
    sample = sample_response.json()
    assert sample["document_type_filter"] is None

    update_response = client.put(
        f"/api/prompts/{prompt.id}",
        json={
            "name": sample["name"],
            "prompt_type": sample["prompt_type"],
            "document_type_filter": "",
            "system_prompt": sample["system_prompt"],
            "user_template": sample["user_template"],
            "is_active": sample["is_active"],
        },
    )

    assert update_response.status_code == 200
    payload = client.get(f"/api/prompts/{prompt.id}").json()
    assert payload["document_type_filter"] is None
    assert payload["sample_status"] == "sample_current"
    assert payload["sample_key"] == "ocr-fix"


def test_sample_status_ignores_trailing_prompt_whitespace(client, session):
    delete_prompts_by_name(session, "OCR Fix")
    seed_response = client.post("/api/prompts/load-samples")
    assert seed_response.status_code == 200

    prompt = session.exec(select(Prompt).where(Prompt.name == "OCR Fix")).one()
    prompt.user_template = "OCR Text:  \r\n{content}"
    session.add(prompt)
    session.commit()

    payload = client.get(f"/api/prompts/{prompt.id}").json()
    assert payload["sample_status"] == "sample_current"
