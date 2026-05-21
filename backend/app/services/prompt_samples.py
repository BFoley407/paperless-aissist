"""Helpers for bundled prompt sample metadata and status."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fastapi import HTTPException

from ..models import Prompt

SAMPLE_FIELDS = (
    "name",
    "prompt_type",
    "document_type_filter",
    "system_prompt",
    "user_template",
    "is_active",
)
SAMPLE_STATUS_FIELDS = (
    "name",
    "prompt_type",
    "document_type_filter",
    "system_prompt",
    "user_template",
)


def examples_dir() -> Path:
    return Path(__file__).parent.parent.parent.parent / "examples" / "prompts"


def sample_key_for_file(path: Path) -> str:
    return path.stem


def sample_payload(sample: dict) -> dict:
    return {field: normalize_prompt_value(field, sample.get(field)) for field in SAMPLE_FIELDS}


def normalize_prompt_value(field: str, value):
    if field == "document_type_filter" and value == "":
        return None
    if field in {"system_prompt", "user_template"} and isinstance(value, str):
        return "\n".join(line.rstrip() for line in value.replace("\r\n", "\n").replace("\r", "\n").split("\n"))
    return value


def sample_hash(sample: dict) -> str:
    encoded = json.dumps(
        {field: normalize_prompt_value(field, sample.get(field)) for field in SAMPLE_STATUS_FIELDS},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_samples() -> dict[str, dict]:
    sample_dir = examples_dir()
    if not sample_dir.exists():
        raise HTTPException(status_code=404, detail="Examples directory not found")

    samples: dict[str, dict] = {}
    for json_file in sorted(sample_dir.glob("*.json")):
        with open(json_file, encoding="utf-8") as f:
            sample = json.load(f)
        sample["sample_key"] = sample_key_for_file(json_file)
        sample["sample_hash"] = sample_hash(sample)
        samples[sample["sample_key"]] = sample
    return samples


def find_sample_for_prompt(prompt: Prompt, samples: dict[str, dict]) -> dict | None:
    if prompt.sample_key and prompt.sample_key in samples:
        return samples[prompt.sample_key]
    return next((sample for sample in samples.values() if sample["name"] == prompt.name), None)


def prompt_payload(prompt: Prompt) -> dict:
    return {
        field: normalize_prompt_value(field, getattr(prompt, field))
        for field in SAMPLE_STATUS_FIELDS
    }


def prompt_hash(prompt: Prompt) -> str:
    encoded = json.dumps(
        prompt_payload(prompt),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sample_status(prompt: Prompt, sample: dict | None) -> str:
    if sample is None:
        return "custom"
    current_hash = prompt_hash(prompt)
    if current_hash == sample["sample_hash"]:
        return "sample_current"
    if prompt.sample_hash is None:
        return "legacy_sample"
    if current_hash == prompt.sample_hash:
        return "sample_update_available"
    return "modified"
