from __future__ import annotations

import os
from collections.abc import Callable
from datetime import datetime
from typing import Any

from actions_core import ActionContext, ActionResult

JsonObject = dict[str, Any]


async def spotify_status(
    params: JsonObject,
    ctx: ActionContext,
    *,
    spotify_initialize_cache: Callable[[], None],
    spotify_api_request: Callable[..., tuple[JsonObject | list[Any] | None, ActionResult | None]],
) -> ActionResult:
    _ = params, ctx
    spotify_initialize_cache()
    me, error = spotify_api_request("GET", "me")
    if error is not None:
        return error

    devices_payload, _ = spotify_api_request("GET", "me/player/devices")
    devices = devices_payload.get("devices", []) if isinstance(devices_payload, dict) else []
    active_devices = []
    if isinstance(devices, list):
        active_devices = [str(d.get("name", "")) for d in devices if isinstance(d, dict) and d.get("is_active")]

    return ActionResult(
        success=True,
        message="Spotify conectado e pronto para uso.",
        data={
            "spotify_connected": True,
            "user_id": me.get("id") if isinstance(me, dict) else None,
            "display_name": me.get("display_name") if isinstance(me, dict) else None,
            "active_devices": active_devices,
        },
    )


async def spotify_get_devices(
    params: JsonObject,
    ctx: ActionContext,
    *,
    spotify_api_request: Callable[..., tuple[JsonObject | list[Any] | None, ActionResult | None]],
) -> ActionResult:
    _ = params, ctx
    payload, error = spotify_api_request("GET", "me/player/devices")
    if error is not None:
        return error
    devices = payload.get("devices", []) if isinstance(payload, dict) else []
    if not isinstance(devices, list):
        devices = []
    mapped = [
        {
            "id": str(device.get("id", "")),
            "name": str(device.get("name", "")),
            "type": str(device.get("type", "")),
            "is_active": bool(device.get("is_active")),
            "volume_percent": device.get("volume_percent"),
        }
        for device in devices
        if isinstance(device, dict)
    ]
    return ActionResult(success=True, message=f"{len(mapped)} device(s) Spotify encontrados.", data={"devices": mapped})


async def spotify_transfer_playback(
    params: JsonObject,
    ctx: ActionContext,
    *,
    coerce_optional_str: Callable[[Any], str | None],
    spotify_find_device: Callable[[str | None, str | None], tuple[JsonObject | None, ActionResult | None]],
    spotify_api_request: Callable[..., tuple[JsonObject | list[Any] | None, ActionResult | None]],
    spotify_remember_device_alias: Callable[[str, str], None],
) -> ActionResult:
    _ = ctx
    requested_device_name = coerce_optional_str(params.get("device_name"))
    requested_device_id = coerce_optional_str(params.get("device_id"))
    play_now = bool(params.get("play", True))
    device, error = spotify_find_device(requested_device_name, requested_device_id)
    if error is not None:
        return error
    if device is None:
        return ActionResult(success=False, message="Nao consegui resolver o device Spotify.", error="device not found")

    _, request_error = spotify_api_request(
        "PUT",
        "me/player",
        body={"device_ids": [str(device.get("id"))], "play": play_now},
    )
    if request_error is not None:
        return request_error
    if requested_device_name:
        spotify_remember_device_alias(requested_device_name, str(device.get("id", "")).strip())

    return ActionResult(
        success=True,
        message=f"Playback transferido para {device.get('name', 'device desconhecido')}.",
        data={"device_id": device.get("id"), "device_name": device.get("name"), "is_active": True},
    )


async def spotify_play(
    params: JsonObject,
    ctx: ActionContext,
    *,
    coerce_optional_str: Callable[[Any], str | None],
    normalize_spotify_uri: Callable[[str], str],
    spotify_find_device: Callable[[str | None, str | None], tuple[JsonObject | None, ActionResult | None]],
    spotify_api_request: Callable[..., tuple[JsonObject | list[Any] | None, ActionResult | None]],
    is_spotify_restriction_error: Callable[[ActionResult | None], bool],
    spotify_remember_device_alias: Callable[[str, str], None],
) -> ActionResult:
    _ = ctx
    requested_device_name = coerce_optional_str(params.get("device_name")) or coerce_optional_str(
        os.getenv("SPOTIFY_DEFAULT_DEVICE_NAME", "")
    )
    requested_device_id = coerce_optional_str(params.get("device_id"))
    query = str(params.get("query", "")).strip()
    uri = normalize_spotify_uri(str(params.get("uri", "")))
    target_device: JsonObject | None = None
    if requested_device_name or requested_device_id:
        target_device, target_error = spotify_find_device(requested_device_name, requested_device_id)
        if target_error is not None:
            return target_error

    resolved_uri = uri
    resolved_title = None
    if query and not resolved_uri:
        search_payload, search_error = spotify_api_request(
            "GET",
            "search",
            params={"q": query, "type": "track", "limit": 1},
        )
        if search_error is not None:
            return search_error
        tracks = search_payload.get("tracks", {}).get("items", []) if isinstance(search_payload, dict) else []
        if not isinstance(tracks, list) or not tracks:
            return ActionResult(success=False, message=f"Nao encontrei musica para '{query}'.", error="track not found")
        first = tracks[0]
        if not isinstance(first, dict):
            return ActionResult(success=False, message=f"Nao encontrei musica para '{query}'.", error="track not found")
        resolved_uri = str(first.get("uri", "")).strip()
        artist_names = ", ".join(
            str(artist.get("name", "")) for artist in first.get("artists", []) if isinstance(artist, dict)
        )
        resolved_title = f"{first.get('name', 'Faixa')} - {artist_names}".strip(" -")

    body: JsonObject | None = None
    if resolved_uri:
        if resolved_uri.startswith("spotify:track:"):
            body = {"uris": [resolved_uri]}
        else:
            body = {"context_uri": resolved_uri}

    play_params: JsonObject | None = None
    if target_device and target_device.get("id"):
        play_params = {"device_id": str(target_device.get("id"))}

    _, play_error = spotify_api_request("PUT", "me/player/play", params=play_params, body=body)
    if play_error is not None:
        if target_device and is_spotify_restriction_error(play_error):
            fallback_body = {"device_ids": [str(target_device.get("id"))], "play": True}
            _, transfer_error = spotify_api_request("PUT", "me/player", body=fallback_body)
            if transfer_error is None:
                if requested_device_name:
                    spotify_remember_device_alias(requested_device_name, str(target_device.get("id", "")).strip())
                return ActionResult(
                    success=True,
                    message=f"Playback transferido e retomado em {target_device.get('name', 'device desconhecido')}.",
                    data={
                        "device_id": target_device.get("id"),
                        "device_name": target_device.get("name"),
                        "uri": resolved_uri,
                        "title": resolved_title,
                    },
                )
        return play_error

    if resolved_uri:
        if requested_device_name and target_device:
            spotify_remember_device_alias(requested_device_name, str(target_device.get("id", "")).strip())
        return ActionResult(
            success=True,
            message=f"Tocando agora: {resolved_title or resolved_uri}.",
            data={
                "uri": resolved_uri,
                "title": resolved_title,
                "device_id": target_device.get("id") if target_device else None,
                "device_name": target_device.get("name") if target_device else None,
            },
        )
    return ActionResult(success=True, message="Playback retomado no Spotify.")


async def spotify_pause(
    params: JsonObject,
    ctx: ActionContext,
    *,
    spotify_api_request: Callable[..., tuple[JsonObject | list[Any] | None, ActionResult | None]],
) -> ActionResult:
    _ = params, ctx
    _, error = spotify_api_request("PUT", "me/player/pause")
    if error is not None:
        return error
    return ActionResult(success=True, message="Playback pausado.")


async def spotify_next_track(
    params: JsonObject,
    ctx: ActionContext,
    *,
    spotify_api_request: Callable[..., tuple[JsonObject | list[Any] | None, ActionResult | None]],
) -> ActionResult:
    _ = params, ctx
    _, error = spotify_api_request("POST", "me/player/next")
    if error is not None:
        return error
    return ActionResult(success=True, message="Faixa avancada.")


async def spotify_previous_track(
    params: JsonObject,
    ctx: ActionContext,
    *,
    spotify_api_request: Callable[..., tuple[JsonObject | list[Any] | None, ActionResult | None]],
) -> ActionResult:
    _ = params, ctx
    _, error = spotify_api_request("POST", "me/player/previous")
    if error is not None:
        return error
    return ActionResult(success=True, message="Voltando para a faixa anterior.")


async def spotify_set_volume(
    params: JsonObject,
    ctx: ActionContext,
    *,
    coerce_optional_str: Callable[[Any], str | None],
    spotify_find_device: Callable[[str | None, str | None], tuple[JsonObject | None, ActionResult | None]],
    spotify_api_request: Callable[..., tuple[JsonObject | list[Any] | None, ActionResult | None]],
    spotify_remember_device_alias: Callable[[str, str], None],
) -> ActionResult:
    _ = ctx
    volume = int(params.get("volume_percent", 50))
    requested_device_name = coerce_optional_str(params.get("device_name"))
    requested_device_id = coerce_optional_str(params.get("device_id"))
    request_params: JsonObject = {"volume_percent": volume}

    if requested_device_name or requested_device_id:
        device, error = spotify_find_device(requested_device_name, requested_device_id)
        if error is not None:
            return error
        if device and device.get("id"):
            request_params["device_id"] = str(device.get("id"))

    _, request_error = spotify_api_request("PUT", "me/player/volume", params=request_params)
    if request_error is not None:
        return request_error
    if requested_device_name and "device_id" in request_params:
        spotify_remember_device_alias(requested_device_name, str(request_params["device_id"]))
    return ActionResult(success=True, message=f"Volume do Spotify ajustado para {volume}%.")


async def spotify_create_surprise_playlist(
    params: JsonObject,
    ctx: ActionContext,
    *,
    spotify_api_request: Callable[..., tuple[JsonObject | list[Any] | None, ActionResult | None]],
    spotify_pick_surprise_tracks: Callable[[JsonObject | None], list[str]],
) -> ActionResult:
    _ = ctx
    playlist_name = str(params.get("name", "")).strip() or f"Jarvez Surprise {datetime.now().strftime('%Y-%m-%d')}"
    public = bool(params.get("public", False))

    me_payload, me_error = spotify_api_request("GET", "me")
    if me_error is not None:
        return me_error
    user_id = str(me_payload.get("id", "")).strip() if isinstance(me_payload, dict) else ""
    if not user_id:
        return ActionResult(success=False, message="Nao consegui identificar sua conta Spotify.", error="missing user id")

    top_tracks_payload, _ = spotify_api_request(
        "GET",
        "me/top/tracks",
        params={"time_range": "long_term", "limit": 20},
    )
    selected_uris = spotify_pick_surprise_tracks(top_tracks_payload if isinstance(top_tracks_payload, dict) else None)

    playlist_payload, create_error = spotify_api_request(
        "POST",
        f"users/{user_id}/playlists",
        body={
            "name": playlist_name,
            "description": "Playlist surpresa criada pelo Jarvez.",
            "public": public,
        },
    )
    if create_error is not None:
        return create_error

    playlist_id = str(playlist_payload.get("id", "")).strip() if isinstance(playlist_payload, dict) else ""
    if not playlist_id:
        return ActionResult(success=False, message="Spotify nao retornou id da playlist criada.", error="playlist id missing")

    _, add_error = spotify_api_request("POST", f"playlists/{playlist_id}/tracks", body={"uris": selected_uris})
    if add_error is not None:
        return add_error

    playlist_url = ""
    if isinstance(playlist_payload, dict):
        external_urls = playlist_payload.get("external_urls", {})
        if isinstance(external_urls, dict):
            playlist_url = str(external_urls.get("spotify", ""))

    return ActionResult(
        success=True,
        message=f"Playlist surpresa criada: {playlist_name}.",
        data={
            "playlist_id": playlist_id,
            "playlist_name": playlist_name,
            "playlist_url": playlist_url,
            "tracks_added": len(selected_uris),
            "tracks": selected_uris,
        },
    )
