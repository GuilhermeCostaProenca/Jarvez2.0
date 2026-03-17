from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
import os
import re
import secrets
from typing import Any
import webbrowser

from actions_core import ActionContext, ActionResult

JsonObject = dict[str, Any]


def _default_briefing_cooldown_seconds() -> int:
    raw = str(os.getenv("JARVEZ_AUTOMATION_BRIEFING_COOLDOWN_SECONDS", "3600")).strip()
    try:
        value = int(raw)
    except ValueError:
        value = 3600
    return max(60, min(value, 86_400))


# DEPRECATED: migrated to jarvez-mcp-research
async def web_search_dashboard(
    params: JsonObject,
    ctx: ActionContext,
    *,
    collapse_spaces: Callable[[str], str],
    run_web_search: Callable[[str], tuple[list[JsonObject], ActionResult | None]]
    | Callable[[str, int], tuple[list[JsonObject], ActionResult | None]],
    build_summary: Callable[[str, list[JsonObject]], str],
    frontend_dashboard_url: Callable[[], str],
) -> ActionResult:
    _ = ctx
    query = collapse_spaces(str(params.get("query", "")))
    max_results = int(params.get("max_results", 5))
    if not query:
        return ActionResult(success=False, message="Informe o que devo pesquisar na web.", error="missing query")

    max_results = max(3, min(max_results, 8))
    results, search_error = run_web_search(query, max_results=max_results)  # type: ignore[misc]
    if search_error is not None:
        return search_error

    image_urls = [
        str(item["image_url"])
        for item in results
        if isinstance(item.get("image_url"), str) and str(item.get("image_url")).strip()
    ][:4]
    summary = build_summary(query, results)
    generated_at = datetime.now(timezone.utc).isoformat()
    dashboard_url = frontend_dashboard_url()
    dashboard_opened = False

    try:
        dashboard_opened = bool(webbrowser.open(dashboard_url, new=2))
    except OSError:
        dashboard_opened = False

    return ActionResult(
        success=True,
        message=f"Pesquisa web compilada para '{query}'.",
        data={
            "web_dashboard": {
                "query": query,
                "summary": summary,
                "generated_at": generated_at,
                "results": results,
                "images": image_urls,
                "dashboard_url": dashboard_url,
                "dashboard_opened": dashboard_opened,
            }
        },
    )


async def save_web_briefing_schedule(
    params: JsonObject,
    ctx: ActionContext,
    *,
    collapse_spaces: Callable[[str], str],
) -> ActionResult:
    _ = ctx
    query = collapse_spaces(str(params.get("query", "")))
    time_of_day = collapse_spaces(str(params.get("time_of_day", "08:00"))) or "08:00"
    timezone_name = collapse_spaces(str(params.get("timezone", os.getenv("JARVEZ_AUTOMATION_TIMEZONE", "UTC")))) or "UTC"
    enabled = bool(params.get("enabled", True))
    schedule_dry_run = bool(params.get("dry_run", False))
    max_results = int(params.get("max_results", 5))
    cooldown_seconds_raw = params.get(
        "cooldown_seconds",
        int(params.get("cooldown_minutes", 0) or 0) * 60,
    )
    try:
        cooldown_seconds = int(cooldown_seconds_raw)
    except (TypeError, ValueError):
        cooldown_seconds = _default_briefing_cooldown_seconds()
    cooldown_seconds = max(60, min(cooldown_seconds or _default_briefing_cooldown_seconds(), 86_400))

    if not query:
        return ActionResult(success=False, message="Informe o tema da pesquisa recorrente.", error="missing query")
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", time_of_day):
        return ActionResult(success=False, message="Horario invalido. Use HH:MM.", error="invalid time_of_day")

    schedule_id = f"research-{secrets.token_hex(6)}"
    schedule = {
        "id": schedule_id,
        "query": query,
        "cadence": "daily",
        "time_of_day": time_of_day,
        "timezone": timezone_name,
        "enabled": enabled,
        "dry_run": schedule_dry_run,
        "max_results": max(3, min(max_results, 8)),
        "cooldown_seconds": cooldown_seconds,
        "prompt": (
            "Faca uma pesquisa na internet e gere um dashboard completo com resumo, links e imagens sobre: "
            f"{query}"
        ),
    }

    return ActionResult(
        success=True,
        message=f"Briefing diario salvo para {time_of_day}.",
        data={"web_dashboard_schedule": schedule},
    )
