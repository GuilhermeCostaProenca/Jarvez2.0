from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
import os
from typing import Any

from actions_core import ActionContext, ActionResult

JsonObject = dict[str, Any]


def _thinq_build_air_command(*, section: str, payload: JsonObject) -> JsonObject:
    return {section: payload}


def _normalize_ac_mode(value: str, *, normalize_label: Callable[[str], str]) -> str:
    normalized = normalize_label(value)
    mapping = {
        "auto": "AUTO",
        "automatico": "AUTO",
        "automatic": "AUTO",
        "secar": "AIR_DRY",
        "dry": "AIR_DRY",
        "desumidificar": "AIR_DRY",
        "aquecer": "HEAT",
        "heat": "HEAT",
        "ventilar": "FAN",
        "fan": "FAN",
        "frio": "COOL",
        "cool": "COOL",
        "refrigerar": "COOL",
    }
    return mapping.get(normalized.replace(" ", ""), mapping.get(normalized, value.strip().upper()))


def _normalize_ac_fan_speed(value: str, *, normalize_label: Callable[[str], str]) -> str:
    normalized = normalize_label(value)
    mapping = {
        "auto": "AUTO",
        "automatico": "AUTO",
        "baixo": "LOW",
        "low": "LOW",
        "medio": "MID",
        "medio alto": "MID_HIGH",
        "mid": "MID",
        "mid high": "MID_HIGH",
        "alto": "HIGH",
        "high": "HIGH",
        "natural": "NATURE",
        "nature": "NATURE",
        "baixo medio": "LOW_MID",
        "low mid": "LOW_MID",
    }
    compact = normalized.replace(" ", "")
    return mapping.get(compact, mapping.get(normalized, value.strip().upper()))


def _thinq_profile_write_enum_values(profile: JsonObject, section: str, key: str) -> set[str]:
    properties = profile.get("property")
    if not isinstance(properties, dict):
        return set()
    section_payload = properties.get(section)
    if not isinstance(section_payload, dict):
        return set()
    entry = section_payload.get(key)
    if not isinstance(entry, dict):
        return set()
    value = entry.get("value")
    if not isinstance(value, dict):
        return set()
    writable = value.get("w")
    if not isinstance(writable, list):
        return set()
    return {str(item).strip() for item in writable if str(item).strip()}


def _ac_current_temperature_from_status(status_data: JsonObject) -> float | None:
    state = status_data.get("state")
    if not isinstance(state, dict):
        return None
    temperature = state.get("temperature")
    if not isinstance(temperature, dict):
        return None
    current = temperature.get("currentTemperature")
    if isinstance(current, (int, float)):
        return float(current)
    return None


def _resolve_ac_arrival_prefs(
    params: JsonObject,
    *,
    load_ac_arrival_prefs: Callable[[], JsonObject],
    thinq_default_ac_name: Callable[[], str],
    coerce_optional_str: Callable[[Any], str | None],
) -> JsonObject:
    stored = load_ac_arrival_prefs()
    env_presence_entity = str(os.getenv("JARVEZ_PRESENCE_ENTITY_ID", "")).strip()
    env_arrival_cooldown = str(os.getenv("JARVEZ_AUTOMATION_ARRIVAL_COOLDOWN_SECONDS", "2700")).strip()
    try:
        default_arrival_cooldown = int(env_arrival_cooldown)
    except ValueError:
        default_arrival_cooldown = 2700
    default_arrival_cooldown = max(30, min(default_arrival_cooldown, 86_400))
    defaults: JsonObject = {
        "desired_temperature": 23.0,
        "hot_threshold": 28.0,
        "vent_only_threshold": 25.0,
        "eta_minutes": 20,
        "enable_swing": True,
        "device_name": thinq_default_ac_name(),
        "presence_entity_id": env_presence_entity or None,
        "automation_enabled": bool(env_presence_entity),
        "cooldown_seconds": default_arrival_cooldown,
        "run_live_after_dry_run": True,
    }
    resolved = {**defaults, **(stored if isinstance(stored, dict) else {})}
    for key in ("desired_temperature", "hot_threshold", "vent_only_threshold"):
        value = params.get(key)
        if isinstance(value, (int, float)):
            resolved[key] = float(value)
    eta = params.get("eta_minutes")
    if isinstance(eta, int) and eta >= 0:
        resolved["eta_minutes"] = eta
    if isinstance(params.get("enable_swing"), bool):
        resolved["enable_swing"] = params["enable_swing"]
    if isinstance(params.get("automation_enabled"), bool):
        resolved["automation_enabled"] = params["automation_enabled"]
    if isinstance(params.get("run_live_after_dry_run"), bool):
        resolved["run_live_after_dry_run"] = params["run_live_after_dry_run"]
    cooldown_seconds_raw = params.get(
        "cooldown_seconds",
        int(params.get("cooldown_minutes", 0) or 0) * 60,
    )
    try:
        cooldown_seconds = int(cooldown_seconds_raw)
    except (TypeError, ValueError):
        cooldown_seconds = int(resolved.get("cooldown_seconds") or default_arrival_cooldown)
    resolved["cooldown_seconds"] = max(30, min(cooldown_seconds or default_arrival_cooldown, 86_400))
    device_name = coerce_optional_str(params.get("device_name"))
    if device_name:
        resolved["device_name"] = device_name
    presence_entity_id = coerce_optional_str(params.get("presence_entity_id"))
    if presence_entity_id is not None:
        resolved["presence_entity_id"] = presence_entity_id
    if "automation_enabled" not in params and not str(resolved.get("presence_entity_id") or "").strip():
        resolved["automation_enabled"] = False
    return resolved


async def ac_get_status(
    params: JsonObject,
    ctx: ActionContext,
    *,
    coerce_optional_str: Callable[[Any], str | None],
    thinq_find_device: Callable[..., tuple[JsonObject | None, ActionResult | None]],
    thinq_api_request: Callable[..., tuple[JsonObject | list[Any] | None, ActionResult | None]],
    thinq_extract_device_id: Callable[[JsonObject], str],
    thinq_extract_device_alias: Callable[[JsonObject], str],
    thinq_simplify_device: Callable[[JsonObject], JsonObject],
    quote_path_segment: Callable[[str], str],
) -> ActionResult:
    _ = ctx
    device, error = thinq_find_device(
        device_name=coerce_optional_str(params.get("device_name")),
        device_id=coerce_optional_str(params.get("device_id")),
        require_air=True,
    )
    if error is not None:
        return error
    assert device is not None
    payload, request_error = thinq_api_request("GET", f"devices/{quote_path_segment(thinq_extract_device_id(device))}/state")
    if request_error is not None:
        return request_error
    return ActionResult(
        success=True,
        message=f"Estado do ar carregado para {thinq_extract_device_alias(device)}.",
        data={
            "device": thinq_simplify_device(device),
            "state": payload if isinstance(payload, dict) else {"raw": payload},
        },
    )


async def ac_send_command(
    params: JsonObject,
    ctx: ActionContext,
    *,
    coerce_optional_str: Callable[[Any], str | None],
    thinq_find_device: Callable[..., tuple[JsonObject | None, ActionResult | None]],
    thinq_api_request: Callable[..., tuple[JsonObject | list[Any] | None, ActionResult | None]],
    thinq_extract_device_id: Callable[[JsonObject], str],
    thinq_extract_device_alias: Callable[[JsonObject], str],
    thinq_simplify_device: Callable[[JsonObject], JsonObject],
    quote_path_segment: Callable[[str], str],
) -> ActionResult:
    _ = ctx
    device, error = thinq_find_device(
        device_name=coerce_optional_str(params.get("device_name")),
        device_id=coerce_optional_str(params.get("device_id")),
        require_air=True,
    )
    if error is not None:
        return error
    assert device is not None

    command = params.get("command")
    if not isinstance(command, dict) or not command:
        return ActionResult(
            success=False,
            message="Comando do ar invalido.",
            error="missing or invalid command object",
        )

    conditional = bool(params.get("conditional"))
    _, request_error = thinq_api_request(
        "POST",
        f"devices/{quote_path_segment(thinq_extract_device_id(device))}/control",
        body=command,
        extra_headers={"x-conditional-control": "true"} if conditional else None,
    )
    if request_error is not None:
        return request_error

    return ActionResult(
        success=True,
        message=f"Comando enviado para o ar {thinq_extract_device_alias(device)}.",
        data={
            "device": thinq_simplify_device(device),
            "conditional": conditional,
            "command": command,
        },
    )


async def ac_turn_on(
    params: JsonObject,
    ctx: ActionContext,
    *,
    ac_send_command: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
) -> ActionResult:
    return await ac_send_command(
        {
            "device_name": params.get("device_name"),
            "device_id": params.get("device_id"),
            "conditional": params.get("conditional"),
            "command": _thinq_build_air_command(section="operation", payload={"airConOperationMode": "POWER_ON"}),
        },
        ctx,
    )


async def ac_turn_off(
    params: JsonObject,
    ctx: ActionContext,
    *,
    ac_send_command: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
) -> ActionResult:
    return await ac_send_command(
        {
            "device_name": params.get("device_name"),
            "device_id": params.get("device_id"),
            "conditional": params.get("conditional"),
            "command": _thinq_build_air_command(section="operation", payload={"airConOperationMode": "POWER_OFF"}),
        },
        ctx,
    )


async def ac_set_mode(
    params: JsonObject,
    ctx: ActionContext,
    *,
    coerce_optional_str: Callable[[Any], str | None],
    normalize_label: Callable[[str], str],
    ac_send_command: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
) -> ActionResult:
    raw_mode = coerce_optional_str(params.get("mode"))
    if not raw_mode:
        return ActionResult(success=False, message="Informe o modo do ar.", error="missing mode")
    mode = _normalize_ac_mode(raw_mode, normalize_label=normalize_label)
    return await ac_send_command(
        {
            "device_name": params.get("device_name"),
            "device_id": params.get("device_id"),
            "conditional": params.get("conditional"),
            "command": _thinq_build_air_command(section="airConJobMode", payload={"currentJobMode": mode}),
        },
        ctx,
    )


async def ac_set_fan_speed(
    params: JsonObject,
    ctx: ActionContext,
    *,
    coerce_optional_str: Callable[[Any], str | None],
    normalize_label: Callable[[str], str],
    ac_send_command: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
) -> ActionResult:
    raw_speed = coerce_optional_str(params.get("fan_speed"))
    if not raw_speed:
        return ActionResult(success=False, message="Informe a velocidade do vento.", error="missing fan_speed")
    speed = _normalize_ac_fan_speed(raw_speed, normalize_label=normalize_label)
    detail = bool(params.get("detail"))
    key = "windStrengthDetail" if detail else "windStrength"
    return await ac_send_command(
        {
            "device_name": params.get("device_name"),
            "device_id": params.get("device_id"),
            "conditional": params.get("conditional"),
            "command": _thinq_build_air_command(section="airFlow", payload={key: speed}),
        },
        ctx,
    )


async def ac_set_temperature(
    params: JsonObject,
    ctx: ActionContext,
    *,
    coerce_optional_str: Callable[[Any], str | None],
    thinq_find_device: Callable[..., tuple[JsonObject | None, ActionResult | None]],
    thinq_api_request: Callable[..., tuple[JsonObject | list[Any] | None, ActionResult | None]],
    thinq_extract_device_id: Callable[[JsonObject], str],
    thinq_extract_device_alias: Callable[[JsonObject], str],
    quote_path_segment: Callable[[str], str],
    ac_send_command: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
) -> ActionResult:
    device, error = thinq_find_device(
        device_name=coerce_optional_str(params.get("device_name")),
        device_id=coerce_optional_str(params.get("device_id")),
        require_air=True,
    )
    if error is not None:
        return error
    assert device is not None

    temperature = params.get("temperature")
    if not isinstance(temperature, (int, float)):
        return ActionResult(success=False, message="Informe a temperatura alvo.", error="missing temperature")

    profile_payload, profile_error = thinq_api_request(
        "GET",
        f"devices/{quote_path_segment(thinq_extract_device_id(device))}/profile",
    )
    if profile_error is not None:
        return profile_error

    profile = profile_payload if isinstance(profile_payload, dict) else {}
    temperature_property = (
        ((profile.get("property") or {}).get("temperature") or {})
        if isinstance(profile.get("property"), dict)
        else {}
    )
    target_schema = temperature_property.get("targetTemperature") if isinstance(temperature_property, dict) else {}
    range_info = (target_schema.get("value") or {}).get("w", {}) if isinstance(target_schema, dict) else {}
    min_value = float(range_info.get("min", 18))
    max_value = float(range_info.get("max", 30))
    step = float(range_info.get("step", 0.5))

    desired = max(min_value, min(max_value, float(temperature)))
    if step > 0:
        desired = round(round((desired - min_value) / step) * step + min_value, 2)

    unit = coerce_optional_str(params.get("unit")) or "C"
    return await ac_send_command(
        {
            "device_name": thinq_extract_device_alias(device),
            "device_id": thinq_extract_device_id(device),
            "conditional": params.get("conditional"),
            "command": _thinq_build_air_command(
                section="temperature",
                payload={"targetTemperature": desired, "unit": unit.upper()},
            ),
        },
        ctx,
    )


async def ac_set_swing(
    params: JsonObject,
    ctx: ActionContext,
    *,
    ac_send_command: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
) -> ActionResult:
    enabled = params.get("enabled")
    if not isinstance(enabled, bool):
        return ActionResult(success=False, message="Informe se a oscilacao fica ligada ou desligada.", error="missing enabled")
    return await ac_send_command(
        {
            "device_name": params.get("device_name"),
            "device_id": params.get("device_id"),
            "conditional": params.get("conditional"),
            "command": _thinq_build_air_command(section="windDirection", payload={"rotateUpDown": enabled}),
        },
        ctx,
    )


async def ac_set_sleep_timer(
    params: JsonObject,
    ctx: ActionContext,
    *,
    thinq_default_ac_name: Callable[[], str],
    ac_get_device_profile: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
    ac_send_command: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
) -> ActionResult:
    hours = params.get("hours", 0)
    minutes = params.get("minutes", 0)
    target_name = params.get("device_name") or thinq_default_ac_name()
    target_id = params.get("device_id")
    try:
        total_minutes = max(0, int(hours) * 60 + int(minutes))
    except Exception:
        return ActionResult(success=False, message="Timer invalido.", error="invalid timer")

    profile_result = await ac_get_device_profile(
        {"device_name": target_name, "device_id": target_id},
        ctx,
    )
    profile = (profile_result.data or {}).get("profile") if profile_result.success and isinstance(profile_result.data, dict) else {}
    writable_values = _thinq_profile_write_enum_values(profile if isinstance(profile, dict) else {}, "sleepTimer", "relativeStopTimer")

    if total_minutes == 0:
        payload = {"relativeStopTimer": "UNSET"}
        message = "Timer de desligamento removido."
    else:
        if writable_values and "SET" not in writable_values:
            return ActionResult(
                success=False,
                message="Este modelo de ar nao suporta programar timer de desligamento pela API ThinQ.",
                error="sleep timer set unsupported",
            )
        payload = {
            "relativeStopTimer": "SET",
            "relativeHourToStop": total_minutes // 60,
            "relativeMinuteToStop": total_minutes % 60,
        }
        message = f"Timer de desligamento ajustado para {total_minutes // 60}h {total_minutes % 60}min."

    result = await ac_send_command(
        {
            "device_name": target_name,
            "device_id": target_id,
            "conditional": params.get("conditional"),
            "command": _thinq_build_air_command(section="sleepTimer", payload=payload),
        },
        ctx,
    )
    if result.success:
        result.message = message
    return result


async def ac_set_start_timer(
    params: JsonObject,
    ctx: ActionContext,
    *,
    thinq_default_ac_name: Callable[[], str],
    ac_get_device_profile: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
    ac_send_command: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
) -> ActionResult:
    hours = params.get("hours", 0)
    minutes = params.get("minutes", 0)
    target_name = params.get("device_name") or thinq_default_ac_name()
    target_id = params.get("device_id")
    try:
        total_minutes = max(0, int(hours) * 60 + int(minutes))
    except Exception:
        return ActionResult(success=False, message="Timer de ligar invalido.", error="invalid timer")

    profile_result = await ac_get_device_profile(
        {"device_name": target_name, "device_id": target_id},
        ctx,
    )
    profile = (profile_result.data or {}).get("profile") if profile_result.success and isinstance(profile_result.data, dict) else {}
    writable_values = _thinq_profile_write_enum_values(profile if isinstance(profile, dict) else {}, "timer", "relativeStartTimer")

    if total_minutes == 0:
        payload = {"relativeStartTimer": "UNSET"}
        message = "Timer de ligamento removido."
    else:
        if writable_values and "SET" not in writable_values:
            return ActionResult(
                success=False,
                message="Este modelo de ar nao suporta programar timer de ligamento pela API ThinQ.",
                error="start timer set unsupported",
            )
        payload = {
            "relativeStartTimer": "SET",
            "relativeHourToStart": total_minutes // 60,
            "relativeMinuteToStart": total_minutes % 60,
        }
        message = f"Timer de ligamento ajustado para {total_minutes // 60}h {total_minutes % 60}min."

    result = await ac_send_command(
        {
            "device_name": target_name,
            "device_id": target_id,
            "conditional": params.get("conditional"),
            "command": _thinq_build_air_command(section="timer", payload=payload),
        },
        ctx,
    )
    if result.success:
        result.message = message
    return result


async def ac_set_power_save(
    params: JsonObject,
    ctx: ActionContext,
    *,
    ac_send_command: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
) -> ActionResult:
    enabled = params.get("enabled")
    if not isinstance(enabled, bool):
        return ActionResult(success=False, message="Informe se o modo economia fica ligado ou desligado.", error="missing enabled")
    result = await ac_send_command(
        {
            "device_name": params.get("device_name"),
            "device_id": params.get("device_id"),
            "conditional": params.get("conditional"),
            "command": _thinq_build_air_command(section="powerSave", payload={"powerSaveEnabled": enabled}),
        },
        ctx,
    )
    if result.success:
        result.message = "Modo economia ligado." if enabled else "Modo economia desligado."
    return result


async def ac_apply_preset(
    params: JsonObject,
    ctx: ActionContext,
    *,
    coerce_optional_str: Callable[[Any], str | None],
    normalize_label: Callable[[str], str],
    ac_turn_on: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
    ac_set_mode: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
    ac_set_temperature: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
    ac_set_fan_speed: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
    ac_set_sleep_timer: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
    ac_set_swing: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
    ac_set_power_save: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
) -> ActionResult:
    preset_raw = coerce_optional_str(params.get("preset"))
    if not preset_raw:
        return ActionResult(success=False, message="Informe qual preset aplicar.", error="missing preset")

    preset = normalize_label(preset_raw)
    base_params = {
        "device_name": params.get("device_name"),
        "device_id": params.get("device_id"),
        "conditional": params.get("conditional"),
    }

    if preset in {"modo dormir", "dormir", "sleep"}:
        sequence = [
            ("modo", await ac_set_mode({**base_params, "mode": "COOL"}, ctx)),
            ("temperatura", await ac_set_temperature({**base_params, "temperature": 23}, ctx)),
            ("vento", await ac_set_fan_speed({**base_params, "fan_speed": "LOW"}, ctx)),
            ("timer", await ac_set_sleep_timer({**base_params, "hours": 8}, ctx)),
        ]
    elif preset in {"gelar sala", "turbo", "resfriar rapido", "resfriar rapido"}:
        sequence = [
            ("modo", await ac_set_mode({**base_params, "mode": "COOL"}, ctx)),
            ("temperatura", await ac_set_temperature({**base_params, "temperature": 18}, ctx)),
            ("vento", await ac_set_fan_speed({**base_params, "fan_speed": "HIGH"}, ctx)),
        ]
    elif preset in {"modo visita", "visita"}:
        sequence = [
            ("ligar", await ac_turn_on(base_params, ctx)),
            ("modo", await ac_set_mode({**base_params, "mode": "COOL"}, ctx)),
            ("temperatura", await ac_set_temperature({**base_params, "temperature": 22}, ctx)),
            ("vento", await ac_set_fan_speed({**base_params, "fan_speed": "MID"}, ctx)),
            ("oscilacao", await ac_set_swing({**base_params, "enabled": True}, ctx)),
        ]
    elif preset in {"economia", "eco", "modo economia"}:
        sequence = [
            ("ligar", await ac_turn_on(base_params, ctx)),
            ("modo", await ac_set_mode({**base_params, "mode": "AUTO"}, ctx)),
            ("temperatura", await ac_set_temperature({**base_params, "temperature": 24}, ctx)),
            ("vento", await ac_set_fan_speed({**base_params, "fan_speed": "AUTO"}, ctx)),
            ("economia", await ac_set_power_save({**base_params, "enabled": True}, ctx)),
        ]
    elif preset in {"ventilar leve", "ventilar", "brisa"}:
        sequence = [
            ("ligar", await ac_turn_on(base_params, ctx)),
            ("modo", await ac_set_mode({**base_params, "mode": "FAN"}, ctx)),
            ("vento", await ac_set_fan_speed({**base_params, "fan_speed": "LOW"}, ctx)),
            ("oscilacao", await ac_set_swing({**base_params, "enabled": True}, ctx)),
        ]
    else:
        return ActionResult(
            success=False,
            message="Preset desconhecido.",
            error="unsupported preset; use 'modo dormir', 'gelar sala', 'modo visita', 'economia' ou 'ventilar leve'",
        )

    failed = [f"{label}: {result.error or result.message}" for label, result in sequence if not result.success]
    if failed:
        return ActionResult(
            success=False,
            message="Preset executado parcialmente.",
            data={"steps": [{"label": label, "success": result.success, "message": result.message} for label, result in sequence]},
            error="; ".join(failed),
        )

    return ActionResult(
        success=True,
        message=f"Preset aplicado: {preset_raw}.",
        data={"steps": [{"label": label, "success": result.success, "message": result.message} for label, result in sequence]},
    )


async def ac_configure_arrival_prefs(
    params: JsonObject,
    ctx: ActionContext,
    *,
    load_ac_arrival_prefs: Callable[[], JsonObject],
    save_ac_arrival_prefs: Callable[[JsonObject], None],
    thinq_default_ac_name: Callable[[], str],
    coerce_optional_str: Callable[[Any], str | None],
) -> ActionResult:
    _ = ctx
    prefs = _resolve_ac_arrival_prefs(
        params,
        load_ac_arrival_prefs=load_ac_arrival_prefs,
        thinq_default_ac_name=thinq_default_ac_name,
        coerce_optional_str=coerce_optional_str,
    )
    if float(prefs["vent_only_threshold"]) > float(prefs["hot_threshold"]):
        return ActionResult(
            success=False,
            message="O limite de ventilacao nao pode ser maior que o limite de calor forte.",
            error="invalid thresholds",
        )
    save_ac_arrival_prefs(prefs)
    automation_enabled = bool(prefs.get("automation_enabled", False))
    if automation_enabled and not str(prefs.get("presence_entity_id") or "").strip():
        automation_enabled = False
        prefs["automation_enabled"] = False
    return ActionResult(
        success=True,
        message="Preferencias de chegada em casa salvas.",
        data={
            "preferences": prefs,
            "arrival_automation": {
                "enabled": automation_enabled,
                "presence_entity_id": prefs.get("presence_entity_id"),
                "cooldown_seconds": prefs.get("cooldown_seconds"),
                "run_live_after_dry_run": bool(prefs.get("run_live_after_dry_run", True)),
            },
        },
    )


async def ac_prepare_arrival(
    params: JsonObject,
    ctx: ActionContext,
    *,
    load_ac_arrival_prefs: Callable[[], JsonObject],
    thinq_default_ac_name: Callable[[], str],
    coerce_optional_str: Callable[[Any], str | None],
    ac_get_status: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
    ac_turn_on: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
    ac_set_mode: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
    ac_set_temperature: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
    ac_set_fan_speed: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
    ac_set_swing: Callable[[JsonObject, ActionContext], Awaitable[ActionResult]],
) -> ActionResult:
    prefs = _resolve_ac_arrival_prefs(
        params,
        load_ac_arrival_prefs=load_ac_arrival_prefs,
        thinq_default_ac_name=thinq_default_ac_name,
        coerce_optional_str=coerce_optional_str,
    )
    target_name = coerce_optional_str(params.get("device_name")) or coerce_optional_str(prefs.get("device_name")) or thinq_default_ac_name()
    target_id = coerce_optional_str(params.get("device_id"))
    dry_run = bool(params.get("dry_run"))
    trigger_source = coerce_optional_str(params.get("trigger_source")) or "manual"
    executed_at = datetime.now(timezone.utc).isoformat()

    status_result = await ac_get_status({"device_name": target_name, "device_id": target_id}, ctx)
    if not status_result.success:
        return status_result

    status_data = status_result.data if isinstance(status_result.data, dict) else {}
    current_temperature = _ac_current_temperature_from_status(status_data)
    if current_temperature is None:
        return ActionResult(
            success=False,
            message="Nao consegui ler a temperatura atual do ambiente pelo ar.",
            error="missing current temperature",
        )

    desired_temperature = float(prefs["desired_temperature"])
    hot_threshold = float(prefs["hot_threshold"])
    vent_only_threshold = float(prefs["vent_only_threshold"])
    eta_minutes = int(prefs["eta_minutes"])
    enable_swing = bool(prefs["enable_swing"])

    if current_temperature >= hot_threshold:
        strategy = "cool"
        fan_speed = "HIGH" if current_temperature - desired_temperature >= 3 else "MID"
        actions_to_run: list[tuple[str, Callable[[], Awaitable[ActionResult]]]] = [
            ("ligar", lambda: ac_turn_on({"device_name": target_name, "device_id": target_id}, ctx)),
            ("modo", lambda: ac_set_mode({"device_name": target_name, "device_id": target_id, "mode": "COOL"}, ctx)),
            (
                "temperatura",
                lambda: ac_set_temperature(
                    {"device_name": target_name, "device_id": target_id, "temperature": desired_temperature},
                    ctx,
                ),
            ),
            ("vento", lambda: ac_set_fan_speed({"device_name": target_name, "device_id": target_id, "fan_speed": fan_speed}, ctx)),
        ]
        if enable_swing:
            actions_to_run.append(("oscilacao", lambda: ac_set_swing({"device_name": target_name, "device_id": target_id, "enabled": True}, ctx)))
        message = (
            f"Ambiente a {current_temperature:.1f}C: esta quente. "
            f"Vou resfriar para {desired_temperature:.1f}C (ETA {eta_minutes} min)."
        )
    elif current_temperature >= vent_only_threshold:
        strategy = "fan"
        actions_to_run = [
            ("ligar", lambda: ac_turn_on({"device_name": target_name, "device_id": target_id}, ctx)),
            ("modo", lambda: ac_set_mode({"device_name": target_name, "device_id": target_id, "mode": "FAN"}, ctx)),
            ("vento", lambda: ac_set_fan_speed({"device_name": target_name, "device_id": target_id, "fan_speed": "LOW"}, ctx)),
        ]
        if enable_swing:
            actions_to_run.append(("oscilacao", lambda: ac_set_swing({"device_name": target_name, "device_id": target_id, "enabled": True}, ctx)))
        message = (
            f"Ambiente a {current_temperature:.1f}C: esta morno. "
            f"So ventilar ja deve bastar (ETA {eta_minutes} min)."
        )
    else:
        strategy = "hold"
        actions_to_run = []
        message = f"Ambiente a {current_temperature:.1f}C: temperatura aceitavel. Nao precisa mexer no ar agora."

    if dry_run or not actions_to_run:
        return ActionResult(
            success=True,
            message=message + (" (dry-run)" if dry_run else ""),
            data={
                "strategy": strategy,
                "current_temperature": current_temperature,
                "preferences": prefs,
                "applied": False,
                "device_name": target_name,
                "automation": {
                    "trigger_source": trigger_source,
                    "dry_run": dry_run,
                    "executed_at": executed_at,
                },
            },
            evidence={
                "kind": "ac_prepare_arrival",
                "trigger_source": trigger_source,
                "dry_run": dry_run,
                "strategy": strategy,
                "current_temperature": current_temperature,
                "executed_at": executed_at,
            },
        )

    results: list[tuple[str, ActionResult]] = []
    for label, runner in actions_to_run:
        results.append((label, await runner()))

    failed = [f"{label}: {result.error or result.message}" for label, result in results if not result.success]
    if failed:
        return ActionResult(
            success=False,
            message="Falha ao preparar a chegada em casa.",
            error="; ".join(failed),
            data={
                "strategy": strategy,
                "current_temperature": current_temperature,
                "preferences": prefs,
                "steps": [label for label, _ in results],
                "device_name": target_name,
                "automation": {
                    "trigger_source": trigger_source,
                    "dry_run": dry_run,
                    "executed_at": executed_at,
                },
            },
            evidence={
                "kind": "ac_prepare_arrival",
                "trigger_source": trigger_source,
                "dry_run": dry_run,
                "strategy": strategy,
                "current_temperature": current_temperature,
                "executed_at": executed_at,
                "error": "; ".join(failed),
            },
        )

    return ActionResult(
        success=True,
        message=message,
        data={
            "strategy": strategy,
            "current_temperature": current_temperature,
            "preferences": prefs,
            "applied": True,
            "steps": [label for label, _ in results],
            "device_name": target_name,
            "automation": {
                "trigger_source": trigger_source,
                "dry_run": dry_run,
                "executed_at": executed_at,
            },
        },
        evidence={
            "kind": "ac_prepare_arrival",
            "trigger_source": trigger_source,
            "dry_run": dry_run,
            "strategy": strategy,
            "current_temperature": current_temperature,
            "executed_at": executed_at,
        },
    )
