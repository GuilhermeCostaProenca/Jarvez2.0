import json
import logging
import os
import re
import secrets
from typing import Any

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentSession, ChatContext, RoomInputOptions, function_tool
from livekit.agents.voice.events import RunContext
from livekit.plugins import google, noise_cancellation
from mem0 import AsyncMemoryClient

from actions import (
    ActionContext,
    action_spec_to_raw_schema,
    dispatch_action,
    get_exposed_actions,
    is_authenticated_session,
)
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_USER_NAME = os.getenv('JARVEZ_USER_NAME', 'Usuario')
PUBLIC_SCOPE = 'public'
PRIVATE_SCOPE = 'private'
SENSITIVE_MEMORY_RE = re.compile(
    r'\b(senha|pin|cpf|cart[aã]o|banco|conta|endere[cç]o|telefone|email|segredo|doen[cç]a|sa[uú]de|trauma|intim[oa])\b',
    re.IGNORECASE,
)
EXPLICIT_PRIVATE_RE = re.compile(
    r'\b(segredo|privad[oa]|n[aã]o conta|nao conta|entre n[oó]s|isso e segredo)\b',
    re.IGNORECASE,
)
EXPLICIT_PUBLIC_RE = re.compile(
    r'\b(n[aã]o e segredo|nao e segredo|pode compartilhar|isso e publico|isso e p[uú]blico)\b',
    re.IGNORECASE,
)


def vision_dependencies_available() -> bool:
    try:
        import PIL  # noqa: F401
    except Exception:
        return False
    return True


class Assistant(Agent):
    def __init__(self, chat_ctx: ChatContext | None = None, tools: list[object] | None = None):
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=google.beta.realtime.RealtimeModel(
                voice='Charon',
                temperature=0.6,
            ),
            chat_ctx=chat_ctx,
            tools=tools,
        )


def _scoped_user_id(user_id: str, scope: str) -> str:
    return f'{user_id}::{scope}'


def _extract_item_text(item: Any) -> str:
    content = getattr(item, 'content', None)
    if content is None:
        return ''
    if isinstance(content, list):
        return ''.join(part for part in content if isinstance(part, str)).strip()
    return str(content).strip()


def _detect_scope_for_text(text: str, fallback_scope: str) -> str:
    if EXPLICIT_PUBLIC_RE.search(text):
        return PUBLIC_SCOPE
    if EXPLICIT_PRIVATE_RE.search(text):
        return PRIVATE_SCOPE
    if SENSITIVE_MEMORY_RE.search(text):
        return PRIVATE_SCOPE
    return fallback_scope


def _prepare_memory_batches(chat_ctx: ChatContext, loaded_memory_blobs: set[str]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    public_batch: list[dict[str, str]] = []
    private_batch: list[dict[str, str]] = []
    current_scope = PUBLIC_SCOPE

    for item in chat_ctx.items:
        role = getattr(item, 'role', None)
        if role not in {'user', 'assistant'}:
            continue

        text = _extract_item_text(item)
        if not text:
            continue
        if any(blob and blob in text for blob in loaded_memory_blobs):
            continue

        if role == 'user':
            current_scope = _detect_scope_for_text(text, current_scope)

        target = private_batch if current_scope == PRIVATE_SCOPE else public_batch
        target.append({'role': role, 'content': text})

        # assistant answer follows same scope as triggering user message only once
        if role == 'assistant':
            current_scope = PUBLIC_SCOPE

    return public_batch, private_batch


async def _load_memories(mem0: AsyncMemoryClient, scoped_user_id: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    try:
        raw_results = await mem0.get_all(user_id=scoped_user_id)
        if isinstance(raw_results, list):
            results = [item for item in raw_results if isinstance(item, dict)]
        logger.info('Retrieved %s memories for %s using get_all', len(results), scoped_user_id)
    except Exception as error:
        logger.warning('get_all failed for %s: %s', scoped_user_id, error)
        try:
            response = await mem0.search('informacoes preferencias contexto', filters={'user_id': scoped_user_id})
            candidate = response['results'] if isinstance(response, dict) and 'results' in response else response
            if isinstance(candidate, list):
                results = [item for item in candidate if isinstance(item, dict)]
            logger.info('Retrieved %s memories for %s using search', len(results), scoped_user_id)
        except Exception as search_error:
            logger.warning('search failed for %s: %s', scoped_user_id, search_error)
            results = []
    return results


def _memory_json_blob(memories: list[dict[str, Any]]) -> str:
    filtered = []
    for result in memories:
        memory_text = result.get('memory')
        if not memory_text:
            continue
        filtered.append(
            {
                'memory': memory_text,
                'updated_at': result.get('updated_at', ''),
            }
        )
    return json.dumps(filtered, ensure_ascii=False) if filtered else ''


def resolve_user_identity(ctx: agents.JobContext) -> tuple[str, str]:
    participant = getattr(ctx.job, 'participant', None)
    participant_identity = getattr(participant, 'identity', None)
    participant_name = getattr(participant, 'name', None)

    if participant_identity:
        return participant_identity, participant_name or DEFAULT_USER_NAME

    room_name = getattr(getattr(ctx.job, 'room', None), 'name', 'room')
    fallback_identity = f"anon-{room_name}-{secrets.token_hex(3)}"
    return fallback_identity, participant_name or DEFAULT_USER_NAME


def build_action_tools(
    *,
    job_id: str,
    room_name: str,
    participant_identity: str,
    mem0: AsyncMemoryClient,
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
            )
            result = await dispatch_action(_action_name, params, action_ctx)

            if _action_name == 'authenticate_identity' and result.success:
                private_results = await _load_memories(mem0, _scoped_user_id(user_id, PRIVATE_SCOPE))
                private_blob = _memory_json_blob(private_results)
                if private_blob:
                    if result.data is None:
                        result.data = {}
                    result.data['private_memories_loaded'] = len(private_results)
                    result.data['private_memories'] = private_blob

            return result.to_json()

        tools.append(function_tool(_tool, raw_schema=action_spec_to_raw_schema(spec)))

    return tools


async def entrypoint(ctx: agents.JobContext):
    user_id, user_name = resolve_user_identity(ctx)
    loaded_memory_blobs: set[str] = set()

    async def shutdown_hook(chat_ctx: ChatContext, mem0: AsyncMemoryClient):
        logging.info('Shutting down, saving chat context to memory...')
        public_batch, private_batch = _prepare_memory_batches(chat_ctx, loaded_memory_blobs)

        if public_batch:
            await mem0.add(public_batch, user_id=_scoped_user_id(user_id, PUBLIC_SCOPE))
            logging.info('Saved %s public messages to memory.', len(public_batch))

        if private_batch:
            await mem0.add(private_batch, user_id=_scoped_user_id(user_id, PRIVATE_SCOPE))
            logging.info('Saved %s private messages to memory.', len(private_batch))

        if not public_batch and not private_batch:
            logging.info('No new messages to persist.')

    mem0 = AsyncMemoryClient()
    initial_ctx = ChatContext()
    public_results = await _load_memories(mem0, _scoped_user_id(user_id, PUBLIC_SCOPE))
    public_blob = _memory_json_blob(public_results)
    if public_blob:
        loaded_memory_blobs.add(public_blob)
        initial_ctx.add_message(
            role='assistant',
            content=f'O nome do usuario e {user_name}. Memorias publicas conhecidas: {public_blob}.',
        )

    room_name = getattr(getattr(ctx.job, 'room', None), 'name', 'room')
    if is_authenticated_session(user_id, room_name):
        private_results = await _load_memories(mem0, _scoped_user_id(user_id, PRIVATE_SCOPE))
        private_blob = _memory_json_blob(private_results)
        if private_blob:
            loaded_memory_blobs.add(private_blob)
            initial_ctx.add_message(
                role='assistant',
                content=f'Memorias privadas liberadas para esta sessao: {private_blob}.',
            )
    elif not public_blob:
        logging.info('No memories found for this user. Starting fresh conversation.')

    await ctx.connect()

    session = AgentSession()
    room_name = getattr(ctx.room, 'name', 'room')
    job_id = getattr(ctx.job, 'id', '')
    action_tools = build_action_tools(
        job_id=job_id,
        room_name=room_name,
        participant_identity=user_id,
        mem0=mem0,
        user_id=user_id,
    )
    agent = Assistant(chat_ctx=initial_ctx, tools=action_tools)

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

    ctx.add_shutdown_callback(lambda: shutdown_hook(agent.chat_ctx, mem0))
    await session.generate_reply(
        instructions=SESSION_INSTRUCTION + '\nCumprimente o usuario de forma breve e confiante.'
    )


if __name__ == '__main__':
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
