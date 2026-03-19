from __future__ import annotations

from typing import Any

from ..adapters import run_t20_sheet_builder
from ..contracts import (
    CharacterGenerationRequest,
    CharacterGenerationResult,
    InvalidCharacterBuildError,
)
from ..shared.common import ability_modifier, normalize_character_sheet_data, now_iso

JsonObject = dict[str, Any]

SUPPORTED_BRIDGE_ORIGINS = {"acolyte", "acolito", "animalsfriend", "animals_friend", "amigo dos animais", "amigo_dos_animais"}
SUPPORTED_BUILD_CHOICE_KEYS = {
    "role_skill_choices",
    "role_options",
    "intelligence_skill_choices",
    "race_choices",
    "origin_choices",
    "equipment_choices",
}


def _class_profile(class_name: str) -> JsonObject:
    normalized = str(class_name or "").strip().casefold()
    profiles: dict[str, JsonObject] = {
        "guerreiro": {"pv_base": 20, "pm_base": 3, "key_ability": "forca", "skills": ["Luta", "Fortitude", "Atletismo", "Iniciativa"]},
        "warrior": {"pv_base": 20, "pm_base": 3, "key_ability": "forca", "skills": ["Luta", "Fortitude", "Atletismo", "Iniciativa"]},
        "arcanista": {"pv_base": 8, "pm_base": 6, "key_ability": "inteligencia", "skills": ["Misticismo", "Vontade", "Conhecimento", "Iniciativa"]},
        "arcanist": {"pv_base": 8, "pm_base": 6, "key_ability": "inteligencia", "skills": ["Misticismo", "Vontade", "Conhecimento", "Iniciativa"]},
    }
    return profiles.get(normalized, {"pv_base": 12, "pm_base": 4, "key_ability": "forca", "skills": ["Percepcao", "Fortitude", "Reflexos"]})


def _normalize_input_attributes(incoming: JsonObject) -> JsonObject:
    attrs = {
        "forca": 10,
        "destreza": 10,
        "constituicao": 10,
        "inteligencia": 10,
        "sabedoria": 10,
        "carisma": 10,
    }
    if isinstance(incoming, dict):
        for key, value in incoming.items():
            if key in attrs and isinstance(value, int):
                attrs[key] = max(1, min(30, value))
    return attrs


def _default_origin(attrs: JsonObject) -> str:
    return "acolyte" if int(attrs.get("sabedoria", 10)) >= 12 else "animals_friend"


def _validate_origin(origin: str, attrs: JsonObject) -> None:
    if origin.casefold() in {"acolyte", "acolito"} and int(attrs.get("sabedoria", 10)) < 12:
        raise InvalidCharacterBuildError("Origem 'acolyte' exige Sabedoria 12+ para nao falhar na engine.")


def _build_fallback_sheet(request: CharacterGenerationRequest, warnings: list[str], bridge_error: str | None) -> JsonObject:
    attrs = request.attributes
    profile = _class_profile(request.class_name)
    con_mod = ability_modifier(int(attrs["constituicao"]))
    dex_mod = ability_modifier(int(attrs["destreza"]))
    key_ability = str(profile["key_ability"])
    key_mod = ability_modifier(int(attrs.get(key_ability, 10)))
    half_level = max(0, request.level // 2)
    pv_total = max(1, int(profile["pv_base"]) + con_mod + max(0, request.level - 1) * max(1, int(profile["pv_base"]) // 2 + con_mod))
    pm_total = max(0, int(profile["pm_base"]) + max(0, request.level - 1) * max(1, int(profile["pm_base"]) // 2))
    defense = 10 + dex_mod + half_level
    initiative = dex_mod + half_level
    perception = ability_modifier(int(attrs["sabedoria"])) + half_level
    attack = max(ability_modifier(int(attrs["forca"])), dex_mod, key_mod) + half_level
    resistances = {
        "fortitude": con_mod + half_level,
        "reflexes": dex_mod + half_level,
        "will": ability_modifier(int(attrs["sabedoria"])) + half_level,
    }
    sheet = {
        "schema_version": 2,
        "system": "tormenta20-base",
        "builder": "fallback",
        "name": request.name,
        "world": request.world,
        "race": request.race,
        "class_name": request.class_name,
        "origin": request.origin or "",
        "level": request.level,
        "concept": request.concept or "A definir",
        "attributes": attrs,
        "derived": {
            "pv": pv_total,
            "pm": pm_total,
            "defense": defense,
            "initiative": initiative,
            "perception": perception,
            "attack_base": attack,
            "resistances": resistances,
        },
        "trained_skills": [{"name": skill, "total": 0, "trained": True, "attribute": key_ability} for skill in list(profile["skills"])[:8]],
        "top_skills": [{"name": skill, "total": 0, "trained": True, "attribute": key_ability} for skill in list(profile["skills"])[:8]],
        "attacks": [],
        "abilities": [],
        "build_steps": [],
        "recommended_skills": list(profile["skills"]),
        "serialized_character": {},
        "displacement": 9,
        "current_cargo": 0,
        "max_cargo": 10 + max(0, ability_modifier(int(attrs["forca"]))) * 5,
        "carry_capacity": (10 + max(0, ability_modifier(int(attrs["forca"]))) * 5) * 2,
        "proficiencies": [],
        "spells": [],
        "powers": [],
        "key_ability": key_ability,
        "generation_warnings": warnings[:],
        "generation_source_details": {
            "requested_engine": request.prefer_engine,
            "bridge_error": bridge_error,
            "fallback_reason": bridge_error or "fallback requested",
        },
        "updated_at": now_iso(),
    }
    return normalize_character_sheet_data(sheet)


def _build_character_markdown(sheet: JsonObject) -> str:
    attrs = sheet["attributes"]
    mods = sheet["modifiers"]
    derived = sheet["derived"]
    resistances = derived.get("resistances", {})
    skills = sheet.get("recommended_skills", [])
    warnings = sheet.get("generation_warnings", [])
    return f"""# Ficha Tormenta20 - {sheet['name']}

- Mundo: {sheet['world']}
- Raca: {sheet['race']}
- Classe: {sheet['class_name']}
- Origem: {sheet.get('origin', '')}
- Nivel: {sheet['level']}
- Conceito: {sheet['concept']}
- Builder: {sheet['builder']}

## Atributos
- Forca: {attrs['forca']} ({mods['forca']:+d})
- Destreza: {attrs['destreza']} ({mods['destreza']:+d})
- Constituicao: {attrs['constituicao']} ({mods['constituicao']:+d})
- Inteligencia: {attrs['inteligencia']} ({mods['inteligencia']:+d})
- Sabedoria: {attrs['sabedoria']} ({mods['sabedoria']:+d})
- Carisma: {attrs['carisma']} ({mods['carisma']:+d})

## Derivados
- PV: {derived.get('pv')}
- PM: {derived.get('pm')}
- Defesa: {derived.get('defense')}
- Iniciativa: {derived.get('initiative')}
- Percepcao: {derived.get('perception')}

## Resistencias
- Fortitude: {resistances.get('fortitude', '')}
- Reflexos: {resistances.get('reflexes', '')}
- Vontade: {resistances.get('will', '')}

## Pericias
""" + "\n".join(f"- {skill}" for skill in skills) + """

## Avisos
""" + ("\n".join(f"- {warning}" for warning in warnings) if warnings else "- Nenhum")


def _build_request(params: JsonObject) -> CharacterGenerationRequest:
    name = str(params.get("name") or params.get("nome", "")).strip()
    if not name:
        raise InvalidCharacterBuildError("Informe o nome do personagem.")
    attrs = _normalize_input_attributes(params.get("attributes") if isinstance(params.get("attributes"), dict) else {})
    origin = str(params.get("origin") or params.get("origem", "")).strip() or None
    if origin:
        _validate_origin(origin, attrs)
    else:
        origin = _default_origin(attrs)
    level = int(params.get("level") or params.get("nivel") or 1)
    return CharacterGenerationRequest(
        name=name,
        world=str(params.get("world", "tormenta20")).strip() or "tormenta20",
        race=str(params.get("race") or params.get("raca", "")).strip() or "A definir",
        class_name=(
            str(params.get("class_name", "")).strip()
            or str(params.get("class", "")).strip()
            or str(params.get("character_class", "")).strip()
            or str(params.get("classe", "")).strip()
            or "A definir"
        ),
        origin=origin,
        level=max(1, min(20, level)),
        concept=str(params.get("concept", "")).strip() or "A definir",
        attributes=attrs,
        build_choices=params.get("build_choices") if isinstance(params.get("build_choices"), dict) else {},
        generation_mode=str(params.get("generation_mode", "auto")).strip() or "auto",
        prefer_engine=str(params.get("prefer_engine", "auto")).strip() or "auto",
    )


def generate_character_sheet(params: JsonObject) -> CharacterGenerationResult:
    request = _build_request(params)
    warnings: list[str] = []
    errors: list[str] = []
    applied_choices: JsonObject = {}
    unsupported_fields: list[str] = []

    if request.build_choices:
        for key in ("spell_choices", "devotion_choices"):
            if key in request.build_choices:
                unsupported_fields.append(key)
                warnings.append(f"{key} ainda nao e suportado e foi ignorado.")
        for key in request.build_choices:
            if key not in SUPPORTED_BUILD_CHOICE_KEYS and key not in {"spell_choices", "devotion_choices"}:
                unsupported_fields.append(key)
                warnings.append(f"{key} nao faz parte do contrato suportado e foi ignorado.")

    bridge_supported = request.level == 1 and (request.origin or "").casefold() in SUPPORTED_BRIDGE_ORIGINS
    if request.level > 1:
        warnings.append("t20-sheet-builder adapter currently supports only level 1 builds; usando fallback versionado.")
    if request.prefer_engine != "fallback" and not bridge_supported:
        if request.level != 1:
            bridge_error = "t20-sheet-builder adapter currently supports only level 1 builds."
        else:
            bridge_error = f"Origem '{request.origin}' ainda nao esta suportada pela bridge automatica."
    else:
        bridge_error = None
    bridge_data: JsonObject | None = None

    if request.prefer_engine != "fallback" and bridge_supported:
        bridge_data, bridge_error = run_t20_sheet_builder(
            {
                "name": request.name,
                "world": request.world,
                "race": request.race,
                "class_name": request.class_name,
                "origin": request.origin,
                "level": request.level,
                "concept": request.concept,
                "attributes": request.attributes,
                "build_choices": request.build_choices,
                "generation_mode": request.generation_mode,
            }
        )

    if bridge_data is not None:
        serialized_character = bridge_data.get("serialized_character")
        if not isinstance(serialized_character, dict):
            serialized_character = {}
        serialized_sheet = serialized_character.get("sheet", {}) if isinstance(serialized_character, dict) else {}
        applied_choices = bridge_data.get("applied_choices") if isinstance(bridge_data.get("applied_choices"), dict) else {}
        bridge_warnings = bridge_data.get("warnings")
        if isinstance(bridge_warnings, list):
            warnings.extend(str(item) for item in bridge_warnings if str(item).strip())
        sheet = normalize_character_sheet_data(
            {
                "schema_version": 2,
                "system": str(bridge_data.get("system", "tormenta20-t20-sheet-builder")),
                "builder": "t20-sheet-builder",
                "name": request.name,
                "world": request.world,
                "race": request.race,
                "class_name": request.class_name,
                "origin": request.origin or "",
                "level": int(bridge_data.get("level", request.level) or request.level),
                "concept": request.concept or "A definir",
                "attributes": bridge_data.get("attributes", {}),
                "derived": {
                    "pv": bridge_data.get("life_points"),
                    "pm": bridge_data.get("mana_points"),
                    "defense": bridge_data.get("defense"),
                },
                "trained_skills": bridge_data.get("trained_skills", []),
                "top_skills": bridge_data.get("top_skills", []),
                "attacks": bridge_data.get("attacks", []),
                "abilities": [],
                "build_steps": bridge_data.get("build_steps", []),
                "recommended_skills": [
                    item.get("name") for item in bridge_data.get("trained_skills", [])
                    if isinstance(item, dict) and item.get("name")
                ],
                "serialized_character": serialized_character,
                "displacement": serialized_sheet.get("displacement", 9) if isinstance(serialized_sheet, dict) else 9,
                "current_cargo": int(serialized_sheet.get("money", 0) or 0) if isinstance(serialized_sheet, dict) else 0,
                "max_cargo": 10 + max(0, int((bridge_data.get("attributes", {}) or {}).get("strength", 0) or 0)) * 5,
                "carry_capacity": (10 + max(0, int((bridge_data.get("attributes", {}) or {}).get("strength", 0) or 0)) * 5) * 2,
                "proficiencies": serialized_sheet.get("proficiencies", []) if isinstance(serialized_sheet, dict) else [],
                "spells": serialized_sheet.get("spells", []) if isinstance(serialized_sheet, dict) else [],
                "powers": (
                    list(serialized_sheet.get("generalPowers", []))
                    + list(serialized_sheet.get("rolePowers", []))
                    + list(serialized_sheet.get("originPowers", []))
                    + list(serialized_sheet.get("grantedPowers", []))
                ) if isinstance(serialized_sheet, dict) else [],
                "generation_warnings": warnings,
                "generation_source_details": {
                    "requested_engine": request.prefer_engine,
                    "requested_level": request.level,
                    "bridge_generated_level": int(bridge_data.get("level", 1) or 1),
                },
                "updated_at": now_iso(),
            }
        )
        status = "success"
        markdown = _build_character_markdown(sheet)
        return CharacterGenerationResult(
            source="t20-sheet-builder",
            status=status,
            normalized_sheet=sheet,
            serialized_character=serialized_character,
            warnings=warnings,
            errors=errors,
            applied_choices=applied_choices,
            unsupported_fields=unsupported_fields,
            markdown=markdown,
        )

    if request.generation_mode == "strict" and request.prefer_engine != "fallback":
        raise InvalidCharacterBuildError(bridge_error or "Nao foi possivel gerar a ficha com a engine solicitada.")

    if bridge_error:
        warnings.append(f"fallback ativo: {bridge_error}")
    if request.build_choices:
        used_keys = sorted(key for key in request.build_choices if key in SUPPORTED_BUILD_CHOICE_KEYS)
        if used_keys:
            warnings.append("build_choices suportado apenas parcialmente no fallback; escolhas foram registradas, mas nao aplicadas.")
    sheet = _build_fallback_sheet(request, warnings, bridge_error)
    markdown = _build_character_markdown(sheet)
    status = "partial" if (request.prefer_engine != "fallback" or request.level > 1) else "success"
    applied_choices = {
        "origin": request.origin,
        "generation_mode": request.generation_mode,
        "requested_build_choices": request.build_choices,
    }
    return CharacterGenerationResult(
        source="fallback",
        status=status,
        normalized_sheet=sheet,
        serialized_character=None,
        warnings=warnings,
        errors=errors,
        applied_choices=applied_choices,
        unsupported_fields=unsupported_fields,
        markdown=markdown,
    )
