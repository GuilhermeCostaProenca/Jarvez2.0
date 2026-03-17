from __future__ import annotations

from .types import ActionSpec

ACTION_REGISTRY: dict[str, ActionSpec] = {}


def register_action(spec: ActionSpec) -> None:
    if spec.name in ACTION_REGISTRY:
        raise ValueError(f"duplicate action name: {spec.name}")
    ACTION_REGISTRY[spec.name] = spec


def get_action(name: str) -> ActionSpec | None:
    return ACTION_REGISTRY.get(name)


def get_exposed_actions() -> list[ActionSpec]:
    return [spec for spec in ACTION_REGISTRY.values() if spec.expose_to_model]
