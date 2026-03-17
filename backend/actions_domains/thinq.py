from __future__ import annotations

from collections.abc import Callable
from typing import Any

from actions_core import ActionContext, ActionResult

JsonObject = dict[str, Any]


async def thinq_status(
    params: JsonObject,
    ctx: ActionContext,
    *,
    thinq_api_request: Callable[..., tuple[JsonObject | list[Any] | None, ActionResult | None]],
    thinq_list_devices_payload: Callable[[], tuple[list[JsonObject] | None, ActionResult | None]],
    thinq_pat: Callable[[], str],
    thinq_country: Callable[[], str],
    thinq_api_base: Callable[[], str],
) -> ActionResult:
    _ = params, ctx
    route_payload, route_error = thinq_api_request("GET", "route", require_auth=False)
    devices, devices_error = thinq_list_devices_payload()
    if route_error is not None and devices_error is not None:
        return devices_error

    return ActionResult(
        success=True,
        message="ThinQ configurado." if devices_error is None else "ThinQ parcialmente configurado.",
        data={
            "thinq_configured": bool(thinq_pat()),
            "country": thinq_country(),
            "api_base": thinq_api_base(),
            "route": route_payload if route_error is None else None,
            "devices_count": len(devices or []),
            "devices_error": devices_error.error if devices_error is not None else None,
        },
    )


async def thinq_list_devices(
    params: JsonObject,
    ctx: ActionContext,
    *,
    thinq_list_devices_payload: Callable[[], tuple[list[JsonObject] | None, ActionResult | None]],
    thinq_simplify_device: Callable[[JsonObject], JsonObject],
) -> ActionResult:
    _ = params, ctx
    devices, error = thinq_list_devices_payload()
    if error is not None:
        return error
    simplified = [thinq_simplify_device(item) for item in devices or []]
    return ActionResult(
        success=True,
        message=f"Encontrei {len(simplified)} dispositivo(s) no ThinQ.",
        data={"devices": simplified},
    )


async def thinq_get_device_profile(
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
    )
    if error is not None:
        return error
    assert device is not None
    device_id = quote_path_segment(thinq_extract_device_id(device))
    payload, request_error = thinq_api_request("GET", f"devices/{device_id}/profile")
    if request_error is not None:
        return request_error
    return ActionResult(
        success=True,
        message=f"Perfil carregado para {thinq_extract_device_alias(device)}.",
        data={
            "device": thinq_simplify_device(device),
            "profile": payload if isinstance(payload, dict) else {"raw": payload},
        },
    )


async def thinq_get_device_state(
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
    )
    if error is not None:
        return error
    assert device is not None
    device_id = quote_path_segment(thinq_extract_device_id(device))
    payload, request_error = thinq_api_request("GET", f"devices/{device_id}/state")
    if request_error is not None:
        return request_error
    return ActionResult(
        success=True,
        message=f"Estado carregado para {thinq_extract_device_alias(device)}.",
        data={
            "device": thinq_simplify_device(device),
            "state": payload if isinstance(payload, dict) else {"raw": payload},
        },
    )


async def thinq_control_device(
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
    )
    if error is not None:
        return error
    assert device is not None

    command = params.get("command")
    if not isinstance(command, dict) or not command:
        return ActionResult(
            success=False,
            message="Comando ThinQ invalido.",
            error="missing or invalid command object",
        )

    conditional = bool(params.get("conditional"))
    device_id = quote_path_segment(thinq_extract_device_id(device))
    _, request_error = thinq_api_request(
        "POST",
        f"devices/{device_id}/control",
        body=command,
        extra_headers={"x-conditional-control": "true"} if conditional else None,
    )
    if request_error is not None:
        return request_error

    return ActionResult(
        success=True,
        message=f"Comando enviado para {thinq_extract_device_alias(device)}.",
        data={
            "device": thinq_simplify_device(device),
            "conditional": conditional,
            "command": command,
        },
    )
