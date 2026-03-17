from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

JsonObject = dict[str, Any]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def humanize_identifier(value: str) -> str:
    compact = str(value or "").strip()
    if not compact:
        return ""
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", compact.replace("_", " ").replace("-", " "))
    return " ".join(part.capitalize() for part in spaced.split())


def ability_modifier(score: int) -> int:
    return int((int(score) - 10) // 2)


def json_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def normalize_character_sheet_data(sheet: JsonObject) -> JsonObject:
    attrs = sheet.get("attributes")
    if not isinstance(attrs, dict):
        attrs = {}
    raw_attr_values = [value for value in attrs.values() if isinstance(value, (int, float))]
    attrs_are_modifiers = bool(raw_attr_values) and all(-5 <= float(value) <= 10 for value in raw_attr_values)

    def score_value(*keys: str) -> int:
        for key in keys:
            raw = attrs.get(key)
            if isinstance(raw, (int, float)):
                if attrs_are_modifiers:
                    return int(10 + int(raw) * 2)
                return int(raw)
        return 0

    normalized_attrs = {
        "forca": score_value("forca", "strength"),
        "destreza": score_value("destreza", "dexterity"),
        "constituicao": score_value("constituicao", "constitution"),
        "inteligencia": score_value("inteligencia", "intelligence"),
        "sabedoria": score_value("sabedoria", "wisdom"),
        "carisma": score_value("carisma", "charisma"),
    }

    derived = sheet.get("derived")
    if not isinstance(derived, dict):
        derived = {}

    normalized: JsonObject = dict(sheet)
    normalized["attributes"] = normalized_attrs
    normalized["modifiers"] = {
        "forca": ability_modifier(normalized_attrs["forca"]),
        "destreza": ability_modifier(normalized_attrs["destreza"]),
        "constituicao": ability_modifier(normalized_attrs["constituicao"]),
        "inteligencia": ability_modifier(normalized_attrs["inteligencia"]),
        "sabedoria": ability_modifier(normalized_attrs["sabedoria"]),
        "carisma": ability_modifier(normalized_attrs["carisma"]),
    }
    normalized["derived"] = {
        "pv": derived.get("pv"),
        "pm": derived.get("pm"),
        "defense": derived.get("defense"),
        "initiative": derived.get("initiative"),
        "perception": derived.get("perception"),
        "attack_base": derived.get("attack_base"),
        "resistances": derived.get("resistances", {}),
    }
    for key in (
        "trained_skills",
        "top_skills",
        "attacks",
        "abilities",
        "build_steps",
        "recommended_skills",
        "proficiencies",
        "spells",
        "powers",
    ):
        normalized[key] = json_list(normalized.get(key))
    if not isinstance(normalized.get("serialized_character"), dict):
        normalized["serialized_character"] = {}
    normalized["displacement"] = int(normalized.get("displacement", 9) or 9)
    normalized["current_cargo"] = int(normalized.get("current_cargo", 0) or 0)
    normalized["max_cargo"] = int(normalized.get("max_cargo", 0) or 0)
    normalized["carry_capacity"] = int(normalized.get("carry_capacity", 0) or 0)
    normalized["updated_at"] = str(normalized.get("updated_at") or now_iso())
    return normalized
