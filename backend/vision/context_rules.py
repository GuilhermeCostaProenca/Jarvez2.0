from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .context_events import VisualEvent

logger = logging.getLogger(__name__)

# CTX6: Only R1 (low-risk) actions are triggered automatically from visual context.
# R2+ actions always require explicit user confirmation.

VISUAL_CONTEXT_RULES: list[dict[str, Any]] = [
    {
        "rule_id": "light_on_got_up",
        "trigger_event": "got_up",
        "min_confidence": 0.6,
        "cooldown_seconds": 300,
        "action": "turn_light_on",
        "action_params": {"area": "bedroom"},
        "risk": "R1",
        "description": "Levantou da cama → ligar luz",
    },
    {
        "rule_id": "light_off_lay_down",
        "trigger_event": "lay_down",
        "min_confidence": 0.6,
        "cooldown_seconds": 300,
        "action": "turn_light_off",
        "action_params": {"area": "bedroom"},
        "risk": "R1",
        "description": "Deitou → desligar luz",
    },
    {
        "rule_id": "all_off_long_absence",
        "trigger_event": "left_room",
        "min_confidence": 0.7,
        "cooldown_seconds": 600,
        "action": "turn_light_off",
        "action_params": {"area": "all"},
        "risk": "R1",
        "description": "Saiu faz muito tempo → desligar tudo",
    },
    {
        "rule_id": "ac_arrival",
        "trigger_event": "presence_detected",
        "min_confidence": 0.8,
        "cooldown_seconds": 2700,
        "action": "ac_prepare_arrival",
        "action_params": {"trigger_source": "camera_presence"},
        "risk": "R1",
        "description": "Detectou chegada → preparar AC",
    },
]

# CTX4 — Contextual modes (stub, not triggered automatically by camera).
# Activation requires explicit voice command or user action.
CONTEXT_MODES: dict[str, Any] = {
    "rpg_mode": {
        "description": "Modo RPG: ambiente imersivo",
        "actions_sequence": [
            {"action": "set_light_scene", "params": {"scene": "dim"}},
            # expandível pelo usuário
        ],
        "trigger_phrase": "modo rpg",  # hint for voice integration
    }
}


@dataclass(slots=True)
class ContextRuleMatch:
    rule_id: str
    action: str
    action_params: dict[str, Any]
    should_execute: bool
    reason: str


class ContextRulesEngine:
    """
    CTX2+CTX3 — Evaluates visual events against VISUAL_CONTEXT_RULES.
    Only R1 rules are executed automatically; R2+ require explicit confirmation.
    Cooldown is tracked in memory per rule_id.
    """

    def __init__(self, rules: list[dict[str, Any]] | None = None) -> None:
        self._rules = rules if rules is not None else VISUAL_CONTEXT_RULES
        # In-memory cooldown tracking: rule_id → last triggered datetime
        self._last_triggered: dict[str, datetime] = {}

    def evaluate(
        self,
        event: VisualEvent,
        last_triggers: dict[str, Any] | None = None,
    ) -> list[ContextRuleMatch]:
        """
        Evaluate a VisualEvent against all rules.
        Returns list of ContextRuleMatch for every matching rule.
        """
        matches: list[ContextRuleMatch] = []
        now = datetime.now(timezone.utc)

        for rule in self._rules:
            if rule.get("trigger_event") != event.event_type:
                continue

            rule_id: str = rule["rule_id"]
            min_conf: float = float(rule.get("min_confidence", 0.0))
            cooldown: float = float(rule.get("cooldown_seconds", 0))
            risk: str = str(rule.get("risk", "R1"))
            action: str = rule["action"]
            action_params: dict[str, Any] = dict(rule.get("action_params") or {})

            # Confidence check
            if event.confidence < min_conf:
                matches.append(
                    ContextRuleMatch(
                        rule_id=rule_id,
                        action=action,
                        action_params=action_params,
                        should_execute=False,
                        reason=f"confidence {event.confidence:.2f} < min {min_conf:.2f}",
                    )
                )
                continue

            # Cooldown check (in-memory)
            last_dt = self._last_triggered.get(rule_id)
            if last_dt is not None:
                elapsed = (now - last_dt).total_seconds()
                if elapsed < cooldown:
                    matches.append(
                        ContextRuleMatch(
                            rule_id=rule_id,
                            action=action,
                            action_params=action_params,
                            should_execute=False,
                            reason=f"cooldown active ({elapsed:.0f}s elapsed, need {cooldown:.0f}s)",
                        )
                    )
                    continue

            # Risk check: only R1 executes automatically
            if risk != "R1":
                matches.append(
                    ContextRuleMatch(
                        rule_id=rule_id,
                        action=action,
                        action_params=action_params,
                        should_execute=False,
                        reason=f"risk {risk} requires explicit confirmation",
                    )
                )
                continue

            # All checks passed → execute
            self._last_triggered[rule_id] = now
            logger.info(
                "ContextRulesEngine: rule %s matched → %s (confidence=%.2f)",
                rule_id,
                action,
                event.confidence,
            )
            matches.append(
                ContextRuleMatch(
                    rule_id=rule_id,
                    action=action,
                    action_params=action_params,
                    should_execute=True,
                    reason=f"rule matched: {rule.get('description', '')}",
                )
            )

        return matches

    def suggest_new_rules(self, recent_events: list[dict[str, Any]]) -> list[str]:
        """
        CTX5 — Analyze recent event patterns and suggest new rules in plain language.
        Does NOT create rules autonomously — only returns human-readable suggestions.
        """
        suggestions: list[str] = []

        # Count events by type and hour
        hour_counts: dict[str, dict[int, int]] = {}
        for ev in recent_events:
            etype = ev.get("event_type", "")
            hour = ev.get("hour_of_day")
            if hour is None:
                continue
            if etype not in hour_counts:
                hour_counts[etype] = {}
            hour_counts[etype][hour] = hour_counts[etype].get(hour, 0) + 1

        # Generate suggestions for repeated patterns
        for etype, hours in hour_counts.items():
            if not hours:
                continue
            best_hour = max(hours, key=lambda h: hours[h])
            best_count = hours[best_hour]

            if best_count < 3:
                continue  # Not enough data to suggest

            if etype == "got_up":
                suggestions.append(
                    f"Você acorda sempre entre {best_hour}h e {best_hour+1}h. "
                    f"Posso ligar a luz automaticamente quando você se levantar nesse horário?"
                )
            elif etype == "lay_down":
                suggestions.append(
                    f"Você costuma se deitar por volta das {best_hour}h. "
                    f"Posso desligar as luzes automaticamente quando você deitar nesse horário?"
                )
            elif etype == "left_room":
                suggestions.append(
                    f"Você sai do quarto frequentemente por volta das {best_hour}h. "
                    f"Posso desligar tudo automaticamente quando você sair nesse horário?"
                )
            elif etype == "presence_detected":
                suggestions.append(
                    f"Você costuma chegar por volta das {best_hour}h. "
                    f"Posso preparar o ambiente (AC, luzes) quando você aparecer na câmera nesse horário?"
                )

        return suggestions
