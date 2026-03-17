import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { toast } from 'sonner';
import { useChat, useRoomContext, useTextStream, useVoiceAssistant } from '@livekit/components-react';
import {
  readStoredCodexTaskHistory,
  readStoredCodingHistory,
  writeStoredCodexTaskHistory,
  writeStoredCodingHistory,
} from '@/lib/coding-history-storage';
import {
  attachTraceToOpsCommand,
  readStoredAutoRemediation,
  readStoredAutomationState,
  readStoredBrowserTask,
  readStoredCanaryPromotion,
  readStoredCanaryState,
  readStoredControlTick,
  readStoredEvalBaselineSummary,
  readStoredEvalMetrics,
  readStoredEvalMetricsSummary,
  readStoredExecutionTraces,
  readStoredFeatureFlags,
  readStoredIncidentSnapshot,
  readStoredModelRoute,
  readStoredPlaybookReport,
  readStoredPolicyEvents,
  readStoredProvidersHealth,
  readStoredSloReport,
  readStoredSubagents,
  writeStoredAutoRemediation,
  writeStoredAutomationState,
  writeStoredBackendDomainTrustScores,
  writeStoredBrowserTask,
  writeStoredCanaryPromotion,
  writeStoredCanaryState,
  writeStoredControlTick,
  writeStoredEvalBaselineSummary,
  writeStoredEvalMetrics,
  writeStoredEvalMetricsSummary,
  writeStoredExecutionTraces,
  writeStoredFeatureFlags,
  writeStoredIncidentSnapshot,
  writeStoredModelRoute,
  writeStoredPlaybookReport,
  writeStoredPolicyEvents,
  writeStoredProvidersHealth,
  writeStoredSloReport,
  writeStoredSubagents,
  writeStoredWorkflowState,
  readStoredWorkflowState,
  writeStoredWhatsAppChannelStatus,
} from '@/lib/orchestration-storage';
import {
  readStoredResearchSchedules,
  writeStoredResearchDashboard,
  writeStoredResearchSchedules,
} from '@/lib/research-dashboard-storage';
import type {
  ActionEvidence,
  ActionExecutionEvent,
  ActionResultPayload,
  AutomationState,
  BrowserTaskState,
  CodexTaskEvent,
  CodexTaskHistoryEntry,
  CodexTaskState,
  CodingHistoryEntry,
  ExecutionTraceStep,
  ModelRouteDecision,
  PendingActionConfirmation,
  PolicyEvent,
  ResearchDashboard,
  ResearchSchedule,
  SecuritySessionState,
  SessionSnapshot,
  SubagentState,
  VoiceInteractivityState,
  VoiceInteractivityStateValue,
  WorkflowState,
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

interface CodexStreamEvent {
  type?: string;
  codex_task?: CodexTaskState | null;
  codex_event?: CodexTaskEvent | null;
  codex_history?: CodexTaskHistoryEntry[];
  browser_task?: BrowserTaskState | null;
  workflow_state?: WorkflowState | null;
  automation_state?: AutomationState | null;
  notice?: SecuritySessionState['autonomyNotice'];
  snapshot?: SessionSnapshot | null;
  voice_interactivity?: VoiceInteractivityState | null;
}

interface SpeechRecognitionAlternativeLike {
  transcript?: string;
}

interface SpeechRecognitionResultLike {
  isFinal?: boolean;
  length?: number;
  [index: number]: SpeechRecognitionAlternativeLike;
}

interface SpeechRecognitionEventLike extends Event {
  resultIndex?: number;
  results?: ArrayLike<SpeechRecognitionResultLike>;
}

interface SpeechRecognitionLike extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onend: ((event: Event) => void) | null;
  onerror: ((event: Event & { error?: string }) => void) | null;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  start: () => void;
  stop: () => void;
}

interface SpeechRecognitionConstructorLike {
  new (): SpeechRecognitionLike;
}

interface RecentInteractionEntry {
  id: string;
  title: string;
  status: ActionExecutionEvent['status'] | 'running';
  timestamp: number;
  message: string;
  retryable: boolean;
  actionName?: string;
  source: 'action' | 'background';
}

const ACTIVE_VOICE_STATES = new Set<VoiceInteractivityStateValue>([
  'listening',
  'transcribing',
  'thinking',
  'confirming',
  'executing',
  'background',
  'speaking',
]);

function formatActionLabel(actionName?: string): string {
  if (!actionName) {
    return 'ultima acao';
  }
  return actionName.replaceAll('_', ' ');
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

function normalizeCodexTask(task: unknown): CodexTaskState | null {
  if (!task || typeof task !== 'object') {
    return null;
  }
  return task as CodexTaskState;
}

function normalizeCodexEvent(event: unknown): CodexTaskEvent | null {
  if (!event || typeof event !== 'object') {
    return null;
  }
  return event as CodexTaskEvent;
}

function normalizeCodexHistory(history: unknown): CodexTaskHistoryEntry[] {
  if (!Array.isArray(history)) {
    return [];
  }
  return history.filter((item): item is CodexTaskHistoryEntry =>
    Boolean(item && typeof item === 'object')
  );
}

function normalizeSessionSnapshot(snapshot: unknown): SessionSnapshot | null {
  if (!snapshot || typeof snapshot !== "object") {
    return null;
  }
  return snapshot as SessionSnapshot;
}

function normalizeVoiceInteractivity(snapshot: unknown): VoiceInteractivityState | null {
  if (!snapshot || typeof snapshot !== 'object') {
    return null;
  }
  const payload = snapshot as VoiceInteractivityState;
  if (!payload.state || typeof payload.state !== 'string') {
    return null;
  }
  return payload;
}

function mapVoiceAssistantState(rawState: unknown): VoiceInteractivityStateValue {
  const value = String(rawState ?? '').trim().toLowerCase();
  if (!value || value === 'disconnected') {
    return 'idle';
  }
  if (value.includes('listen')) {
    return 'listening';
  }
  if (value.includes('transcrib')) {
    return 'transcribing';
  }
  if (value.includes('speak')) {
    return 'speaking';
  }
  if (value.includes('confirm')) {
    return 'confirming';
  }
  if (value.includes('execut')) {
    return 'executing';
  }
  if (value.includes('background')) {
    return 'background';
  }
  if (value.includes('error') || value.includes('fail')) {
    return 'error';
  }
  if (value.includes('think') || value.includes('process') || value.includes('connect')) {
    return 'thinking';
  }
  return 'idle';
}

export function useAgentActionEvents() {
  const { textStreams } = useTextStream('lk.agent.events');
  const { send } = useChat();
  const room = useRoomContext();
  const { state: voiceAssistantState } = useVoiceAssistant();

  const processedStreamIds = useRef<Set<string>>(new Set());
  const spokenAutonomyNoticeAt = useRef<Map<string, number>>(new Map());
  const reportedAutonomyNoticeDelivery = useRef<Set<string>>(new Set());
  const spokenVoiceCueAt = useRef<Map<string, number>>(new Map());
  const visualVoiceNoticeAt = useRef<Map<string, number>>(new Map());
  const lastPublishedVoiceState = useRef<string>('');
  const lastWakeWordAt = useRef<number>(0);
  const voiceInteractivityRef = useRef<VoiceInteractivityState | null>(null);
  const [pendingConfirmation, setPendingConfirmation] = useState<PendingActionConfirmation | null>(
    null
  );
  const [isConfirming, setIsConfirming] = useState(false);
  const [events, setEvents] = useState<ActionExecutionEvent[]>([]);
  const [latestResearchDashboard, setLatestResearchDashboard] = useState<ResearchDashboard | null>(
    null
  );
  const [researchSchedules, setResearchSchedules] = useState<ResearchSchedule[]>([]);
  const [latestModelRoute, setLatestModelRoute] = useState<ModelRouteDecision | null>(null);
  const [subagentStates, setSubagentStates] = useState<SubagentState[]>([]);
  const [policyEvents, setPolicyEvents] = useState<PolicyEvent[]>([]);
  const [executionTraces, setExecutionTraces] = useState<ExecutionTraceStep[]>([]);
  const [latestEvalBaselineSummary, setLatestEvalBaselineSummary] = useState<Record<
    string,
    unknown
  > | null>(null);
  const [evalMetrics, setEvalMetrics] = useState<Array<Record<string, unknown>>>([]);
  const [evalMetricsSummary, setEvalMetricsSummary] = useState<Record<string, unknown> | null>(
    null
  );
  const [sloReport, setSloReport] = useState<Record<string, unknown> | null>(null);
  const [providersHealth, setProvidersHealth] = useState<Array<Record<string, unknown>>>([]);
  const [featureFlags, setFeatureFlags] = useState<Record<string, unknown> | null>(null);
  const [canaryState, setCanaryState] = useState<Record<string, unknown> | null>(null);
  const [incidentSnapshot, setIncidentSnapshot] = useState<Record<string, unknown> | null>(null);
  const [playbookReport, setPlaybookReport] = useState<Record<string, unknown> | null>(null);
  const [autoRemediation, setAutoRemediation] = useState<Record<string, unknown> | null>(null);
  const [canaryPromotion, setCanaryPromotion] = useState<Record<string, unknown> | null>(null);
  const [controlTick, setControlTick] = useState<Record<string, unknown> | null>(null);
  const [latestWorkerStatus, setLatestWorkerStatus] = useState<{
    success: boolean;
    message: string;
  } | null>(null);
  const [latestProjectAnalysis, setLatestProjectAnalysis] = useState<
    NonNullable<ActionResultPayload['data']>['project_analysis'] | null
  >(null);
  const [latestProposedCodeChange, setLatestProposedCodeChange] = useState<
    NonNullable<ActionResultPayload['data']>['proposed_code_change'] | null
  >(null);
  const [latestCommandExecution, setLatestCommandExecution] = useState<
    NonNullable<ActionResultPayload['data']>['command_execution'] | null
  >(null);
  const [latestGitStatus, setLatestGitStatus] = useState<
    NonNullable<ActionResultPayload['data']>['git_status'] | null
  >(null);
  const [latestGitDiffSummary, setLatestGitDiffSummary] = useState<
    NonNullable<ActionResultPayload['data']>['git_diff_summary'] | null
  >(null);
  const [codingHistory, setCodingHistory] = useState<CodingHistoryEntry[]>([]);
  const [activeCodexTask, setActiveCodexTask] = useState<CodexTaskState | null>(null);
  const [codexTaskEvents, setCodexTaskEvents] = useState<CodexTaskEvent[]>([]);
  const [codexTaskHistory, setCodexTaskHistory] = useState<CodexTaskHistoryEntry[]>([]);
  const [browserTask, setBrowserTask] = useState<BrowserTaskState | null>(null);
  const [workflowState, setWorkflowState] = useState<WorkflowState | null>(null);
  const [automationState, setAutomationState] = useState<AutomationState | null>(null);
  const [voiceInteractivity, setVoiceInteractivity] = useState<VoiceInteractivityState | null>(null);
  const [pushToTalkActive, setPushToTalkActive] = useState(false);
  const [lastReplayableMessage, setLastReplayableMessage] = useState('');
  const [securitySession, setSecuritySession] = useState<SecuritySessionState>({
    authenticated: false,
    identityBound: false,
    expiresIn: 0,
    stepUpRequired: false,
    autonomyNotice: null,
  });

  useEffect(() => {
    setResearchSchedules(readStoredResearchSchedules());
    setCodingHistory(readStoredCodingHistory());
    setCodexTaskHistory(readStoredCodexTaskHistory());
    setLatestModelRoute(readStoredModelRoute());
    setSubagentStates(readStoredSubagents());
    setPolicyEvents(readStoredPolicyEvents());
    setExecutionTraces(readStoredExecutionTraces());
    setLatestEvalBaselineSummary(readStoredEvalBaselineSummary());
    setEvalMetrics(readStoredEvalMetrics());
    setEvalMetricsSummary(readStoredEvalMetricsSummary());
    setSloReport(readStoredSloReport());
    setProvidersHealth(readStoredProvidersHealth());
    setFeatureFlags(readStoredFeatureFlags());
    setCanaryState(readStoredCanaryState());
    setIncidentSnapshot(readStoredIncidentSnapshot());
    setPlaybookReport(readStoredPlaybookReport());
    setAutoRemediation(readStoredAutoRemediation());
    setCanaryPromotion(readStoredCanaryPromotion());
    setControlTick(readStoredControlTick());
    setBrowserTask(readStoredBrowserTask());
    setWorkflowState(readStoredWorkflowState());
    setAutomationState(readStoredAutomationState());
  }, []);

  useEffect(() => {
    voiceInteractivityRef.current = voiceInteractivity;
    if (
      voiceInteractivity?.spoken_message?.trim() ||
      voiceInteractivity?.display_message?.trim()
    ) {
      setLastReplayableMessage(
        voiceInteractivity.spoken_message?.trim() || voiceInteractivity.display_message?.trim() || ''
      );
    }
    if (
      pushToTalkActive &&
      voiceInteractivity?.state &&
      !['listening', 'transcribing', 'thinking'].includes(voiceInteractivity.state)
    ) {
      setPushToTalkActive(false);
    }
  }, [pushToTalkActive, voiceInteractivity]);

  const pushEvent = useCallback((event: ActionExecutionEvent) => {
    setEvents((current) => [event, ...current].slice(0, 12));
  }, []);

  const pushPolicyEvent = useCallback((event: PolicyEvent) => {
    setPolicyEvents((current) => {
      const next = [event, ...current].slice(0, 40);
      writeStoredPolicyEvents(next);
      return next;
    });
  }, []);

  const pushTraceStep = useCallback((trace: ExecutionTraceStep) => {
    setExecutionTraces((current) => {
      const next = [trace, ...current].slice(0, 120);
      writeStoredExecutionTraces(next);
      return next;
    });
  }, []);

  const pushCodingHistory = useCallback((entry: CodingHistoryEntry) => {
    setCodingHistory((current) => {
      const next = [entry, ...current].slice(0, 12);
      writeStoredCodingHistory(next);
      return next;
    });
  }, []);

  const pushCodexTaskEvent = useCallback((event: CodexTaskEvent) => {
    setCodexTaskEvents((current) => [event, ...current].slice(0, 20));
  }, []);

  const replaceCodexTaskHistory = useCallback((entries: CodexTaskHistoryEntry[]) => {
    setCodexTaskHistory(() => {
      const next = entries.slice(0, 12);
      writeStoredCodexTaskHistory(next);
      return next;
    });
  }, []);

  const upsertCodexTaskHistory = useCallback((entry: CodexTaskHistoryEntry) => {
    setCodexTaskHistory((current) => {
      const next = [entry, ...current.filter((item) => item.task_id !== entry.task_id)].slice(
        0,
        12
      );
      writeStoredCodexTaskHistory(next);
      return next;
    });
  }, []);

  const applyAutonomyNotice = useCallback(
    (notice: SecuritySessionState['autonomyNotice'], { speak }: { speak: boolean }) => {
      if (!notice || notice.active === false) {
        return;
      }

      setSecuritySession((current) => ({
        ...current,
        autonomyNotice: {
          active: notice.active !== false,
          level: notice.level,
          title: notice.title,
          message: notice.message,
          domain: notice.domain,
          scenario: notice.scenario,
          decision: notice.decision,
          signature: notice.signature,
          spoken_message: notice.spoken_message,
          spoken_channel: notice.spoken_channel,
          trace_id: notice.trace_id,
        },
      }));

      const noticeMessage = notice.message ?? 'Autonomia reduzida temporariamente.';
      if (notice.level === 'critical') {
        toast.error(noticeMessage);
      } else if (notice.level === 'warning') {
        toast.warning(noticeMessage);
      } else {
        toast.message(noticeMessage);
      }

      if (
        !speak ||
        (notice.level !== 'warning' && notice.level !== 'critical') ||
        notice.spoken_channel === 'agent_audio' ||
        typeof window === 'undefined' ||
        !('speechSynthesis' in window)
      ) {
        return;
      }

      const signature =
        notice.signature ??
        `${notice.scenario ?? 'notice'}:${notice.domain ?? 'general'}:${notice.decision ?? 'unknown'}`;
      const now = Date.now();
      const lastSpokenAt = spokenAutonomyNoticeAt.current.get(signature) ?? 0;
      if (now - lastSpokenAt < 15_000) {
        return;
      }
      spokenAutonomyNoticeAt.current.set(signature, now);
      if (spokenAutonomyNoticeAt.current.size > 40) {
        for (const [key, value] of spokenAutonomyNoticeAt.current.entries()) {
          if (now - value > 60_000) {
            spokenAutonomyNoticeAt.current.delete(key);
          }
        }
      }

      const utterance = new SpeechSynthesisUtterance(
        notice.spoken_message ??
          `Atencao. Reduzi a autonomia no dominio ${notice.domain ?? 'general'}.`
      );
      utterance.lang = 'pt-BR';
      utterance.rate = 1;
      utterance.pitch = 1;

      try {
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
        setSecuritySession((current) => ({
          ...current,
          autonomyNotice: current.autonomyNotice
            ? {
                ...current.autonomyNotice,
                spoken_channel: 'browser_tts',
              }
            : current.autonomyNotice,
        }));
        const telemetryKey =
          notice.trace_id ??
          notice.signature ??
          `${notice.scenario ?? 'notice'}:${notice.domain ?? 'general'}:${notice.decision ?? 'unknown'}`;
        if (!reportedAutonomyNoticeDelivery.current.has(telemetryKey)) {
          reportedAutonomyNoticeDelivery.current.add(telemetryKey);
          const payload = new TextEncoder().encode(
            JSON.stringify({
              type: 'autonomy_notice_delivery',
              trace_id: notice.trace_id,
              signature: notice.signature,
              channel: 'browser_tts',
              level: notice.level,
              domain: notice.domain,
              scenario: notice.scenario,
            })
          );
          void room.localParticipant
            .publishData(payload, {
              reliable: true,
              topic: 'jarvez.client.telemetry',
            })
            .catch(() => {
              reportedAutonomyNoticeDelivery.current.delete(telemetryKey);
            });
        }
      } catch {
        // Ignore browser speech synthesis failures; the visual notice remains available.
      }
    },
    [room]
  );

  const publishClientVoiceState = useCallback(
    (payload: {
      state: VoiceInteractivityStateValue;
      activationMode?: string;
      rawClientState?: string;
      displayMessage?: string;
      spokenMessage?: string;
      errorCode?: string;
      canRetry?: boolean;
      wakeWordAvailable?: boolean;
    }) => {
      const serialized = JSON.stringify({
        state: payload.state,
        activationMode: payload.activationMode ?? '',
        rawClientState: payload.rawClientState ?? '',
        displayMessage: payload.displayMessage ?? '',
        spokenMessage: payload.spokenMessage ?? '',
        errorCode: payload.errorCode ?? '',
        canRetry: payload.canRetry ?? false,
        wakeWordAvailable: payload.wakeWordAvailable ?? false,
      });
      if (lastPublishedVoiceState.current === serialized) {
        return;
      }
      if (!room.localParticipant) {
        return;
      }
      lastPublishedVoiceState.current = serialized;
      const telemetry = new TextEncoder().encode(
        JSON.stringify({
          type: 'voice_interactivity_client',
          state: payload.state,
          activation_mode: payload.activationMode,
          raw_client_state: payload.rawClientState,
          display_message: payload.displayMessage,
          spoken_message: payload.spokenMessage,
          error_code: payload.errorCode,
          can_retry: payload.canRetry,
          wake_word_available: payload.wakeWordAvailable,
        })
      );
      void room.localParticipant.publishData(telemetry, {
        reliable: true,
        topic: 'jarvez.client.telemetry',
      });
    },
    [room]
  );

  const setClientVoiceInteractivity = useCallback(
    (payload: {
      state: VoiceInteractivityStateValue;
      activationMode?: string;
      rawClientState?: string;
      displayMessage?: string;
      spokenMessage?: string;
      errorCode?: string;
      canRetry?: boolean;
      wakeWordAvailable?: boolean;
    }) => {
      const nextState: VoiceInteractivityState = {
        state: payload.state,
        source: 'client',
        activation_mode: payload.activationMode,
        raw_client_state: payload.rawClientState,
        display_message: payload.displayMessage,
        spoken_message: payload.spokenMessage,
        error_code: payload.errorCode,
        can_retry: payload.canRetry,
        wake_word_available:
          payload.wakeWordAvailable ?? voiceInteractivityRef.current?.wake_word_available,
        updated_at: new Date().toISOString(),
      };
      setVoiceInteractivity(nextState);
      publishClientVoiceState(payload);
    },
    [publishClientVoiceState]
  );

  const speakReplayText = useCallback(
    (text: string) => {
      if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
        toast.message('Repeticao de audio indisponivel neste navegador.');
        return;
      }

      const activationMode = voiceInteractivityRef.current?.activation_mode ?? 'button';
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'pt-BR';
      utterance.rate = 1.04;
      utterance.pitch = 1.01;
      utterance.onstart = () => {
        setClientVoiceInteractivity({
          state: 'speaking',
          activationMode,
          rawClientState: 'gesture_repeat_start',
          displayMessage: 'Repetindo a ultima resposta.',
          spokenMessage: text,
        });
      };
      utterance.onend = () => {
        setClientVoiceInteractivity({
          state: 'idle',
          activationMode,
          rawClientState: 'gesture_repeat_end',
          displayMessage: 'Pronto.',
        });
      };
      utterance.onerror = () => {
        setClientVoiceInteractivity({
          state: 'error',
          activationMode,
          rawClientState: 'gesture_repeat_error',
          displayMessage: 'Nao consegui repetir a ultima resposta.',
          errorCode: 'repeat_audio_error',
          canRetry: true,
        });
      };

      try {
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
      } catch {
        toast.error('Nao consegui repetir a ultima resposta.');
      }
    },
    [setClientVoiceInteractivity]
  );

  useEffect(() => {
    const mappedState = mapVoiceAssistantState(voiceAssistantState);
    publishClientVoiceState({
      state: mappedState,
      activationMode: 'voice',
      rawClientState: String(voiceAssistantState ?? ''),
      displayMessage:
        mappedState === 'idle'
          ? 'Pronto para ouvir.'
          : mappedState === 'listening'
            ? 'Ouvindo.'
            : mappedState === 'transcribing'
              ? 'Transcrevendo.'
              : mappedState === 'thinking'
                ? 'Pensando.'
                : mappedState === 'speaking'
                  ? 'Falando.'
                  : undefined,
    });
  }, [publishClientVoiceState, voiceAssistantState]);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const activateListening = (mode?: string) => {
      const activationMode =
        mode === 'wake_word'
          ? 'wake_word'
          : mode === 'push_to_talk'
            ? 'push_to_talk'
            : 'button';
      if (activationMode === 'push_to_talk') {
        setPushToTalkActive(true);
      }
      setClientVoiceInteractivity({
        state: 'listening',
        activationMode,
        rawClientState:
          activationMode === 'push_to_talk' ? 'push_to_talk_start' : 'manual_activation',
        displayMessage:
          activationMode === 'wake_word'
            ? 'Wake word detectado.'
            : activationMode === 'push_to_talk'
              ? 'Segure e fale.'
              : 'Escuta ativada.',
      });
    };

    const deactivateListening = (mode?: string) => {
      const activationMode = mode === 'push_to_talk' ? 'push_to_talk' : 'button';
      if (activationMode === 'push_to_talk') {
        setPushToTalkActive(false);
      }
      setClientVoiceInteractivity({
        state: activationMode === 'push_to_talk' ? 'transcribing' : 'idle',
        activationMode,
        rawClientState:
          activationMode === 'push_to_talk' ? 'push_to_talk_release' : 'manual_deactivation',
        displayMessage:
          activationMode === 'push_to_talk' ? 'Processando sua fala.' : 'Escuta pausada.',
      });
    };

    const handleActivation = (event: Event) => {
      const customEvent = event as CustomEvent<{ mode?: string }>;
      activateListening(customEvent.detail?.mode);
    };

    const handleDeactivation = (event: Event) => {
      const customEvent = event as CustomEvent<{ mode?: string }>;
      deactivateListening(customEvent.detail?.mode);
    };

    const handleToggle = (event: Event) => {
      const customEvent = event as CustomEvent<{ mode?: string }>;
      const currentState =
        voiceInteractivityRef.current?.state ?? mapVoiceAssistantState(voiceAssistantState);
      if (ACTIVE_VOICE_STATES.has(currentState)) {
        deactivateListening(customEvent.detail?.mode);
        return;
      }
      activateListening(customEvent.detail?.mode);
    };

    window.addEventListener('jarvez:voice-activation', handleActivation as EventListener);
    window.addEventListener('jarvez:voice-deactivation', handleDeactivation as EventListener);
    window.addEventListener('jarvez:voice-toggle', handleToggle as EventListener);
    return () => {
      window.removeEventListener('jarvez:voice-activation', handleActivation as EventListener);
      window.removeEventListener('jarvez:voice-deactivation', handleDeactivation as EventListener);
      window.removeEventListener('jarvez:voice-toggle', handleToggle as EventListener);
    };
  }, [setClientVoiceInteractivity, voiceAssistantState]);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const recognitionCtor = (
      window as Window & {
        SpeechRecognition?: SpeechRecognitionConstructorLike;
        webkitSpeechRecognition?: SpeechRecognitionConstructorLike;
      }
    ).SpeechRecognition ??
      (
        window as Window & {
          webkitSpeechRecognition?: SpeechRecognitionConstructorLike;
        }
      ).webkitSpeechRecognition;

    if (!recognitionCtor) {
      publishClientVoiceState({
        state: mapVoiceAssistantState(voiceAssistantState),
        activationMode: 'button',
        rawClientState: String(voiceAssistantState ?? ''),
        displayMessage: 'Wake word indisponivel neste navegador.',
        wakeWordAvailable: false,
      });
      return;
    }

    let disposed = false;
    let recognition: SpeechRecognitionLike | null = null;

    try {
      recognition = new recognitionCtor();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'pt-BR';
      recognition.onresult = (event) => {
        const results = event.results;
        if (!results) {
          return;
        }
        let transcript = '';
        for (let i = event.resultIndex ?? 0; i < results.length; i += 1) {
          const result = results[i];
          const alternative = result?.[0];
          if (alternative?.transcript) {
            transcript += ` ${alternative.transcript}`;
          }
        }
        const normalized = transcript.trim().toLowerCase();
        if (!normalized || (!normalized.includes('jarvis') && !normalized.includes('jarvez'))) {
          return;
        }
        const now = Date.now();
        if (now - lastWakeWordAt.current < 8_000) {
          return;
        }
        lastWakeWordAt.current = now;
        window.dispatchEvent(
          new CustomEvent('jarvez:voice-activation', {
            detail: { mode: 'wake_word' },
          })
        );
      };
      recognition.onerror = () => {
        publishClientVoiceState({
          state: mapVoiceAssistantState(voiceAssistantState),
          activationMode: 'button',
          rawClientState: 'wake_word_error',
          displayMessage: 'Wake word indisponivel; use o botao.',
          wakeWordAvailable: false,
        });
      };
      recognition.onend = () => {
        if (disposed) {
          return;
        }
        try {
          recognition?.start();
        } catch {
          publishClientVoiceState({
            state: mapVoiceAssistantState(voiceAssistantState),
            activationMode: 'button',
            rawClientState: 'wake_word_restart_failed',
            displayMessage: 'Wake word indisponivel; use o botao.',
            wakeWordAvailable: false,
          });
        }
      };
      recognition.start();
      publishClientVoiceState({
        state: mapVoiceAssistantState(voiceAssistantState),
        activationMode: 'button',
        rawClientState: 'wake_word_ready',
        displayMessage: 'Wake word pronta.',
        wakeWordAvailable: true,
      });
    } catch {
      publishClientVoiceState({
        state: mapVoiceAssistantState(voiceAssistantState),
        activationMode: 'button',
        rawClientState: 'wake_word_unavailable',
        displayMessage: 'Wake word indisponivel; use o botao.',
        wakeWordAvailable: false,
      });
    }

    return () => {
      disposed = true;
      try {
        recognition?.stop();
      } catch {
        // ignore cleanup failures
      }
    };
  }, [publishClientVoiceState, voiceAssistantState]);

  const applyVoiceInteractivity = useCallback(
    (
      nextState: VoiceInteractivityState | null,
      {
        speak,
      }: {
        speak: boolean;
      } = { speak: false }
    ) => {
      if (!nextState) {
        return;
      }
      setVoiceInteractivity(nextState);

      if (nextState.source === 'backend') {
        const dedupeKey =
          nextState.trace_id ??
          `${nextState.state}:${nextState.action_name ?? 'voice'}:${nextState.updated_at ?? nextState.display_message ?? ''}`;
        const now = Date.now();
        const lastVisualNoticeAt = visualVoiceNoticeAt.current.get(dedupeKey) ?? 0;
        if (now - lastVisualNoticeAt > 4_000) {
          visualVoiceNoticeAt.current.set(dedupeKey, now);
          if (visualVoiceNoticeAt.current.size > 80) {
            for (const [key, value] of visualVoiceNoticeAt.current.entries()) {
              if (now - value > 45_000) {
                visualVoiceNoticeAt.current.delete(key);
              }
            }
          }

          if (nextState.state === 'error') {
            toast.error(nextState.display_message ?? 'Nao consegui concluir a acao.', {
              description: nextState.can_retry
                ? 'Voce pode tentar de novo ou escolher outra abordagem.'
                : undefined,
            });
          } else if (nextState.state === 'background') {
            toast.message(nextState.display_message ?? 'Tarefa em segundo plano.', {
              description: nextState.action_name
                ? `Acompanhando ${nextState.action_name.replaceAll('_', ' ')}.`
                : 'O Jarvez continua executando isso sem bloquear a conversa.',
            });
          }
        }
      }

      if (
        !speak ||
        !nextState.spoken_message ||
        nextState.source !== 'backend' ||
        typeof window === 'undefined' ||
        !('speechSynthesis' in window)
      ) {
        return;
      }

      const dedupeKey =
        nextState.trace_id ??
        `${nextState.state}:${nextState.action_name ?? 'voice'}:${nextState.spoken_message}`;
      const now = Date.now();
      const lastSpokenAt = spokenVoiceCueAt.current.get(dedupeKey) ?? 0;
      if (now - lastSpokenAt < 3_000) {
        return;
      }
      spokenVoiceCueAt.current.set(dedupeKey, now);

      const utterance = new SpeechSynthesisUtterance(nextState.spoken_message);
      utterance.lang = 'pt-BR';
      utterance.rate = 1.08;
      utterance.pitch = 1.02;
      utterance.onstart = () => {
        publishClientVoiceState({
          state: 'speaking',
          activationMode: nextState.activation_mode,
          rawClientState: 'browser_tts',
          displayMessage: nextState.display_message ?? nextState.spoken_message,
        });
      };
      utterance.onend = () => {
        publishClientVoiceState({
          state: 'idle',
          activationMode: nextState.activation_mode,
          rawClientState: 'browser_tts_complete',
          displayMessage: 'Pronto.',
        });
      };
      utterance.onerror = () => {
        publishClientVoiceState({
          state: 'error',
          activationMode: nextState.activation_mode,
          rawClientState: 'browser_tts_error',
          displayMessage: nextState.display_message ?? nextState.spoken_message,
          errorCode: 'browser_tts_error',
          canRetry: true,
        });
      };

      try {
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
      } catch {
        // Mantem o feedback visual mesmo quando TTS do browser falha.
      }
    },
    [publishClientVoiceState]
  );

  const hydrateSessionSnapshot = useCallback(
    (snapshot: SessionSnapshot) => {
      const securityPayload = snapshot.security_session;
      const securityStatus = securityPayload?.security_status;
      const personaProfile = securityPayload?.persona_profile;
      const activeCharacter = securityPayload?.active_character;
      const activeProject = securityPayload?.active_project;

      if (securityStatus || securityPayload) {
        setSecuritySession((current) => ({
          ...current,
          authenticated: Boolean(securityStatus?.authenticated),
          identityBound: Boolean(securityStatus?.identity_bound),
          expiresIn: Number(securityStatus?.expires_in ?? 0),
          authMethod:
            typeof securityStatus?.auth_method === 'string' ? securityStatus.auth_method : undefined,
          stepUpRequired: Boolean(securityStatus?.step_up_required),
          personaMode:
            typeof securityPayload?.persona_mode === 'string'
              ? securityPayload.persona_mode
              : current.personaMode,
          personaColorHex:
            typeof personaProfile?.color_hex === 'string'
              ? personaProfile.color_hex
              : current.personaColorHex,
          personaLabel:
            typeof personaProfile?.label === 'string' ? personaProfile.label : current.personaLabel,
          activeCharacterName:
            typeof activeCharacter?.name === 'string' ? activeCharacter.name : undefined,
          activeCharacterSource:
            typeof activeCharacter?.source === 'string' ? activeCharacter.source : undefined,
          activeCharacterSummary:
            typeof activeCharacter?.summary === 'string' ? activeCharacter.summary : undefined,
          activeProjectId:
            typeof activeProject?.project_id === 'string' ? activeProject.project_id : undefined,
          activeProjectName:
            typeof activeProject?.name === 'string' ? activeProject.name : undefined,
          activeProjectRootPath:
            typeof activeProject?.root_path === 'string' ? activeProject.root_path : undefined,
          activeProjectIndexStatus:
            typeof activeProject?.index_status === 'string' ? activeProject.index_status : undefined,
          codingMode:
            typeof securityPayload?.coding_mode === 'string'
              ? securityPayload.coding_mode
              : current.codingMode,
        }));
      }

      if (Array.isArray(snapshot.research_schedules)) {
        const nextSchedules = snapshot.research_schedules
          .map((item) => ({
            id: typeof item.id === 'string' ? item.id : '',
            query: typeof item.query === 'string' ? item.query : '',
            cadence: typeof item.cadence === 'string' ? item.cadence : 'daily',
            timeOfDay: typeof item.time_of_day === 'string' ? item.time_of_day : '08:00',
            prompt: typeof item.prompt === 'string' ? item.prompt : '',
            lastRunOn: typeof item.last_run_on === 'string' ? item.last_run_on : undefined,
          }))
          .filter((item) => item.id && item.query && item.prompt);
        setResearchSchedules(nextSchedules);
        writeStoredResearchSchedules(nextSchedules);
      }
      if (snapshot.model_route && typeof snapshot.model_route === 'object') {
        setLatestModelRoute(snapshot.model_route);
        writeStoredModelRoute(snapshot.model_route);
      }
      if (Array.isArray(snapshot.subagent_states)) {
        setSubagentStates(snapshot.subagent_states);
        writeStoredSubagents(snapshot.subagent_states);
      }
      if (Array.isArray(snapshot.policy_events)) {
        setPolicyEvents(snapshot.policy_events);
        writeStoredPolicyEvents(snapshot.policy_events);
      }
      if (Array.isArray(snapshot.execution_traces)) {
        setExecutionTraces(snapshot.execution_traces);
        writeStoredExecutionTraces(snapshot.execution_traces);
      }
      if (snapshot.eval_baseline_summary && typeof snapshot.eval_baseline_summary === 'object') {
        setLatestEvalBaselineSummary(snapshot.eval_baseline_summary);
        writeStoredEvalBaselineSummary(snapshot.eval_baseline_summary);
      }
      if (Array.isArray(snapshot.eval_metrics)) {
        setEvalMetrics(snapshot.eval_metrics);
        writeStoredEvalMetrics(snapshot.eval_metrics);
      }
      if (snapshot.eval_metrics_summary && typeof snapshot.eval_metrics_summary === 'object') {
        setEvalMetricsSummary(snapshot.eval_metrics_summary);
        writeStoredEvalMetricsSummary(snapshot.eval_metrics_summary);
      }
      if (snapshot.slo_report && typeof snapshot.slo_report === 'object') {
        setSloReport(snapshot.slo_report);
        writeStoredSloReport(snapshot.slo_report);
      }
      if (Array.isArray(snapshot.providers_health)) {
        setProvidersHealth(snapshot.providers_health);
        writeStoredProvidersHealth(snapshot.providers_health);
      }
      if (snapshot.feature_flags && typeof snapshot.feature_flags === 'object') {
        setFeatureFlags(snapshot.feature_flags);
        writeStoredFeatureFlags(snapshot.feature_flags);
      }
      if (snapshot.canary_state && typeof snapshot.canary_state === 'object') {
        setCanaryState(snapshot.canary_state as Record<string, unknown>);
        writeStoredCanaryState(snapshot.canary_state as Record<string, unknown>);
      }
      if (snapshot.incident_snapshot && typeof snapshot.incident_snapshot === 'object') {
        setIncidentSnapshot(snapshot.incident_snapshot as Record<string, unknown>);
        writeStoredIncidentSnapshot(snapshot.incident_snapshot as Record<string, unknown>);
      }
      if (snapshot.playbook_report && typeof snapshot.playbook_report === 'object') {
        setPlaybookReport(snapshot.playbook_report as Record<string, unknown>);
        writeStoredPlaybookReport(snapshot.playbook_report as Record<string, unknown>);
      }
      if (snapshot.auto_remediation && typeof snapshot.auto_remediation === 'object') {
        setAutoRemediation(snapshot.auto_remediation as Record<string, unknown>);
        writeStoredAutoRemediation(snapshot.auto_remediation as Record<string, unknown>);
      }
      if (snapshot.canary_promotion && typeof snapshot.canary_promotion === 'object') {
        setCanaryPromotion(snapshot.canary_promotion as Record<string, unknown>);
        writeStoredCanaryPromotion(snapshot.canary_promotion as Record<string, unknown>);
      }
      if (snapshot.control_tick && typeof snapshot.control_tick === 'object') {
        setControlTick(snapshot.control_tick as Record<string, unknown>);
        writeStoredControlTick(snapshot.control_tick as Record<string, unknown>);
      }
      if (snapshot.active_codex_task && typeof snapshot.active_codex_task === 'object') {
        setActiveCodexTask(snapshot.active_codex_task);
      }
      if (Array.isArray(snapshot.codex_history)) {
        replaceCodexTaskHistory(snapshot.codex_history);
      }
      if (snapshot.browser_tasks) {
        if (Array.isArray(snapshot.browser_tasks)) {
          const latest = snapshot.browser_tasks[0] ?? null;
          setBrowserTask(latest);
          writeStoredBrowserTask(latest);
        } else {
          setBrowserTask(snapshot.browser_tasks);
          writeStoredBrowserTask(snapshot.browser_tasks);
        }
      }
      if (snapshot.workflow_state && typeof snapshot.workflow_state === 'object') {
        setWorkflowState(snapshot.workflow_state);
        writeStoredWorkflowState(snapshot.workflow_state);
      }
      if (snapshot.automation_state && typeof snapshot.automation_state === 'object') {
        setAutomationState(snapshot.automation_state);
        writeStoredAutomationState(snapshot.automation_state);
      }
      if (snapshot.whatsapp_channel && typeof snapshot.whatsapp_channel === 'object') {
        writeStoredWhatsAppChannelStatus(snapshot.whatsapp_channel as Record<string, unknown>);
      }
      if (snapshot.voice_interactivity) {
        applyVoiceInteractivity(snapshot.voice_interactivity, { speak: false });
      }
    },
    [applyVoiceInteractivity, replaceCodexTaskHistory]
  );

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

      const genericPayload = safeParseJson<CodexStreamEvent | FunctionToolsExecutedEvent>(
        stream.text
      );
      if (!genericPayload || typeof genericPayload !== 'object') {
        continue;
      }

      if (
        genericPayload.type === 'codex_task_started' ||
        genericPayload.type === 'codex_task_progress' ||
        genericPayload.type === 'codex_task_completed' ||
        genericPayload.type === 'codex_task_failed' ||
        genericPayload.type === 'codex_task_cancelled'
      ) {
        const codexTask = normalizeCodexTask((genericPayload as CodexStreamEvent).codex_task);
        const codexEvent = normalizeCodexEvent((genericPayload as CodexStreamEvent).codex_event);
        const codexHistoryItems = normalizeCodexHistory(
          (genericPayload as CodexStreamEvent).codex_history
        );

        if (codexTask) {
          setActiveCodexTask(codexTask);
          if (
            codexTask.status === 'completed' ||
            codexTask.status === 'failed' ||
            codexTask.status === 'cancelled'
          ) {
            upsertCodexTaskHistory(codexTask);
          }
        }
        if (codexEvent) {
          if (genericPayload.type === 'codex_task_started') {
            setCodexTaskEvents([codexEvent]);
          } else {
            pushCodexTaskEvent(codexEvent);
          }
        }
        if (codexHistoryItems.length) {
          replaceCodexTaskHistory(codexHistoryItems);
        }
        continue;
      }

      if (
        genericPayload.type === 'browser_task_started' ||
        genericPayload.type === 'browser_task_progress' ||
        genericPayload.type === 'browser_task_completed' ||
        genericPayload.type === 'browser_task_failed'
      ) {
        const browserTaskPayload = (genericPayload as CodexStreamEvent).browser_task;
        if (browserTaskPayload && typeof browserTaskPayload === 'object') {
          const nextTask = browserTaskPayload as BrowserTaskState;
          setBrowserTask(nextTask);
          writeStoredBrowserTask(nextTask);
        }
        continue;
      }

      if (
        genericPayload.type === 'workflow_started' ||
        genericPayload.type === 'workflow_progress' ||
        genericPayload.type === 'workflow_completed' ||
        genericPayload.type === 'workflow_failed'
      ) {
        const workflowPayload = (genericPayload as CodexStreamEvent).workflow_state;
        if (workflowPayload && typeof workflowPayload === 'object') {
          setWorkflowState(workflowPayload as WorkflowState);
          writeStoredWorkflowState(workflowPayload as WorkflowState);
        }
        continue;
      }

      if (genericPayload.type === 'voice_interactivity_state') {
        const voiceInteractivityPayload = normalizeVoiceInteractivity(
          (genericPayload as CodexStreamEvent).voice_interactivity
        );
        if (voiceInteractivityPayload) {
          applyVoiceInteractivity(voiceInteractivityPayload, { speak: true });
        }
        continue;
      }

      if (genericPayload.type === 'autonomy_notice') {
        applyAutonomyNotice((genericPayload as CodexStreamEvent).notice ?? null, { speak: true });
        continue;
      }

      if (genericPayload.type === 'session_snapshot') {
        const snapshot = normalizeSessionSnapshot((genericPayload as CodexStreamEvent).snapshot);
        if (snapshot) {
          hydrateSessionSnapshot(snapshot);
        }
        continue;
      }

      const eventPayload = genericPayload as FunctionToolsExecutedEvent;
      if (eventPayload.type !== 'function_tools_executed') {
        continue;
      }

      const calls = eventPayload.function_calls ?? [];
      const outputs = eventPayload.function_call_outputs ?? [];

      calls.forEach((call, index) => {
        const actionName = call?.name ?? `action_${index + 1}`;
        pushEvent({
          callId: call?.call_id ?? `${streamId}-start-${index}`,
          actionName,
          name: actionName,
          status: 'started',
          timestamp: Date.now(),
          message: `Executando ${actionName}...`,
        });
      });

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
        const activeProject = actionResult.data?.active_project;
        const codingMode =
          typeof actionResult.data?.coding_mode === 'string'
            ? actionResult.data.coding_mode
            : undefined;
        const workerStatus = actionResult.data?.worker_status;
        const projectAnalysis = actionResult.data?.project_analysis;
        const proposedCodeChange = actionResult.data?.proposed_code_change;
        const commandExecution = actionResult.data?.command_execution;
        const gitStatus = actionResult.data?.git_status;
        const gitDiffSummary = actionResult.data?.git_diff_summary;
        const webDashboard = actionResult.data?.web_dashboard;
        const webDashboardSchedule = actionResult.data?.web_dashboard_schedule;
        const modelRoute = actionResult.data?.model_route;
        const subagentState = actionResult.data?.subagent_state;
        const subagentStatesPayload = actionResult.data?.subagent_states;
        const policyPayload = actionResult.data?.policy;
        const autonomyNoticePayload = actionResult.data?.autonomy_notice;
        const evalBaselineSummary = actionResult.data?.eval_baseline_summary;
        const evalMetricsPayload = actionResult.data?.eval_metrics;
        const evalMetricsSummaryPayload = actionResult.data?.eval_metrics_summary;
        const sloReportPayload = actionResult.data?.slo_report;
        const providersHealthPayload = actionResult.data?.providers_health;
        const domainTrustPayload = actionResult.data?.domain_trust;
        const featureFlagsPayload = actionResult.data?.feature_flags;
        const canaryStatePayload = actionResult.data?.canary_state;
        const incidentSnapshotPayload = actionResult.data?.ops_incident_snapshot;
        const playbookReportPayload = actionResult.data?.ops_playbook_report;
        const autoRemediationPayload = actionResult.data?.ops_auto_remediation;
        const canaryPromotionPayload = actionResult.data?.ops_canary_promotion;
        const controlTickPayload = actionResult.data?.ops_control_tick;
        const browserTaskPayload = actionResult.data?.browser_task;
        const workflowStatePayload = actionResult.data?.workflow_state;
        const automationStatePayload = actionResult.data?.automation_state;
        const whatsappChannelPayload = actionResult.data?.whatsapp_channel;
        const evidence = actionResult.evidence as ActionEvidence | undefined;
        const codexTask = normalizeCodexTask(actionResult.data?.codex_task);
        const codexHistoryItems = normalizeCodexHistory(actionResult.data?.codex_history);

        if (workerStatus?.message) {
          setLatestWorkerStatus({
            success: workerStatus.success !== false,
            message: workerStatus.message,
          });
        }
        if (projectAnalysis) {
          setLatestProjectAnalysis(projectAnalysis);
        }
        if (proposedCodeChange) {
          setLatestProposedCodeChange(proposedCodeChange);
        }
        if (commandExecution) {
          setLatestCommandExecution(commandExecution);
        }
        if (gitStatus) {
          setLatestGitStatus(gitStatus);
        }
        if (gitDiffSummary) {
          setLatestGitDiffSummary(gitDiffSummary);
        }
        if (codexTask) {
          setActiveCodexTask(codexTask);
          if (
            codexTask.status === 'completed' ||
            codexTask.status === 'failed' ||
            codexTask.status === 'cancelled'
          ) {
            upsertCodexTaskHistory(codexTask);
          }
        }
        if (codexHistoryItems.length) {
          replaceCodexTaskHistory(codexHistoryItems);
        }
        if (modelRoute) {
          setLatestModelRoute(modelRoute);
          writeStoredModelRoute(modelRoute);
        }
        if (Array.isArray(subagentStatesPayload)) {
          setSubagentStates(subagentStatesPayload);
          writeStoredSubagents(subagentStatesPayload);
        } else if (subagentState && subagentState.subagent_id) {
          setSubagentStates((current) => {
            const next = [
              subagentState,
              ...current.filter((item) => item.subagent_id !== subagentState.subagent_id),
            ].slice(0, 40);
            writeStoredSubagents(next);
            return next;
          });
        }
        if (policyPayload) {
          pushPolicyEvent(policyPayload);
        } else if (actionResult.policy_decision || actionResult.risk) {
          const traceActionName = calls[index]?.name ?? output.name ?? 'action';
          pushPolicyEvent({
            action_name: traceActionName,
            risk: actionResult.risk,
            decision: actionResult.policy_decision,
            reason: undefined,
          });
        }
        if (autonomyNoticePayload && autonomyNoticePayload.active !== false) {
          applyAutonomyNotice(autonomyNoticePayload, { speak: false });
        } else if (
          policyPayload &&
          typeof policyPayload === 'object' &&
          policyPayload.trust_drift_active === false
        ) {
          setSecuritySession((current) => ({
            ...current,
            autonomyNotice: null,
          }));
        }
        if (evalBaselineSummary && typeof evalBaselineSummary === 'object') {
          setLatestEvalBaselineSummary(evalBaselineSummary as Record<string, unknown>);
          writeStoredEvalBaselineSummary(evalBaselineSummary as Record<string, unknown>);
        }
        if (Array.isArray(evalMetricsPayload)) {
          const nextMetrics = evalMetricsPayload.filter((item): item is Record<string, unknown> =>
            Boolean(item && typeof item === 'object')
          );
          setEvalMetrics(nextMetrics);
          writeStoredEvalMetrics(nextMetrics);
        }
        if (evalMetricsSummaryPayload && typeof evalMetricsSummaryPayload === 'object') {
          setEvalMetricsSummary(evalMetricsSummaryPayload as Record<string, unknown>);
          writeStoredEvalMetricsSummary(evalMetricsSummaryPayload as Record<string, unknown>);
        }
        if (sloReportPayload && typeof sloReportPayload === 'object') {
          setSloReport(sloReportPayload as Record<string, unknown>);
          writeStoredSloReport(sloReportPayload as Record<string, unknown>);
        }
        if (Array.isArray(providersHealthPayload)) {
          const rows = providersHealthPayload.filter((item): item is Record<string, unknown> =>
            Boolean(item && typeof item === 'object')
          );
          setProvidersHealth(rows);
          writeStoredProvidersHealth(rows);
        }
        if (Array.isArray(domainTrustPayload)) {
          writeStoredBackendDomainTrustScores(
            domainTrustPayload.filter((item): item is Record<string, unknown> =>
              Boolean(item && typeof item === 'object')
            )
          );
        }
        if (featureFlagsPayload && typeof featureFlagsPayload === 'object') {
          setFeatureFlags(featureFlagsPayload as Record<string, unknown>);
          writeStoredFeatureFlags(featureFlagsPayload as Record<string, unknown>);
        }
        if (canaryStatePayload && typeof canaryStatePayload === 'object') {
          setCanaryState(canaryStatePayload as Record<string, unknown>);
          writeStoredCanaryState(canaryStatePayload as Record<string, unknown>);
        }
        if (incidentSnapshotPayload && typeof incidentSnapshotPayload === 'object') {
          setIncidentSnapshot(incidentSnapshotPayload as Record<string, unknown>);
          writeStoredIncidentSnapshot(incidentSnapshotPayload as Record<string, unknown>);
        }
        if (playbookReportPayload && typeof playbookReportPayload === 'object') {
          setPlaybookReport(playbookReportPayload as Record<string, unknown>);
          writeStoredPlaybookReport(playbookReportPayload as Record<string, unknown>);
        }
        if (autoRemediationPayload && typeof autoRemediationPayload === 'object') {
          setAutoRemediation(autoRemediationPayload as Record<string, unknown>);
          writeStoredAutoRemediation(autoRemediationPayload as Record<string, unknown>);
        }
        if (canaryPromotionPayload && typeof canaryPromotionPayload === 'object') {
          setCanaryPromotion(canaryPromotionPayload as Record<string, unknown>);
          writeStoredCanaryPromotion(canaryPromotionPayload as Record<string, unknown>);
        }
        if (controlTickPayload && typeof controlTickPayload === 'object') {
          setControlTick(controlTickPayload as Record<string, unknown>);
          writeStoredControlTick(controlTickPayload as Record<string, unknown>);
        }
        if (browserTaskPayload && typeof browserTaskPayload === 'object') {
          const nextBrowser = browserTaskPayload as BrowserTaskState;
          setBrowserTask(nextBrowser);
          writeStoredBrowserTask(nextBrowser);
        }
        if (workflowStatePayload && typeof workflowStatePayload === 'object') {
          const nextWorkflow = workflowStatePayload as WorkflowState;
          setWorkflowState(nextWorkflow);
          writeStoredWorkflowState(nextWorkflow);
        }
        if (automationStatePayload && typeof automationStatePayload === 'object') {
          const nextAutomation = automationStatePayload as AutomationState;
          setAutomationState(nextAutomation);
          writeStoredAutomationState(nextAutomation);
        }
        if (whatsappChannelPayload && typeof whatsappChannelPayload === 'object') {
          writeStoredWhatsAppChannelStatus(whatsappChannelPayload as Record<string, unknown>);
        }

        if (webDashboard?.query && Array.isArray(webDashboard.results)) {
          const nextDashboard: ResearchDashboard = {
            query: webDashboard.query,
            summary: webDashboard.summary ?? '',
            generatedAt: webDashboard.generated_at,
            images: Array.isArray(webDashboard.images)
              ? webDashboard.images.filter((item): item is string => typeof item === 'string')
              : [],
            results: webDashboard.results
              .map((item) => ({
                title: item.title ?? 'Resultado',
                url: item.url ?? '',
                domain: item.domain ?? 'site',
                snippet: item.snippet,
                pageTitle: item.page_title,
                pageDescription: item.page_description,
                imageUrl: item.image_url,
              }))
              .filter((item) => item.url),
          };

          setLatestResearchDashboard(nextDashboard);
          writeStoredResearchDashboard(nextDashboard);

          if (typeof window !== 'undefined' && webDashboard.dashboard_opened !== true) {
            const dashboardUrl = webDashboard.dashboard_url || '/research-dashboard';
            const opened = window.open(dashboardUrl, 'jarvez-research-dashboard');
            if (!opened) {
              toast.warning('O navegador bloqueou a nova guia do dashboard.');
            }
          }
        }

        if (
          webDashboardSchedule?.id &&
          webDashboardSchedule?.query &&
          webDashboardSchedule?.prompt
        ) {
          const nextSchedule: ResearchSchedule = {
            id: webDashboardSchedule.id,
            query: webDashboardSchedule.query,
            cadence: webDashboardSchedule.cadence ?? 'daily',
            timeOfDay: webDashboardSchedule.time_of_day ?? '08:00',
            prompt: webDashboardSchedule.prompt,
            lastRunOn: webDashboardSchedule.last_run_on,
          };
          setResearchSchedules((current) => {
            const next = [nextSchedule, ...current.filter((item) => item.id !== nextSchedule.id)];
            writeStoredResearchSchedules(next);
            return next;
          });
          toast.message(`Briefing diario salvo para ${nextSchedule.timeOfDay}.`);
        }

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
            activeProjectId:
              typeof activeProject?.project_id === 'string' ? activeProject.project_id : undefined,
            activeProjectName:
              typeof activeProject?.name === 'string' ? activeProject.name : undefined,
            activeProjectRootPath:
              typeof activeProject?.root_path === 'string' ? activeProject.root_path : undefined,
            activeProjectIndexStatus:
              typeof activeProject?.index_status === 'string'
                ? activeProject.index_status
                : undefined,
            codingMode,
          });
        } else if (
          personaMode ||
          personaProfile ||
          activeCharacter ||
          activeCharacterCleared ||
          activeProject ||
          codingMode
        ) {
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
            activeProjectId:
              typeof activeProject?.project_id === 'string'
                ? activeProject.project_id
                : current.activeProjectId,
            activeProjectName:
              typeof activeProject?.name === 'string'
                ? activeProject.name
                : current.activeProjectName,
            activeProjectRootPath:
              typeof activeProject?.root_path === 'string'
                ? activeProject.root_path
                : current.activeProjectRootPath,
            activeProjectIndexStatus:
              typeof activeProject?.index_status === 'string'
                ? activeProject.index_status
                : current.activeProjectIndexStatus,
            codingMode: codingMode ?? current.codingMode,
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
          if (
            actionName.startsWith('project_') ||
            actionName.startsWith('code_') ||
            actionName.startsWith('coding_mode_')
          ) {
            pushCodingHistory({
              id: `${callId}-confirmation`,
              timestamp: Date.now(),
              actionName,
              status: 'confirmation_required',
              message: actionResult.message,
              projectName:
                typeof activeProject?.name === 'string'
                  ? activeProject.name
                  : securitySession.activeProjectName,
            });
          }
          return;
        }

        const status = actionResult.success ? 'completed' : 'failed';
        if (actionResult.success) {
          toast.success(`Acao executada: ${actionResult.message}`);
        } else {
          toast.error(`Falha na acao: ${actionResult.error ?? actionResult.message}`);
        }

        if (actionResult.trace_id) {
          const traceStep: ExecutionTraceStep = {
            traceId: actionResult.trace_id,
            actionName,
            timestamp: Date.now(),
            risk: actionResult.risk,
            policyDecision: actionResult.policy_decision,
            provider: evidence?.provider,
            fallbackUsed: actionResult.fallback_used,
            success: actionResult.success,
            message: actionResult.message,
          };
          pushTraceStep(traceStep);
          attachTraceToOpsCommand(traceStep);
        }

        pushEvent({
          callId,
          actionName,
          name: actionName,
          status,
          timestamp: Date.now(),
          message: actionResult.message,
        });

        if (
          actionName.startsWith('project_') ||
          actionName.startsWith('code_') ||
          actionName.startsWith('coding_mode_')
        ) {
          pushCodingHistory({
            id: `${callId}-${status}`,
            timestamp: Date.now(),
            actionName,
            status,
            message: actionResult.message,
            projectName:
              typeof activeProject?.name === 'string'
                ? activeProject.name
                : securitySession.activeProjectName,
          });
        }
      });
    }
  }, [
    applyAutonomyNotice,
    hydrateSessionSnapshot,
    pushCodingHistory,
    pushCodexTaskEvent,
    pushEvent,
    pushPolicyEvent,
    pushTraceStep,
    replaceCodexTaskHistory,
    securitySession.activeProjectName,
    textStreams,
    upsertCodexTaskHistory,
  ]);

  const recentInteractions = useMemo<RecentInteractionEntry[]>(() => {
    const backgroundEntries: RecentInteractionEntry[] = [];
    if (browserTask?.status === 'running') {
      backgroundEntries.push({
        id: `browser-${browserTask.task_id ?? 'running'}`,
        title: 'Browser agent',
        status: 'running',
        timestamp: Date.now(),
        message: browserTask.summary ?? browserTask.request ?? 'Automacao em andamento.',
        retryable: false,
        source: 'background',
      });
    }
    if (workflowState && ['planning', 'awaiting_confirmation', 'running'].includes(workflowState.status ?? '')) {
      backgroundEntries.push({
        id: `workflow-${workflowState.workflow_id ?? workflowState.status ?? 'running'}`,
        title: 'Workflow',
        status: 'running',
        timestamp: Date.now(),
        message: workflowState.summary ?? workflowState.current_step ?? 'Fluxo em andamento.',
        retryable: false,
        source: 'background',
      });
    }
    if (automationState && ['scheduled', 'running'].includes(automationState.status ?? '')) {
      backgroundEntries.push({
        id: `automation-${automationState.automation_id ?? automationState.status ?? 'running'}`,
        title: 'Automacao',
        status: 'running',
        timestamp: Date.now(),
        message: automationState.summary ?? 'Automacao ativa.',
        retryable: false,
        source: 'background',
      });
    }
    if (activeCodexTask?.status === 'running') {
      backgroundEntries.push({
        id: `codex-${activeCodexTask.task_id ?? 'running'}`,
        title: 'Codex',
        status: 'running',
        timestamp: Date.now(),
        message: activeCodexTask.summary ?? activeCodexTask.request ?? 'Tarefa de codigo em andamento.',
        retryable: false,
        source: 'background',
      });
    }

    const actionEntries = events.map((event) => ({
      id: event.callId,
      title: formatActionLabel(event.actionName),
      status: event.status,
      timestamp: event.timestamp,
      message: event.message ?? 'Sem detalhe adicional.',
      retryable: event.status === 'failed',
      actionName: event.actionName,
      source: 'action' as const,
    }));

    return [...backgroundEntries, ...actionEntries].slice(0, 8);
  }, [activeCodexTask, automationState, browserTask, events, workflowState]);

  const hasReplayableResponse = Boolean(lastReplayableMessage.trim());
  const isActionInProgress =
    Boolean(pendingConfirmation) ||
    Boolean(
      voiceInteractivity?.state &&
        ['thinking', 'confirming', 'executing', 'background'].includes(voiceInteractivity.state)
    ) ||
    recentInteractions.some((entry) => entry.status === 'running');

  const repeatLastResponse = useCallback(() => {
    const text =
      lastReplayableMessage.trim() ||
      voiceInteractivityRef.current?.spoken_message?.trim() ||
      voiceInteractivityRef.current?.display_message?.trim() ||
      '';
    if (!text) {
      toast.message('Nao ha resposta recente para repetir.');
      return;
    }
    speakReplayText(text);
  }, [lastReplayableMessage, speakReplayText]);

  const cancelActiveInteraction = useCallback(async () => {
    if (!isActionInProgress) {
      toast.message('Nenhuma acao em andamento para cancelar.');
      return;
    }

    if (pendingConfirmation) {
      setPendingConfirmation(null);
    }
    setPushToTalkActive(false);
    setClientVoiceInteractivity({
      state: 'thinking',
      activationMode: voiceInteractivityRef.current?.activation_mode ?? 'button',
      rawClientState: 'gesture_cancel_request',
      displayMessage: 'Cancelando agora.',
      spokenMessage: 'Cancelando agora.',
      canRetry: true,
    });

    try {
      await send(
        'Cancelar a acao em andamento e qualquer tarefa em segundo plano que possa ser interrompida com seguranca.'
      );
      toast.message('Pedido de cancelamento enviado.');
      setClientVoiceInteractivity({
        state: 'idle',
        activationMode: voiceInteractivityRef.current?.activation_mode ?? 'button',
        rawClientState: 'gesture_cancel_sent',
        displayMessage: 'Cancelamento enviado.',
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Nao consegui enviar o cancelamento.';
      toast.error(message);
      setClientVoiceInteractivity({
        state: 'error',
        activationMode: voiceInteractivityRef.current?.activation_mode ?? 'button',
        rawClientState: 'gesture_cancel_error',
        displayMessage: message,
        errorCode: 'gesture_cancel_error',
        canRetry: true,
      });
    }
  }, [isActionInProgress, pendingConfirmation, send, setClientVoiceInteractivity]);

  const retryRecentInteraction = useCallback(
    async (entry: RecentInteractionEntry) => {
      if (!entry.retryable) {
        return;
      }

      setClientVoiceInteractivity({
        state: 'confirming',
        activationMode: voiceInteractivityRef.current?.activation_mode ?? 'button',
        rawClientState: 'gesture_retry_request',
        displayMessage: `Tentando novamente ${entry.title}.`,
      });

      try {
        await send(
          `Tente novamente a acao ${entry.actionName ?? entry.title}, considerando o ultimo contexto e pedindo clarificacao se houver ambiguidade.`
        );
        toast.message('Retry enviado ao Jarvez.');
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Nao consegui reenviar a acao.';
        toast.error(message);
        setClientVoiceInteractivity({
          state: 'error',
          activationMode: voiceInteractivityRef.current?.activation_mode ?? 'button',
          rawClientState: 'gesture_retry_error',
          displayMessage: message,
          errorCode: 'gesture_retry_error',
          canRetry: true,
        });
      }
    },
    [send, setClientVoiceInteractivity]
  );

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
    latestResearchDashboard,
    researchSchedules,
    latestModelRoute,
    subagentStates,
    policyEvents,
    executionTraces,
    latestEvalBaselineSummary,
    evalMetrics,
    evalMetricsSummary,
    sloReport,
    providersHealth,
    featureFlags,
    canaryState,
    incidentSnapshot,
    playbookReport,
    autoRemediation,
    canaryPromotion,
    controlTick,
    latestWorkerStatus,
    latestProjectAnalysis,
    latestProposedCodeChange,
    latestCommandExecution,
    latestGitStatus,
    latestGitDiffSummary,
    codingHistory,
    activeCodexTask,
    browserTask,
    workflowState,
    automationState,
    voiceInteractivity,
    pushToTalkActive,
    isActionInProgress,
    recentInteractions,
    hasReplayableResponse,
    codexTaskEvents,
    codexTaskHistory,
    securitySession,
    repeatLastResponse,
    retryRecentInteraction,
    cancelActiveInteraction,
    confirmPendingAction,
    cancelPendingAction,
  };
}
