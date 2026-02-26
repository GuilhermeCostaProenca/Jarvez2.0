import { useCallback, useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';
import { useChat, useTextStream } from '@livekit/components-react';
import type {
  ActionExecutionEvent,
  ActionResultPayload,
  PendingActionConfirmation,
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
    confirmPendingAction,
    cancelPendingAction,
  };
}
