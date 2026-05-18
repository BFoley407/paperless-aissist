from app.models import Prompt


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
