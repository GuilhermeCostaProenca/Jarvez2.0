from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

JsonObject = dict[str, Any]

CharacterGenerationStatus = Literal["success", "partial", "unsupported"]
ThreatGenerationStatus = Literal["success", "partial", "unsupported"]


class UnsupportedBuildOptionError(ValueError):
    pass


class MissingBuildChoiceError(ValueError):
    pass


class InvalidCharacterBuildError(ValueError):
    pass


class InvalidThreatDefinitionError(ValueError):
    pass


@dataclass(slots=True)
class CharacterGenerationRequest:
    name: str
    world: str
    race: str
    class_name: str
    origin: str | None
    level: int
    concept: str | None
    attributes: JsonObject
    build_choices: JsonObject = field(default_factory=dict)
    generation_mode: Literal["auto", "strict"] = "auto"
    prefer_engine: Literal["t20", "fallback", "auto"] = "auto"


@dataclass(slots=True)
class CharacterGenerationResult:
    source: Literal["t20-sheet-builder", "fallback"]
    status: CharacterGenerationStatus
    normalized_sheet: JsonObject
    serialized_character: JsonObject | None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    applied_choices: JsonObject = field(default_factory=dict)
    unsupported_fields: list[str] = field(default_factory=list)
    markdown: str = ""


@dataclass(slots=True)
class ThreatGenerationRequest:
    name: str
    world: str
    threat_type: str
    size: str
    role: str
    challenge_level: str
    concept: str | None
    has_mana_points: bool
    is_boss: bool
    displacement: str
    attributes: JsonObject | None = None
    attacks_override: list[JsonObject] = field(default_factory=list)
    abilities_override: list[JsonObject] = field(default_factory=list)
    spells_override: list[JsonObject] = field(default_factory=list)
    special_qualities: str = ""
    equipment: str = ""
    treasure_level: str = "Padrao"
    generation_mode: Literal["suggested", "structured"] = "suggested"


@dataclass(slots=True)
class ThreatGenerationResult:
    source: Literal["jarvez-threat-generator"]
    status: ThreatGenerationStatus
    normalized_threat: JsonObject
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    markdown: str = ""
