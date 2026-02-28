import { useCallback, useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';
import { useChat, useTextStream } from '@livekit/components-react';
import type {
  ActionExecutionEvent,
  ActionResultPayload,
  PendingActionConfirmation,
  SecuritySessionState,
} from '@/lib/types/realtime';

interface FunctionCallItem {
  name?: string;
  call_id?: string;
}

interface FunctionCallOutputItem {
  name?: string;
  call_id?: string;
  output?: string;
}

interface FunctionToolsExecutedEvent {
  type?: string;
  function_calls?: FunctionCallItem[];
  function_call_outputs?: Array<FunctionCallOutputItem | null>;
}

function safeParseJson<T>(value: string): T | null {
  try {
    return JSON.parse(value) as T;
  } catch {
    return null;
  }
}

function extractActionResult(output?: string): ActionResultPayload | null {
  if (!output) return null;
  const parsed = safeParseJson<ActionResultPayload>(output);
  if (!parsed || typeof parsed.success !== 'boolean' || typeof parsed.message !== 'string') {
    return null;
  }
  return parsed;
}

export function useAgentActionEvents() {
  const { textStreams } = useTextStream('lk.agent.events');
  const { send } = useChat();

  const processedStreamIds = useRef<Set<string>>(new Set());
  const [pendingConfirmation, setPendingConfirmation] = useState<PendingActionConfirmation | null>(
    null
  );
  const [isConfirming, setIsConfirming] = useState(false);
  const [events, setEvents] = useState<ActionExecutionEvent[]>([]);
  const [securitySession, setSecuritySession] = useState<SecuritySessionState>({
    authenticated: false,
    identityBound: false,
    expiresIn: 0,
    stepUpRequired: false,
  });

  const pushEvent = useCallback((event: ActionExecutionEvent) => {
    setEvents((current) => [event, ...current].slice(0, 8));
  }, []);

  useEffect(() => {
    for (const stream of textStreams) {
      const streamId = stream.streamInfo?.id;
      if (!streamId || processedStreamIds.current.has(streamId)) {
        continue;
      }

      processedStreamIds.current.add(streamId);
      if (processedStreamIds.current.size > 1000) {
        processedStreamIds.current.clear();
      }

      const eventPayload = safeParseJson<FunctionToolsExecutedEvent>(stream.text);
      if (!eventPayload || eventPayload.type !== 'function_tools_executed') {
        continue;
      }

      const calls = eventPayload.function_calls ?? [];
      const outputs = eventPayload.function_call_outputs ?? [];

      outputs.forEach((output, index) => {
        if (!output || typeof output.output !== 'string') {
          return;
        }

        const actionResult = extractActionResult(output.output);
        if (!actionResult) {
          return;
        }

        const security = actionResult.data?.security_status;
        const personaMode =
          (typeof actionResult.data?.applied_persona_mode === 'string'
            ? actionResult.data.applied_persona_mode
            : undefined) ??
          (typeof actionResult.data?.current_persona_mode === 'string'
            ? actionResult.data.current_persona_mode
            : undefined) ??
          (typeof actionResult.data?.persona_mode === 'string'
            ? actionResult.data.persona_mode
            : undefined);
        const personaProfile = actionResult.data?.persona_profile;
        const activeCharacter = actionResult.data?.active_character;
        const activeCharacterCleared = actionResult.data?.active_character_cleared === true;

        if (security) {
          setSecuritySession({
            authenticated: Boolean(security.authenticated),
            identityBound: Boolean(security.identity_bound),
            expiresIn: Number(security.expires_in ?? 0),
            authMethod: typeof security.auth_method === 'string' ? security.auth_method : undefined,
            stepUpRequired: Boolean(security.step_up_required),
            voiceScore:
              typeof actionResult.data?.voice_score === 'number'
                ? actionResult.data.voice_score
                : undefined,
            personaMode,
            personaColorHex:
              typeof personaProfile?.color_hex === 'string' ? personaProfile.color_hex : undefined,
            personaLabel:
              typeof personaProfile?.label === 'string' ? personaProfile.label : undefined,
            activeCharacterName:
              typeof activeCharacter?.name === 'string' ? activeCharacter.name : undefined,
            activeCharacterSource:
              typeof activeCharacter?.source === 'string' ? activeCharacter.source : undefined,
            activeCharacterSummary:
              typeof activeCharacter?.summary === 'string' ? activeCharacter.summary : undefined,
          });
        } else if (personaMode || personaProfile || activeCharacter || activeCharacterCleared) {
          setSecuritySession((current) => ({
            ...current,
            personaMode: personaMode ?? current.personaMode,
            personaColorHex:
              typeof personaProfile?.color_hex === 'string'
                ? personaProfile.color_hex
                : current.personaColorHex,
            personaLabel:
              typeof personaProfile?.label === 'string'
                ? personaProfile.label
                : current.personaLabel,
            activeCharacterName: activeCharacterCleared
              ? undefined
              : typeof activeCharacter?.name === 'string'
                ? activeCharacter.name
                : current.activeCharacterName,
            activeCharacterSource: activeCharacterCleared
              ? undefined
              : typeof activeCharacter?.source === 'string'
                ? activeCharacter.source
                : current.activeCharacterSource,
            activeCharacterSummary: activeCharacterCleared
              ? undefined
              : typeof activeCharacter?.summary === 'string'
                ? activeCharacter.summary
                : current.activeCharacterSummary,
          }));
        }

        if (actionResult.data?.authentication_required) {
          if (actionResult.data.step_up_required) {
            toast.warning('Validacao por voz parcial. Confirme com PIN/frase para liberar sessao.');
          } else {
            toast.warning('Sessao privada bloqueada. Diga seu PIN/frase para autenticar.');
          }
        }

        const call = calls[index];
        const actionName = call?.name ?? output.name ?? 'action';
        const callId = call?.call_id ?? output.call_id ?? `${streamId}-${index}`;

        if (actionResult.data?.confirmation_required && actionResult.data.confirmation_token) {
          const confirmation: PendingActionConfirmation = {
            token: actionResult.data.confirmation_token,
            message: actionResult.message,
            expiresIn: actionResult.data.expires_in ?? 60,
            actionName: actionResult.data.action_name,
            params: actionResult.data.params,
          };
          setPendingConfirmation(confirmation);
          toast.warning(`Confirmacao necessaria: ${actionResult.message}`);
          pushEvent({
            callId,
            actionName,
            name: actionName,
            status: 'confirmation_required',
            timestamp: Date.now(),
            message: actionResult.message,
          });
          return;
        }

        const status = actionResult.success ? 'completed' : 'failed';
        if (actionResult.success) {
          toast.success(`Acao executada: ${actionResult.message}`);
        } else {
          toast.error(`Falha na acao: ${actionResult.error ?? actionResult.message}`);
        }

        pushEvent({
          callId,
          actionName,
          name: actionName,
          status,
          timestamp: Date.now(),
          message: actionResult.message,
        });
      });
    }
  }, [pushEvent, textStreams]);

  const confirmPendingAction = useCallback(async () => {
    if (!pendingConfirmation) {
      return;
    }

    setIsConfirming(true);
    try {
      await send(`Sim, confirmo a execucao. confirmation_token=${pendingConfirmation.token}`);
      toast.message('Confirmacao enviada para o agente.');
      setPendingConfirmation(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro ao enviar confirmacao.';
      toast.error(message);
    } finally {
      setIsConfirming(false);
    }
  }, [pendingConfirmation, send]);

  const cancelPendingAction = useCallback(() => {
    setPendingConfirmation(null);
    toast.message('Acao cancelada.');
  }, []);

  return {
    events,
    pendingConfirmation,
    isConfirming,
    securitySession,
    confirmPendingAction,
    cancelPendingAction,
  };
}
