from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _default_metrics_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "evals_metrics.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_metrics(path: Path | None = None) -> dict[str, Any]:
    target = path or _default_metrics_path()
    if not target.exists():
        return {"updated_at": None, "items": []}
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return {"updated_at": None, "items": []}


def append_metric(item: dict[str, Any], path: Path | None = None) -> dict[str, Any]:
    target = path or _default_metrics_path()
    current = read_metrics(target)
    payload = {
        "updated_at": _now_iso(),
        "items": [item, *list(current.get("items", []))][:500],
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def summarize_action_metrics(items: list[dict[str, Any]]) -> dict[str, Any]:
    provider_totals: dict[str, dict[str, int]] = {}
    risk_totals: dict[str, dict[str, int]] = {}
    trust_drift_totals: dict[str, Any] = {
        "active_total": 0,
        "inactive_total": 0,
        "by_domain": {},
    }
    autonomy_notice_totals: dict[str, Any] = {
        "active_total": 0,
        "inactive_total": 0,
        "by_level": {},
        "by_channel": {},
        "by_domain": {},
        "unconfirmed_total": 0,
        "unconfirmed_by_domain": {},
    }
    autonomy_notice_trace_ids: set[str] = set()
    autonomy_notice_confirmed_trace_ids: set[str] = set()
    autonomy_notice_trace_domains: dict[str, str] = {}
    total = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        if item_type == "autonomy_notice_delivery":
            payload = item.get("payload")
            if not isinstance(payload, dict):
                continue
            channel = str(payload.get("channel") or "unknown")
            trace_id = str(payload.get("trace_id") or "").strip()
            domain = str(payload.get("domain") or "").strip().lower() or "general"
            by_channel = autonomy_notice_totals["by_channel"]
            channel_entry = by_channel.setdefault(channel, {"total": 0})
            channel_entry["total"] += 1
            if trace_id:
                autonomy_notice_confirmed_trace_ids.add(trace_id)
                autonomy_notice_trace_domains.setdefault(trace_id, domain)
            continue
        if item_type != "action_result":
            continue
        payload = item.get("payload")
        if not isinstance(payload, dict):
            continue
        total += 1
        success = bool(payload.get("success"))
        provider = str(payload.get("evidence_provider") or "unknown")
        risk = str(payload.get("risk") or "unknown")
        trust_drift_active = bool(payload.get("trust_drift_active"))
        trust_drift_domain = str(payload.get("trust_drift_domain") or "none")
        autonomy_notice_active = bool(payload.get("autonomy_notice_active"))
        autonomy_notice_level = str(payload.get("autonomy_notice_level") or "none")
        autonomy_notice_channel = str(payload.get("autonomy_notice_channel") or "none")
        autonomy_notice_domain = str(payload.get("autonomy_notice_domain") or "general")
        trace_id = str(payload.get("trace_id") or "").strip()

        provider_entry = provider_totals.setdefault(provider, {"total": 0, "success": 0, "failed": 0})
        provider_entry["total"] += 1
        if success:
            provider_entry["success"] += 1
        else:
            provider_entry["failed"] += 1

        risk_entry = risk_totals.setdefault(risk, {"total": 0, "success": 0, "failed": 0})
        risk_entry["total"] += 1
        if success:
            risk_entry["success"] += 1
        else:
            risk_entry["failed"] += 1

        if trust_drift_active:
            trust_drift_totals["active_total"] += 1
            by_domain = trust_drift_totals["by_domain"]
            domain_entry = by_domain.setdefault(trust_drift_domain, {"total": 0, "success": 0, "failed": 0})
            domain_entry["total"] += 1
            if success:
                domain_entry["success"] += 1
            else:
                domain_entry["failed"] += 1
        else:
            trust_drift_totals["inactive_total"] += 1

        if autonomy_notice_active:
            autonomy_notice_totals["active_total"] += 1
            if trace_id:
                autonomy_notice_trace_ids.add(trace_id)
                autonomy_notice_trace_domains.setdefault(trace_id, autonomy_notice_domain)

            by_level = autonomy_notice_totals["by_level"]
            level_entry = by_level.setdefault(autonomy_notice_level, {"total": 0, "success": 0, "failed": 0})
            level_entry["total"] += 1
            if success:
                level_entry["success"] += 1
            else:
                level_entry["failed"] += 1

            by_domain = autonomy_notice_totals["by_domain"]
            domain_entry = by_domain.setdefault(autonomy_notice_domain, {"total": 0, "success": 0, "failed": 0})
            domain_entry["total"] += 1
            if success:
                domain_entry["success"] += 1
            else:
                domain_entry["failed"] += 1

            if autonomy_notice_channel == "agent_audio":
                by_channel = autonomy_notice_totals["by_channel"]
                channel_entry = by_channel.setdefault("agent_audio", {"total": 0})
                channel_entry["total"] += 1
                if trace_id:
                    autonomy_notice_confirmed_trace_ids.add(trace_id)
        else:
            autonomy_notice_totals["inactive_total"] += 1

    autonomy_notice_totals["unconfirmed_total"] = len(
        autonomy_notice_trace_ids - autonomy_notice_confirmed_trace_ids
    )
    for trace_id in autonomy_notice_trace_ids - autonomy_notice_confirmed_trace_ids:
        domain = autonomy_notice_trace_domains.get(trace_id, "general")
        by_domain = autonomy_notice_totals["unconfirmed_by_domain"]
        by_domain[domain] = int(by_domain.get(domain, 0)) + 1

    return {
        "total_actions": total,
        "providers": provider_totals,
        "risk_tiers": risk_totals,
        "trust_drift": trust_drift_totals,
        "autonomy_notice": autonomy_notice_totals,
    }


def _percentile(values: list[int], pct: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    rank = int(round((pct / 100.0) * (len(ordered) - 1)))
    rank = max(0, min(rank, len(ordered) - 1))
    return int(ordered[rank])


def summarize_slo(items: list[dict[str, Any]]) -> dict[str, Any]:
    action_rows: list[dict[str, Any]] = []
    fallback_durations: list[int] = []
    low_risk_total = 0
    low_risk_success = 0
    false_success_flags = 0
    trust_drift_active_total = 0
    autonomy_notice_total = 0
    autonomy_notice_agent_audio_total = 0
    autonomy_notice_browser_tts_total = 0
    autonomy_notice_trace_ids: set[str] = set()
    autonomy_notice_agent_audio_traces: set[str] = set()
    autonomy_notice_browser_tts_traces: set[str] = set()

    by_provider: dict[str, dict[str, int]] = {}
    by_action: dict[str, dict[str, int]] = {}

    for item in items:
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        if item_type == "autonomy_notice_delivery":
            payload = item.get("payload")
            if not isinstance(payload, dict):
                continue
            trace_id = str(payload.get("trace_id") or "").strip()
            channel = str(payload.get("channel") or "unknown")
            if channel == "browser_tts":
                autonomy_notice_browser_tts_total += 1
                if trace_id:
                    autonomy_notice_browser_tts_traces.add(trace_id)
            continue
        if item_type != "action_result":
            continue
        payload = item.get("payload")
        if not isinstance(payload, dict):
            continue
        action_rows.append(payload)
        action_name = str(payload.get("action_name") or "unknown")
        provider = str(payload.get("evidence_provider") or "unknown")
        risk = str(payload.get("risk") or "unknown")
        duration_ms = int(payload.get("duration_ms") or 0)
        success = bool(payload.get("success"))
        fallback_used = bool(payload.get("fallback_used"))
        trust_drift_active = bool(payload.get("trust_drift_active"))
        autonomy_notice_active = bool(payload.get("autonomy_notice_active"))
        autonomy_notice_channel = str(payload.get("autonomy_notice_channel") or "none")
        trace_id = str(payload.get("trace_id") or "").strip()

        provider_entry = by_provider.setdefault(provider, {"total": 0, "success": 0, "failed": 0, "p95_ms": 0})
        provider_entry["total"] += 1
        if success:
            provider_entry["success"] += 1
        else:
            provider_entry["failed"] += 1

        action_entry = by_action.setdefault(action_name, {"total": 0, "success": 0, "failed": 0, "p95_ms": 0})
        action_entry["total"] += 1
        if success:
            action_entry["success"] += 1
        else:
            action_entry["failed"] += 1

        if risk in {"R0", "R1"}:
            low_risk_total += 1
            if success:
                low_risk_success += 1

        # proxy de false-success: sucesso sem provider de evidencia ou provider interno em acao sensivel
        if success and (provider == "unknown" or (risk in {"R2", "R3"} and provider == "internal")):
            false_success_flags += 1

        if fallback_used:
            fallback_durations.append(duration_ms)
        if trust_drift_active:
            trust_drift_active_total += 1
        if autonomy_notice_active:
            autonomy_notice_total += 1
            if trace_id:
                autonomy_notice_trace_ids.add(trace_id)
            if autonomy_notice_channel == "agent_audio":
                autonomy_notice_agent_audio_total += 1
                if trace_id:
                    autonomy_notice_agent_audio_traces.add(trace_id)

    provider_durations: dict[str, list[int]] = {}
    action_durations: dict[str, list[int]] = {}
    for payload in action_rows:
        provider = str(payload.get("evidence_provider") or "unknown")
        action_name = str(payload.get("action_name") or "unknown")
        duration_ms = int(payload.get("duration_ms") or 0)
        provider_durations.setdefault(provider, []).append(duration_ms)
        action_durations.setdefault(action_name, []).append(duration_ms)

    for provider, entry in by_provider.items():
        entry["p95_ms"] = _percentile(provider_durations.get(provider, []), 95)
    for action_name, entry in by_action.items():
        entry["p95_ms"] = _percentile(action_durations.get(action_name, []), 95)

    total_actions = len(action_rows)
    overall_p95 = _percentile([int(row.get("duration_ms") or 0) for row in action_rows], 95)
    fallback_p95 = _percentile(fallback_durations, 95)
    low_risk_success_rate = (float(low_risk_success) / float(low_risk_total)) if low_risk_total else 0.0
    false_success_rate = (float(false_success_flags) / float(total_actions)) if total_actions else 0.0
    trust_drift_active_rate = (float(trust_drift_active_total) / float(total_actions)) if total_actions else 0.0
    autonomy_notice_agent_audio_rate = (
        float(len(autonomy_notice_agent_audio_traces) or autonomy_notice_agent_audio_total)
        / float(autonomy_notice_total)
        ) if autonomy_notice_total else 0.0
    autonomy_notice_browser_tts_rate = (
        float(len(autonomy_notice_browser_tts_traces) or autonomy_notice_browser_tts_total)
        / float(autonomy_notice_total)
    ) if autonomy_notice_total else 0.0
    autonomy_notice_unconfirmed_rate = (
        float(
            len(
                autonomy_notice_trace_ids
                - autonomy_notice_agent_audio_traces
                - autonomy_notice_browser_tts_traces
            )
        )
        / float(autonomy_notice_total)
    ) if autonomy_notice_total else 0.0

    return {
        "total_actions": total_actions,
        "latency": {
            "overall_p95_ms": overall_p95,
            "fallback_p95_ms": fallback_p95,
        },
        "reliability": {
            "low_risk_success_rate": round(low_risk_success_rate, 4),
            "false_success_proxy_rate": round(false_success_rate, 4),
            "trust_drift_active_rate": round(trust_drift_active_rate, 4),
            "autonomy_notice_agent_audio_rate": round(autonomy_notice_agent_audio_rate, 4),
            "autonomy_notice_browser_tts_rate": round(autonomy_notice_browser_tts_rate, 4),
            "autonomy_notice_unconfirmed_rate": round(autonomy_notice_unconfirmed_rate, 4),
        },
        "targets": {
            "false_success_rate_max": 0.0,
            "low_risk_success_rate_min": 0.95,
            "fallback_p95_ms_max": 3000,
        },
        "slo_pass": {
            "false_success": false_success_rate <= 0.0,
            "low_risk_success": low_risk_success_rate >= 0.95,
            "fallback_p95": fallback_p95 <= 3000 if fallback_durations else True,
        },
        "by_provider": by_provider,
        "by_action": by_action,
    }
