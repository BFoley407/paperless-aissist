"""Tests for shipped prompt sample JSON files."""

import json
from pathlib import Path


PROMPTS_DIR = Path(__file__).resolve().parents[2] / "examples" / "prompts"


def load_prompt(filename: str) -> dict:
    with open(PROMPTS_DIR / filename, encoding="utf-8") as handle:
        return json.load(handle)


def test_active_ocr_fix_prompt_preserves_original_language():
    prompt = load_prompt("ocr-fix.json")
    combined = f"{prompt['system_prompt']}\n{prompt['user_template']}"

    assert prompt["is_active"] is True
    assert "Preserve the original language" in prompt["system_prompt"]
    assert "Do not translate" in prompt["system_prompt"]
    assert "German document" not in combined
    assert "German text" not in combined
    assert "Deutsch" not in combined


def test_active_title_prompt_uses_language_neutral_correspondent_pattern():
    prompt = load_prompt("title-generation.json")
    system_prompt = prompt["system_prompt"]

    assert prompt["is_active"] is True
    assert '"[document type] from [correspondent] - [date]"' in system_prompt
    assert "Paperless correspondent" in system_prompt
    assert "Keep the title in the document's language" in system_prompt
    assert "For English documents, use English document type words" in system_prompt
    assert "For German documents, use German document type words" in system_prompt
    assert "Dokumenttyp von Absender - Datum" not in system_prompt
    assert "content is likely in German" not in system_prompt


def test_active_title_prompt_keeps_multilingual_examples():
    prompt = load_prompt("title-generation.json")
    system_prompt = prompt["system_prompt"]

    assert 'English invoice: "Invoice from Amazon - 2026-01-15"' in system_prompt
    assert 'German invoice: "Rechnung von Amazon - 2026-01-15"' in system_prompt
    assert 'English letter: "Letter from BMW - 2025-12-24"' in system_prompt
    assert 'German letter: "Brief von BMW - 2025-12-24"' in system_prompt


def test_inactive_localized_rechnung_sample_remains_inactive():
    prompt = load_prompt("type-specific-rechnung.json")

    assert prompt["prompt_type"] == "type_specific"
    assert prompt["document_type_filter"] == "Rechnung"
    assert prompt["is_active"] is False


def test_active_date_detection_prompt_requests_strict_safe_json():
    prompt = load_prompt("date-detection.json")
    system_prompt = prompt["system_prompt"]

    assert prompt["prompt_type"] == "date"
    assert prompt["is_active"] is True
    assert "strict JSON" in system_prompt
    assert "due date" in system_prompt
    assert "payment date" in system_prompt
    assert "service period" in system_prompt
    assert "added date" in system_prompt
    assert "modified date" in system_prompt
    assert "{created_date}" in prompt["user_template"]
