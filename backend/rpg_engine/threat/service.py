from __future__ import annotations

import math
from typing import Any

from ..contracts import InvalidThreatDefinitionError, ThreatGenerationRequest, ThreatGenerationResult
from ..shared.common import now_iso

JsonObject = dict[str, Any]

THREAT_SOLO_COMBAT_TABLE: dict[str, JsonObject] = {
    "1/4": {"attack_value": 6, "average_damage": 8, "defense": 11, "strong_save": 3, "medium_save": 0, "weak_save": -2, "hit_points": 7, "standard_effect_dc": 12},
    "1/3": {"attack_value": 6, "average_damage": 9, "defense": 12, "strong_save": 4, "medium_save": 1, "weak_save": -1, "hit_points": 10, "standard_effect_dc": 12},
    "1/2": {"attack_value": 7, "average_damage": 10, "defense": 14, "strong_save": 6, "medium_save": 3, "weak_save": -1, "hit_points": 15, "standard_effect_dc": 13},
    "1": {"attack_value": 9, "average_damage": 15, "defense": 16, "strong_save": 11, "medium_save": 5, "weak_save": 0, "hit_points": 35, "standard_effect_dc": 14},
    "2": {"attack_value": 12, "average_damage": 18, "defense": 19, "strong_save": 13, "medium_save": 7, "weak_save": 2, "hit_points": 70, "standard_effect_dc": 16},
    "3": {"attack_value": 14, "average_damage": 21, "defense": 21, "strong_save": 15, "medium_save": 9, "weak_save": 3, "hit_points": 105, "standard_effect_dc": 17},
    "4": {"attack_value": 16, "average_damage": 24, "defense": 23, "strong_save": 16, "medium_save": 10, "weak_save": 4, "hit_points": 140, "standard_effect_dc": 18},
    "5": {"attack_value": 17, "average_damage": 40, "defense": 24, "strong_save": 17, "medium_save": 11, "weak_save": 5, "hit_points": 200, "standard_effect_dc": 20},
    "6": {"attack_value": 20, "average_damage": 56, "defense": 27, "strong_save": 18, "medium_save": 12, "weak_save": 6, "hit_points": 240, "standard_effect_dc": 22},
    "7": {"attack_value": 24, "average_damage": 62, "defense": 31, "strong_save": 20, "medium_save": 14, "weak_save": 7, "hit_points": 280, "standard_effect_dc": 24},
    "8": {"attack_value": 26, "average_damage": 68, "defense": 33, "strong_save": 21, "medium_save": 15, "weak_save": 8, "hit_points": 320, "standard_effect_dc": 26},
    "9": {"attack_value": 27, "average_damage": 74, "defense": 34, "strong_save": 21, "medium_save": 15, "weak_save": 9, "hit_points": 360, "standard_effect_dc": 28},
    "10": {"attack_value": 29, "average_damage": 80, "defense": 36, "strong_save": 22, "medium_save": 16, "weak_save": 10, "hit_points": 400, "standard_effect_dc": 30},
    "11": {"attack_value": 34, "average_damage": 130, "defense": 41, "strong_save": 24, "medium_save": 18, "weak_save": 11, "hit_points": 550, "standard_effect_dc": 31},
    "12": {"attack_value": 36, "average_damage": 144, "defense": 43, "strong_save": 26, "medium_save": 20, "weak_save": 12, "hit_points": 600, "standard_effect_dc": 33},
    "13": {"attack_value": 37, "average_damage": 158, "defense": 44, "strong_save": 26, "medium_save": 20, "weak_save": 13, "hit_points": 650, "standard_effect_dc": 35},
    "14": {"attack_value": 39, "average_damage": 172, "defense": 46, "strong_save": 28, "medium_save": 22, "weak_save": 14, "hit_points": 700, "standard_effect_dc": 38},
    "15": {"attack_value": 43, "average_damage": 186, "defense": 50, "strong_save": 28, "medium_save": 22, "weak_save": 15, "hit_points": 750, "standard_effect_dc": 40},
    "16": {"attack_value": 46, "average_damage": 200, "defense": 53, "strong_save": 30, "medium_save": 24, "weak_save": 16, "hit_points": 800, "standard_effect_dc": 42},
    "17": {"attack_value": 48, "average_damage": 214, "defense": 55, "strong_save": 31, "medium_save": 25, "weak_save": 17, "hit_points": 850, "standard_effect_dc": 44},
    "18": {"attack_value": 50, "average_damage": 228, "defense": 57, "strong_save": 33, "medium_save": 27, "weak_save": 18, "hit_points": 900, "standard_effect_dc": 46},
    "19": {"attack_value": 52, "average_damage": 242, "defense": 59, "strong_save": 34, "medium_save": 28, "weak_save": 19, "hit_points": 950, "standard_effect_dc": 48},
    "20": {"attack_value": 54, "average_damage": 256, "defense": 61, "strong_save": 36, "medium_save": 30, "weak_save": 20, "hit_points": 1000, "standard_effect_dc": 50},
    "S": {"attack_value": 56, "average_damage": 280, "defense": 64, "strong_save": 38, "medium_save": 32, "weak_save": 22, "hit_points": 1200, "standard_effect_dc": 52},
    "S+": {"attack_value": 58, "average_damage": 300, "defense": 66, "strong_save": 40, "medium_save": 34, "weak_save": 24, "hit_points": 1400, "standard_effect_dc": 54},
}


def _parse_nd(raw_value: str) -> tuple[str, float]:
    value = str(raw_value or "").strip().upper()
    mapping = {"1/4": 0.25, "1/3": 0.33, "1/2": 0.5, "S": 20.0, "S+": 21.0}
    if value in mapping:
        return value, mapping[value]
    if value.isdigit():
        numeric = float(int(value))
        if value in THREAT_SOLO_COMBAT_TABLE:
            return value, numeric
    raise InvalidThreatDefinitionError("challenge_level must be one of 1/4, 1/3, 1/2, 1-20, S or S+")


def _challenge_tier(nd_value: float) -> str:
    if 0.25 <= nd_value <= 4:
        return "Iniciante"
    if nd_value <= 10:
        return "Veterano"
    if nd_value <= 16:
        return "Campeao"
    if nd_value <= 20:
        return "Lenda"
    return "L+"


def _combat_stats(role: str, challenge_level: str, has_mana_points: bool) -> JsonObject:
    normalized_challenge, _ = _parse_nd(challenge_level)
    base = dict(THREAT_SOLO_COMBAT_TABLE[normalized_challenge])
    role_key = str(role or "Solo").strip().casefold()
    if role_key == "lacaio":
        base["attack_value"] = max(1, base["attack_value"] - 2)
        base["average_damage"] = max(1, base["average_damage"] - 8)
        base["hit_points"] = max(1, int(base["hit_points"] * 0.6))
        base["defense"] = max(10, base["defense"] - 1)
    elif role_key == "especial":
        base["attack_value"] = max(1, base["attack_value"] - 1)
        base["average_damage"] = max(1, base["average_damage"] - 2)
        base["standard_effect_dc"] = int(base["standard_effect_dc"]) + 2
    if has_mana_points:
        base["mana_points"] = int(math.ceil(_parse_nd(challenge_level)[1] * 3))
    else:
        base["mana_points"] = 0
    return base


def _default_attributes(role: str) -> JsonObject:
    role_key = str(role or "Solo").strip().casefold()
    if role_key == "lacaio":
        return {"forca": 2, "destreza": 1, "constituicao": 1, "inteligencia": 0, "sabedoria": 0, "carisma": -1}
    if role_key == "especial":
        return {"forca": 1, "destreza": 2, "constituicao": 1, "inteligencia": 2, "sabedoria": 1, "carisma": 1}
    return {"forca": 3, "destreza": 1, "constituicao": 3, "inteligencia": 0, "sabedoria": 1, "carisma": 0}


def _default_resistances(role: str) -> JsonObject:
    role_key = str(role or "Solo").strip().casefold()
    if role_key == "especial":
        return {"Fortitude": "medium", "Reflexos": "strong", "Vontade": "weak"}
    if role_key == "lacaio":
        return {"Fortitude": "weak", "Reflexos": "medium", "Vontade": "strong"}
    return {"Fortitude": "strong", "Reflexos": "medium", "Vontade": "weak"}


def _recommended_ability_count(challenge_level: str, role: str) -> JsonObject:
    _, nd_value = _parse_nd(challenge_level)
    multiplier = 1 if nd_value <= 4 else 2 if nd_value <= 10 else 3 if nd_value <= 16 else 4 if nd_value <= 20 else 5
    if str(role or "Solo").strip().casefold() == "especial":
        return {"min": multiplier * 2, "max": multiplier * 3, "tier": _challenge_tier(nd_value)}
    return {"min": multiplier, "max": multiplier * 2, "tier": _challenge_tier(nd_value)}


def _qualities(role: str, challenge_level: str, combat_stats: JsonObject) -> list[str]:
    _, nd_value = _parse_nd(challenge_level)
    qualities = [
        f"Ataque base sugerido: {combat_stats.get('attack_value')}.",
        f"Dano medio sugerido: {combat_stats.get('average_damage')}.",
        f"CD padrao sugerida: {combat_stats.get('standard_effect_dc')}.",
    ]
    role_key = str(role or "Solo").strip().casefold()
    if role_key == "solo":
        qualities.append("Considere ao menos 1 reacao e 1 efeito de area para sustentar o combate solo.")
    if role_key == "especial":
        qualities.append("Priorize efeitos de controle, mobilidade ou ruptura de acao para marcar a identidade especial.")
    if role_key == "lacaio":
        qualities.append("Mantenha ataques simples e dano comprimido; o perigo do lacaio vem do numero.")
    if nd_value >= 15:
        qualities.append("Para ND alto, inclua uma habilidade de fase final ou escalada.")
    return qualities


def _generated_abilities(role: str, challenge_level: str, combat_stats: JsonObject, has_mana_points: bool) -> list[JsonObject]:
    _, nd_value = _parse_nd(challenge_level)
    mana_cost = int(combat_stats.get("mana_points", 0) or 0)
    role_key = str(role or "Solo").strip().casefold()
    abilities = [
        {"category": "ofensiva", "name": "Golpe Assolador", "summary": f"Causa cerca de {int(combat_stats.get('average_damage', 1))} de dano.", "action_type": "Padrao", "pm_cost": max(0, mana_cost // 6) if has_mana_points else 0},
        {"category": "controle", "name": "Pressao Tatica", "summary": f"Impoe condicao com CD {int(combat_stats.get('standard_effect_dc', 10))}.", "action_type": "Padrao", "pm_cost": max(0, mana_cost // 8) if has_mana_points else 0},
    ]
    if role_key != "lacaio":
        abilities.append({"category": "mobilidade", "name": "Reposicionamento Hostil", "summary": "Move-se ou desloca inimigos.", "action_type": "Livre" if role_key == "especial" else "Movimento", "pm_cost": max(0, mana_cost // 10) if has_mana_points else 0})
    if role_key in {"solo", "especial"}:
        abilities.append({"category": "defesa", "name": "Resposta Instintiva", "summary": "Reacao defensiva para reduzir dano.", "action_type": "Reacao", "pm_cost": max(0, mana_cost // 12) if has_mana_points else 0})
    if nd_value >= 11:
        abilities.append({"category": "fase", "name": "Escalada de Confronto", "summary": "Entra em fase mais agressiva ao perder PV.", "action_type": "Livre", "pm_cost": max(0, mana_cost // 5) if has_mana_points else 0})
    return abilities


def _boss_features(challenge_level: str, combat_stats: JsonObject, has_mana_points: bool) -> JsonObject:
    _, nd_value = _parse_nd(challenge_level)
    effect_dc = int(combat_stats.get("standard_effect_dc", 10) or 10)
    avg_damage = int(combat_stats.get("average_damage", 1) or 1)
    hit_points = int(combat_stats.get("hit_points", 1) or 1)
    mana_points = int(combat_stats.get("mana_points", 0) or 0)
    return {
        "reactions": [{"name": "Contra-Golpe Instintivo", "summary": f"Quando sofre pico de dano, reage com teste CD {effect_dc}.", "uses_per_round": 3, "pm_cost": max(0, mana_points // 12) if has_mana_points else 0}],
        "legendary_actions": [
            {"name": "Pressao Lendaria", "cost": 1, "summary": f"Causa cerca de {max(1, avg_damage // 3)} de dano."},
            {"name": "Ruptura de Ritmo", "cost": 2, "summary": f"Forca teste CD {effect_dc - 2}."},
            {"name": "Impulso Final", "cost": 3, "summary": "Ativa poder de area ou acelera a fase final."},
        ],
        "phases": [
            {"threshold": "66%", "summary": f"Abaixo de {int(hit_points * 0.66)}, entra em fase de pressao crescente."},
            {"threshold": "33%", "summary": f"Abaixo de {int(hit_points * 0.33)}, destrava pico ofensivo."},
        ],
        "defeat_condition": f"Ao cair, desencadeia um efeito residual final com teste CD {effect_dc}.",
        "boss_tuning": {"recommended_hit_point_breakpoints": [int(hit_points * 0.66), int(hit_points * 0.33)], "nd_is_high": nd_value >= 11},
    }


def _skills(challenge_level: str, attributes: JsonObject) -> list[JsonObject]:
    _, nd_value = _parse_nd(challenge_level)
    training_bonus = 2 if nd_value <= 6 else 4 if nd_value <= 14 else 6
    skill_map = [
        ("Percepcao", "sabedoria", True, 2),
        ("Iniciativa", "destreza", True, 0),
        ("Fortitude", "constituicao", True, 0),
        ("Reflexos", "destreza", True, 0),
        ("Vontade", "sabedoria", True, 0),
        ("Intimidacao", "carisma", False, 2),
    ]
    result = []
    half_nd = int(math.floor(nd_value / 2))
    for name, attr, trained, custom_bonus in skill_map:
        total = half_nd + int(attributes.get(attr, 0) or 0) + (training_bonus if trained else 0) + custom_bonus
        result.append({"name": name, "attribute": attr, "trained": trained, "custom_bonus": custom_bonus, "total": total})
    return result


def _default_attacks(name: str, combat_stats: JsonObject, role: str) -> list[JsonObject]:
    attack_bonus = int(combat_stats.get("attack_value", 0) or 0)
    average_damage = int(combat_stats.get("average_damage", 0) or 0)
    role_key = str(role or "Solo").strip().casefold()
    if role_key == "lacaio":
        attacks = [{"name": "Golpe de Investida", "attack_bonus": attack_bonus, "damage": f"{max(1, average_damage - 4)} dano", "action_type": "Padrao"}]
    elif role_key == "especial":
        attacks = [
            {"name": "Ataque Principal", "attack_bonus": attack_bonus, "damage": f"{average_damage} dano", "action_type": "Padrao"},
            {"name": "Efeito Especial", "attack_bonus": attack_bonus - 2, "damage": f"{max(1, average_damage - 6)} dano + condicao", "action_type": "Completa"},
        ]
    else:
        attacks = [
            {"name": "Ataque Principal", "attack_bonus": attack_bonus, "damage": f"{average_damage} dano", "action_type": "Padrao"},
            {"name": "Golpe Devastador", "attack_bonus": attack_bonus - 2, "damage": f"{max(1, average_damage + 8)} dano", "action_type": "Completa"},
        ]
    for item in attacks:
        item["source_hint"] = f"Gerado automaticamente para {name}"
    return attacks


def _build_request(params: JsonObject) -> ThreatGenerationRequest:
    name = str(params.get("name", "")).strip()
    if not name:
        raise InvalidThreatDefinitionError("Informe o nome da ameaca.")
    challenge_level = str(params.get("challenge_level", "")).strip()
    if not challenge_level:
        raise InvalidThreatDefinitionError("Informe o ND da ameaca.")
    _parse_nd(challenge_level)
    return ThreatGenerationRequest(
        name=name,
        world=str(params.get("world", "tormenta20")).strip() or "tormenta20",
        threat_type=str(params.get("threat_type", "Monstro")).strip() or "Monstro",
        size=str(params.get("size", "Grande")).strip() or "Grande",
        role=str(params.get("role", "Solo")).strip() or "Solo",
        challenge_level=challenge_level,
        concept=str(params.get("concept", "")).strip() or "A definir",
        has_mana_points=bool(params.get("has_mana_points", True)),
        is_boss=bool(params.get("is_boss", False)),
        displacement=str(params.get("displacement", "9 m")).strip() or "9 m",
        attributes=params.get("attributes") if isinstance(params.get("attributes"), dict) else None,
        attacks_override=params.get("attacks_override") if isinstance(params.get("attacks_override"), list) else [],
        abilities_override=params.get("abilities_override") if isinstance(params.get("abilities_override"), list) else [],
        spells_override=params.get("spells_override") if isinstance(params.get("spells_override"), list) else [],
        special_qualities=str(params.get("special_qualities", "")).strip(),
        equipment=str(params.get("equipment", "")).strip(),
        treasure_level=str(params.get("treasure_level", "Padrao")).strip() or "Padrao",
        generation_mode=str(params.get("generation_mode", "suggested")).strip() or "suggested",
    )


def _build_markdown(threat: JsonObject) -> str:
    combat = threat.get("combat_stats", {})
    attrs = threat.get("attributes", {})
    skills = threat.get("skills", [])
    attacks = threat.get("attacks", [])
    abilities = threat.get("abilities", [])
    warnings = threat.get("generation_warnings", [])
    return "\n".join(
        [
            f"# Ameaca Tormenta20 - {threat.get('name', '')}",
            "",
            f"- Mundo: {threat.get('world', '')}",
            f"- Tipo: {threat.get('type', '')}",
            f"- Tamanho: {threat.get('size', '')}",
            f"- Papel: {threat.get('role', '')}",
            f"- ND: {threat.get('challenge_level', '')}",
            f"- Tier: {threat.get('challenge_tier', '')}",
            f"- Builder: {threat.get('builder', '')}",
            "",
            "## Estatisticas de Combate",
            f"- Ataque base: {combat.get('attack_value')}",
            f"- Dano medio: {combat.get('average_damage')}",
            f"- Defesa: {combat.get('defense')}",
            f"- PV: {combat.get('hit_points')}",
            f"- PM: {combat.get('mana_points', 0)}",
            "",
            "## Atributos",
            *(f"- {key.capitalize()}: {value}" for key, value in attrs.items()),
            "",
            "## Pericias",
            *(f"- {item.get('name')}: {item.get('total')}" for item in skills if isinstance(item, dict)),
            "",
            "## Ataques",
            *(f"- {item.get('name')}: +{item.get('attack_bonus')} / {item.get('damage')}" for item in attacks if isinstance(item, dict)),
            "",
            "## Habilidades",
            *(f"- {item.get('name')}: {item.get('summary') or item.get('description', '')}" for item in abilities if isinstance(item, dict)),
            "",
            "## Avisos",
            *([f"- {item}" for item in warnings] or ["- Nenhum"]),
        ]
    )


def generate_threat_sheet(params: JsonObject) -> ThreatGenerationResult:
    request = _build_request(params)
    normalized_challenge, nd_value = _parse_nd(request.challenge_level)
    combat_stats = _combat_stats(request.role, normalized_challenge, request.has_mana_points)
    attributes = _default_attributes(request.role)
    if isinstance(request.attributes, dict):
        for key, value in request.attributes.items():
            if key in attributes and isinstance(value, int):
                attributes[key] = max(-5, min(15, value))
    attacks = request.attacks_override or _default_attacks(request.name, combat_stats, request.role)
    abilities = request.abilities_override or _generated_abilities(request.role, normalized_challenge, combat_stats, request.has_mana_points)
    warnings: list[str] = []
    if request.attacks_override:
        warnings.append("attacks_override substituiu os ataques sugeridos.")
    if request.abilities_override:
        warnings.append("abilities_override substituiu as habilidades geradas.")
    if request.spells_override:
        warnings.append("spells_override aplicado manualmente.")
    special_qualities_list = _qualities(request.role, normalized_challenge, combat_stats)
    if request.special_qualities:
        special_qualities_list.append(request.special_qualities)
    threat = {
        "schema_version": 2,
        "system": "tormenta20-threat-generator",
        "builder": "jarvez-threat-generator",
        "name": request.name,
        "world": request.world,
        "type": request.threat_type,
        "size": request.size,
        "role": request.role,
        "challenge_level": normalized_challenge,
        "challenge_tier": _challenge_tier(nd_value),
        "concept": request.concept,
        "displacement": request.displacement,
        "combat_stats": combat_stats,
        "has_mana_points": request.has_mana_points,
        "attributes": attributes,
        "skills": _skills(normalized_challenge, attributes),
        "resistance_assignments": _default_resistances(request.role),
        "attacks": attacks,
        "abilities": abilities,
        "spells": request.spells_override,
        "special_qualities": "\n".join(f"- {item}" for item in special_qualities_list if str(item).strip()),
        "qualities": special_qualities_list,
        "generated_abilities": abilities,
        "equipment": request.equipment,
        "treasure_level": request.treasure_level,
        "ability_recommendation": _recommended_ability_count(normalized_challenge, request.role),
        "boss_features": _boss_features(normalized_challenge, combat_stats, request.has_mana_points) if request.is_boss else {},
        "source_reference": "Inspired by Fichas de Nimb threat generator tables",
        "generation_warnings": warnings,
        "updated_at": now_iso(),
    }
    markdown = _build_markdown(threat)
    return ThreatGenerationResult(
        source="jarvez-threat-generator",
        status="success",
        normalized_threat=threat,
        warnings=warnings,
        errors=[],
        markdown=markdown,
    )
