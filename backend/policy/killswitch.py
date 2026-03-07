from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

KillSwitchDomain = str

_GLOBAL_KILL_SWITCH = False
_GLOBAL_REASON: str | None = None
_DOMAIN_SWITCHES: dict[KillSwitchDomain, str] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class KillSwitchState:
    global_enabled: bool
    global_reason: str | None
    domains: dict[str, str]
    updated_at: str

    def to_payload(self) -> dict[str, object]:
        return {
            "global_enabled": self.global_enabled,
            "global_reason": self.global_reason,
            "domains": dict(self.domains),
            "updated_at": self.updated_at,
        }


def set_global(enabled: bool, reason: str | None = None) -> KillSwitchState:
    global _GLOBAL_KILL_SWITCH, _GLOBAL_REASON
    _GLOBAL_KILL_SWITCH = enabled
    _GLOBAL_REASON = reason.strip() if isinstance(reason, str) and reason.strip() else None
    return get_status()


def set_domain(domain: str, enabled: bool, reason: str | None = None) -> KillSwitchState:
    normalized = domain.strip().lower()
    if not normalized:
        return get_status()
    if enabled:
        _DOMAIN_SWITCHES[normalized] = reason.strip() if isinstance(reason, str) and reason.strip() else "domain blocked"
    else:
        _DOMAIN_SWITCHES.pop(normalized, None)
    return get_status()


def is_blocked(*, domain: str | None = None) -> tuple[bool, str | None]:
    if _GLOBAL_KILL_SWITCH:
        return True, _GLOBAL_REASON or "Kill switch global ativo."
    normalized = (domain or "").strip().lower()
    if normalized and normalized in _DOMAIN_SWITCHES:
        return True, _DOMAIN_SWITCHES[normalized]
    return False, None


def get_status() -> KillSwitchState:
    return KillSwitchState(
        global_enabled=_GLOBAL_KILL_SWITCH,
        global_reason=_GLOBAL_REASON,
        domains=dict(_DOMAIN_SWITCHES),
        updated_at=_now_iso(),
    )
