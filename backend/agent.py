import asyncio
import json
import logging
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import Agent, AgentSession, ChatContext, RoomInputOptions, function_tool
from livekit.agents.voice.events import RunContext
from livekit.rtc._proto.track_pb2 import TrackSource
from livekit.plugins import noise_cancellation
from mem0 import AsyncMemoryClient

load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=False)

from actions_core import get_state_store
from actions_core.events import publish_session_event
from actions import (
    ActionContext,
    action_spec_to_raw_schema,
    dispatch_action,
    get_memory_scope_override,
    get_exposed_actions,
    is_authenticated_session,
    record_autonomy_notice_delivery,
)
from channels.livekit_adapter import normalize_livekit_data_packet
from memory import MemoryManager
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION
from runtime.model_gateway import resolve_runtime
from runtime.realtime_adapters import build_realtime_runtime
from session_snapshot import publish_session_snapshot
from voice_interactivity import (
    VOICE_INTERACTIVITY_EVENT_TYPE,
    VOICE_INTERACTIVITY_NAMESPACE,
    build_voice_error_message,
    build_voice_interactivity_payload,
)
from voice_biometrics import capture_voice_frame

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_USER_NAME = os.getenv('JARVEZ_USER_NAME', 'Usuario')
# Legacy memory scope detection moved to backend/memory/memory_manager.py.
BOOL_FALSE_VALUES = {'0', 'false', 'off', 'no', 'nao', 'nÃ£o'}


def vision_dependencies_available() -> bool:
    try:
        import PIL  # noqa: F401
    except Exception:
        return False
    return True


class Assistant(Agent):
    def __init__(self, chat_ctx: ChatContext | None = None, tools: list[object] | None = None):
        runtime_decision = resolve_runtime(
            intent="voice_realtime",
            task_type="chat",
            risk="R1",
            required_capabilities=["realtime", "tools"],
        )
        voice_runtime = build_realtime_runtime(runtime_decision)
        agent_kwargs: dict[str, object] = {
            "instructions": AGENT_INSTRUCTION,
            "llm": voice_runtime.model,
            "chat_ctx": chat_ctx,
            "tools": tools,
        }
        if voice_runtime.tts is not None:
            agent_kwargs["tts"] = voice_runtime.tts
        super().__init__(
            **agent_kwargs,
        )
        self.runtime_decision = runtime_decision
        self.voice_provider_name = voice_runtime.provider.provider_name
        self.voice_name = voice_runtime.provider.voice_name


def _env_bool(name: str, default: bool = False) -> bool:
    raw = str(os.getenv(name, '1' if default else '0')).strip().lower()
    return raw not in BOOL_FALSE_VALUES


def _env_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw = str(os.getenv(name, str(default))).strip()
    try:
        value = int(raw)
    except Exception:
        value = default
    return max(minimum, min(value, maximum))


def _build_control_loop_params() -> dict[str, object]:
    params: dict[str, object] = {
        'dry_run': _env_bool('JARVEZ_CONTROL_LOOP_DRY_RUN', True),
        'auto_remediate': _env_bool('JARVEZ_CONTROL_LOOP_AUTO_REMEDIATE', True),
        'auto_promote_canary': _env_bool('JARVEZ_CONTROL_LOOP_AUTO_PROMOTE_CANARY', True),
        'force_remediation': _env_bool('JARVEZ_CONTROL_LOOP_FORCE_REMEDIATION', False),
        'force_promotion': _env_bool('JARVEZ_CONTROL_LOOP_FORCE_PROMOTION', False),
        'metrics_limit': _env_int('JARVEZ_CONTROL_LOOP_METRICS_LIMIT', 400, minimum=20, maximum=1200),
        'freeze_threshold': _env_int('JARVEZ_CONTROL_LOOP_FREEZE_THRESHOLD', 3, minimum=1, maximum=20),
        'freeze_window_seconds': _env_int('JARVEZ_CONTROL_LOOP_FREEZE_WINDOW_SECONDS', 900, minimum=60, maximum=86400),
        'freeze_cooldown_seconds': _env_int(
            'JARVEZ_CONTROL_LOOP_FREEZE_COOLDOWN_SECONDS',
            1800,
            minimum=60,
            maximum=86400,
        ),
    }
    domain = str(os.getenv('JARVEZ_CONTROL_LOOP_DOMAIN', '')).strip().lower()
    if len(domain) >= 2:
        params['domain'] = domain
    return params


async def _publish_voice_interactivity(
    session: AgentSession | None,
    *,
    participant_identity: str,
    room: str,
    state: str,
    source: str = "backend",
    activation_mode: str | None = None,
    raw_client_state: str | None = None,
    display_message: str | None = None,
    spoken_message: str | None = None,
    error_code: str | None = None,
    can_retry: bool | None = None,
    extra: dict[str, object] | None = None,
) -> None:
    payload = build_voice_interactivity_payload(
        state=state,
        source=source,
        activation_mode=activation_mode,
        raw_client_state=raw_client_state,
        display_message=display_message,
        spoken_message=spoken_message,
        error_code=error_code,
        can_retry=can_retry,
        extra=extra,
    )
    get_state_store().upsert_event_state(
        participant_identity=participant_identity,
        room=room,
        namespace=VOICE_INTERACTIVITY_NAMESPACE,
        payload=payload,
    )
    await publish_session_event(
        session,
        {
            "type": VOICE_INTERACTIVITY_EVENT_TYPE,
            "voice_interactivity": payload,
        },
    )


def _handle_client_telemetry_packet(
    packet: rtc.DataPacket,
    *,
    participant_identity: str,
    room_name: str,
    session: AgentSession | None,
) -> None:
    envelope = normalize_livekit_data_packet(packet, room=room_name)
    if envelope is None:
        return
    if envelope.topic != "jarvez.client.telemetry":
        return
    if envelope.identity.participant_identity != participant_identity:
        return
    payload = envelope.raw_payload.get("payload")
    if not isinstance(payload, dict):
        logger.warning("invalid client telemetry payload")
        return
    payload_type = str(payload.get("type") or "").strip()
    if payload_type == "voice_interactivity_client":
        state = str(payload.get("state") or "").strip()
        if not state:
            return
        asyncio.create_task(
            _publish_voice_interactivity(
                session,
                participant_identity=participant_identity,
                room=room_name,
                state=state,
                source="client",
                activation_mode=str(payload.get("activation_mode") or "").strip() or None,
                raw_client_state=str(payload.get("raw_client_state") or "").strip() or None,
                display_message=str(payload.get("display_message") or "").strip() or None,
                spoken_message=str(payload.get("spoken_message") or "").strip() or None,
                error_code=str(payload.get("error_code") or "").strip() or None,
                can_retry=bool(payload.get("can_retry")) if payload.get("can_retry") is not None else None,
                extra=(
                    {"wake_word_available": bool(payload.get("wake_word_available"))}
                    if payload.get("wake_word_available") is not None
                    else None
                ),
            ),
            name=f"voice_interactivity_client_{participant_identity}",
        )
        return
    if payload_type != "autonomy_notice_delivery":
        return
    channel = str(payload.get("channel") or "").strip().lower()
    if channel not in {"browser_tts"}:
        return
    record_autonomy_notice_delivery(
        participant_identity=participant_identity,
        room=room_name,
        trace_id=str(payload.get("trace_id") or "").strip() or None,
        signature=str(payload.get("signature") or "").strip() or None,
        channel=channel,
        level=str(payload.get("level") or "").strip() or None,
        domain=str(payload.get("domain") or "").strip() or None,
        scenario=str(payload.get("scenario") or "").strip() or None,
    )


async def _run_ops_control_loop(
    *,
    job_id: str,
    room_name: str,
    participant_identity: str,
    mem0: AsyncMemoryClient,
    user_id: str,
) -> None:
    interval_seconds = _env_int('JARVEZ_CONTROL_LOOP_INTERVAL_SECONDS', 90, minimum=15, maximum=3600)
    logger.info(
        'ops_control_loop started participant=%s room=%s interval=%ss',
        participant_identity,
        room_name,
        interval_seconds,
    )
    try:
        while True:
            params = _build_control_loop_params()
            action_ctx = ActionContext(
                job_id=job_id,
                room=room_name,
                participant_identity=participant_identity,
                memory_client=mem0,
                user_id=user_id,
            )
            result = await dispatch_action(
                'ops_control_loop_tick',
                params,
                action_ctx,
                skip_confirmation=True,
                bypass_auth=True,
            )
            if result.success:
                tick_data = result.data if isinstance(result.data, dict) else {}
                tick_report = tick_data.get('ops_control_tick') if isinstance(tick_data.get('ops_control_tick'), dict) else {}
                freeze = tick_report.get('freeze') if isinstance(tick_report, dict) else {}
                freeze_applied = bool(isinstance(freeze, dict) and freeze.get('applied'))
                logger.info(
                    'ops_control_loop tick success freeze_applied=%s message=%s',
                    freeze_applied,
                    result.message,
                )
            else:
                logger.warning('ops_control_loop tick failed: %s (%s)', result.message, result.error)
            await asyncio.sleep(interval_seconds)
    except asyncio.CancelledError:
        raise
    except Exception as error:
        logger.exception('ops_control_loop crashed: %s', error)
        raise


def resolve_user_identity(ctx: agents.JobContext) -> tuple[str, str]:
    participant = getattr(ctx.job, 'participant', None)
    participant_identity = getattr(participant, 'identity', None)
    participant_name = getattr(participant, 'name', None)

    if participant_identity:
        return participant_identity, participant_name or DEFAULT_USER_NAME

    remote_participants = getattr(getattr(ctx, 'room', None), 'remote_participants', None)
    if isinstance(remote_participants, dict):
        for remote in remote_participants.values():
            remote_identity = getattr(remote, 'identity', None)
            remote_name = getattr(remote, 'name', None)
            if remote_identity:
                return remote_identity, remote_name or DEFAULT_USER_NAME

    room_name = getattr(getattr(ctx.job, 'room', None), 'name', 'room')
    fallback_identity = f"anon-{room_name}"
    return fallback_identity, participant_name or DEFAULT_USER_NAME


async def _capture_microphone_stream(participant: rtc.RemoteParticipant, participant_identity: str) -> None:
    stream = rtc.AudioStream.from_participant(
        participant=participant,
        track_source=TrackSource.SOURCE_MICROPHONE,
        sample_rate=16000,
        num_channels=1,
        frame_size_ms=20,
    )
    try:
        async for event in stream:
            capture_voice_frame(participant_identity, event.frame)
    except asyncio.CancelledError:
        raise
    except Exception as error:
        logger.debug("voice_capture_stream_error participant=%s error=%s", participant_identity, error)
    finally:
        try:
            await stream.aclose()
        except Exception:
            pass


async def _run_voice_capture_manager(room: rtc.Room) -> None:
    tasks: dict[str, asyncio.Task[None]] = {}
    try:
        while True:
            remote_participants = getattr(room, "remote_participants", None)
            current: dict[str, rtc.RemoteParticipant] = (
                remote_participants if isinstance(remote_participants, dict) else {}
            )

            for identity, participant in current.items():
                if identity and identity not in tasks:
                    tasks[identity] = asyncio.create_task(
                        _capture_microphone_stream(participant, identity),
                        name=f"voice_capture_{identity}",
                    )

            removed = [identity for identity in list(tasks.keys()) if identity not in current]
            for identity in removed:
                task = tasks.pop(identity)
                task.cancel()
                try:
                    await task
                except Exception:
                    pass

            await asyncio.sleep(1.0)
    except asyncio.CancelledError:
        raise
    finally:
        for task in tasks.values():
            task.cancel()
        for task in tasks.values():
            try:
                await task
            except Exception:
                pass


def build_action_tools(
    *,
    job_id: str,
    room_name: str,
    participant_identity: str,
    mem0: AsyncMemoryClient,
    memory_manager: MemoryManager,
    user_id: str,
) -> list[object]:
    tools: list[object] = []

    for spec in get_exposed_actions():

        async def _tool(raw_arguments: dict[str, object], ctx: RunContext, _action_name: str = spec.name):
            params: dict[str, object] = raw_arguments if isinstance(raw_arguments, dict) else {}
            action_ctx = ActionContext(
                job_id=job_id,
                room=room_name,
                participant_identity=participant_identity,
                session=ctx.session,
                memory_client=mem0,
                user_id=user_id,
            )
            result = await dispatch_action(_action_name, params, action_ctx)

            if _action_name == 'authenticate_identity' and result.success:
                private_bundle = await memory_manager.load_scope_memories(
                    participant_identity=user_id,
                    scope="private",
                )
                private_blob = str(private_bundle.get("blob") or "").strip()
                if private_blob:
                    if result.data is None:
                        result.data = {}
                    result.data['private_memories_loaded'] = int(private_bundle.get("count") or 0)
                    result.data['private_memories'] = private_blob
                    logger.info(
                        "private_memory_access %s",
                        json.dumps(
                            {
                                "participant_identity": participant_identity,
                                "room": room_name,
                                "source": "authenticate_identity",
                                "count": int(private_bundle.get("count") or 0),
                            },
                            ensure_ascii=False,
                        ),
                    )

            return result.to_json()

        tools.append(function_tool(_tool, raw_schema=action_spec_to_raw_schema(spec)))

    return tools


async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()
    user_id, user_name = resolve_user_identity(ctx)
    room_name = getattr(getattr(ctx.job, 'room', None), 'name', 'room')
    session_id = f"{room_name}:{user_id}:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}:{secrets.token_hex(4)}"

    async def shutdown_hook(
        chat_ctx: ChatContext,
        memory_manager: MemoryManager,
        loaded_memory_markers: set[str],
    ):
        logging.info('Shutting down, saving chat context to memory...')
        await memory_manager.finalize_session(
            chat_ctx=chat_ctx,
            participant_identity=user_id,
            room=room_name,
            session_id=session_id,
            loaded_memory_markers=loaded_memory_markers,
            scope_override_getter=get_memory_scope_override,
        )

    mem0 = AsyncMemoryClient()
    memory_manager = MemoryManager(mem0=mem0, state_store=get_state_store())
    initial_ctx = ChatContext()
    bootstrap_context = await memory_manager.load_bootstrap_context(
        participant_identity=user_id,
        room=room_name,
        user_name=user_name,
        authenticated=is_authenticated_session(user_id, room_name),
    )
    loaded_memory_markers = set(bootstrap_context.loaded_memory_markers)
    for message in bootstrap_context.prompt_messages:
        initial_ctx.add_message(role='assistant', content=message)
    if not bootstrap_context.prompt_messages:
        logging.info('No memories found for this user. Starting fresh conversation.')

    session = AgentSession()
    job_id = getattr(ctx.job, 'id', '')
    action_tools = build_action_tools(
        job_id=job_id,
        room_name=room_name,
        participant_identity=user_id,
        mem0=mem0,
        memory_manager=memory_manager,
        user_id=user_id,
    )
    agent = Assistant(chat_ctx=initial_ctx, tools=action_tools)
    get_state_store().upsert_event_state(
        participant_identity=user_id,
        room=room_name,
        namespace="model_route",
        payload=agent.runtime_decision.to_payload(),
    )

    vision_enabled = vision_dependencies_available()
    if not vision_enabled:
        logger.warning(
            "Vision disabled: PIL dependency not available. Install backend requirements to enable camera/screen support."
        )

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            video_enabled=vision_enabled,
            noise_cancellation=noise_cancellation.BVC(),
            close_on_disconnect=False,
        ),
    )
    await _publish_voice_interactivity(
        session,
        participant_identity=user_id,
        room=room_name,
        state="idle",
        source="backend",
        activation_mode="button",
        display_message="Jarvez pronto para ouvir.",
    )
    await publish_session_snapshot(session, participant_identity=user_id, room=room_name)
    def _publish_snapshot_on_participant_connected(participant: rtc.RemoteParticipant) -> None:
        identity = str(getattr(participant, "identity", "") or "").strip()
        if not identity:
            return
        if identity != user_id:
            return
        asyncio.create_task(
            publish_session_snapshot(session, participant_identity=user_id, room=room_name),
            name=f"session_snapshot_reconnect_{identity}",
        )

    ctx.room.on("participant_connected", _publish_snapshot_on_participant_connected)
    ctx.room.on(
        "data_received",
        lambda packet: _handle_client_telemetry_packet(
            packet,
            participant_identity=user_id,
            room_name=room_name,
            session=session,
        ),
    )

    voice_capture_task = asyncio.create_task(_run_voice_capture_manager(ctx.room), name="voice_capture_manager")
    control_loop_enabled = _env_bool('JARVEZ_CONTROL_LOOP_ENABLED', False)
    control_loop_task: asyncio.Task[None] | None = None
    if control_loop_enabled:
        control_loop_task = asyncio.create_task(
            _run_ops_control_loop(
                job_id=job_id or 'ops-control-loop',
                room_name=room_name,
                participant_identity=user_id,
                mem0=mem0,
                user_id=user_id,
            ),
            name='ops_control_loop',
        )
    else:
        logger.info('ops_control_loop disabled by env')

    async def _cancel_voice_capture():
        voice_capture_task.cancel()
        try:
            await voice_capture_task
        except Exception:
            pass

    async def _cancel_control_loop():
        if control_loop_task is None:
            return
        control_loop_task.cancel()
        try:
            await control_loop_task
        except Exception:
            pass

    ctx.add_shutdown_callback(lambda: shutdown_hook(agent.chat_ctx, memory_manager, loaded_memory_markers))
    ctx.add_shutdown_callback(_cancel_voice_capture)
    try:
        await _publish_voice_interactivity(
            session,
            participant_identity=user_id,
            room=room_name,
            state="thinking",
            source="backend",
            display_message="Preparando resposta inicial.",
        )
        await session.generate_reply(
            instructions=SESSION_INSTRUCTION + '\nCumprimente o usuario de forma breve e confiante.'
        )
    except Exception as error:
        await _publish_voice_interactivity(
            session,
            participant_identity=user_id,
            room=room_name,
            state="error",
            source="backend",
            display_message="Falha ao iniciar a conversa.",
            spoken_message=build_voice_error_message(
                "session_generate_reply",
                "Falha ao iniciar a conversa.",
                str(error),
            ),
            error_code=str(error),
            can_retry=True,
        )
        logger.error('Failed to generate initial reply: %s', error)


if __name__ == '__main__':
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            ws_url=os.getenv("LIVEKIT_URL"),
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET"),
        )
    )
