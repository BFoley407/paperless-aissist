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
