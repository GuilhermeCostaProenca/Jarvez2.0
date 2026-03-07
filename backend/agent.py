import json
import logging
import os
import secrets

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentSession, ChatContext, RoomInputOptions, function_tool
from livekit.agents.voice.events import RunContext
from livekit.plugins import google, noise_cancellation
from mem0 import AsyncMemoryClient

from actions import ActionContext, action_spec_to_raw_schema, dispatch_action, get_exposed_actions
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_USER_NAME = os.getenv('JARVEZ_USER_NAME', 'Usuario')


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
            return result.to_json()

        tools.append(function_tool(_tool, raw_schema=action_spec_to_raw_schema(spec)))

    return tools


async def entrypoint(ctx: agents.JobContext):
    user_id, user_name = resolve_user_identity(ctx)

    async def shutdown_hook(chat_ctx: ChatContext, mem0: AsyncMemoryClient, memory_str: str):
        logging.info('Shutting down, saving chat context to memory...')
        messages_formatted = []

        for item in chat_ctx.items:
            if not hasattr(item, 'content') or item.content is None:
                continue
            content_str = ''.join(item.content) if isinstance(item.content, list) else str(item.content)

            if memory_str and memory_str in content_str:
                continue

            if item.role in ['user', 'assistant']:
                messages_formatted.append({'role': item.role, 'content': content_str.strip()})

        if messages_formatted:
            await mem0.add(messages_formatted, user_id=user_id)
            logging.info('Chat context saved to memory.')
        else:
            logging.info('No new messages to persist.')

    mem0 = AsyncMemoryClient()
    initial_ctx = ChatContext()
    memory_str = ''
    results = []

    try:
        results = await mem0.get_all(user_id=user_id)
        logging.info(f'Retrieved {len(results) if results else 0} memories using get_all')
    except Exception as error:
        logging.warning(f'get_all failed: {error}. Trying search method...')
        try:
            response = await mem0.search('informacoes preferencias contexto', filters={'user_id': user_id})
            results = response['results'] if isinstance(response, dict) and 'results' in response else response
            logging.info(f'Retrieved {len(results) if results else 0} memories using search')
        except Exception as search_error:
            logging.warning(f'Search also failed: {search_error}. No memories loaded.')
            results = []

    if results:
        memories = [
            {
                'memory': result.get('memory') if isinstance(result, dict) else result.get('memory', ''),
                'updated_at': result.get('updated_at') if isinstance(result, dict) else result.get('updated_at', ''),
            }
            for result in results
            if isinstance(result, dict) and result.get('memory')
        ]
        if memories:
            memory_str = json.dumps(memories, ensure_ascii=False)
            initial_ctx.add_message(
                role='assistant',
                content=f'O nome do usuario e {user_name}. Aqui estao informacoes importantes sobre ele: {memory_str}.',
            )
    else:
        logging.info('No memories found for this user. Starting fresh conversation.')

    await ctx.connect()

    session = AgentSession()
    room_name = getattr(ctx.room, 'name', 'room')
    job_id = getattr(ctx.job, 'id', '')
    action_tools = build_action_tools(job_id=job_id, room_name=room_name, participant_identity=user_id)
    agent = Assistant(chat_ctx=initial_ctx, tools=action_tools)

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
            close_on_disconnect=False,
        ),
    )

    ctx.add_shutdown_callback(lambda: shutdown_hook(agent.chat_ctx, mem0, memory_str))
    await session.generate_reply(
        instructions=SESSION_INSTRUCTION + '\nCumprimente o usuario de forma breve e confiante.'
    )


if __name__ == '__main__':
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
