'use client';

import React, { useEffect, useRef, useState } from 'react';
import {
  BookOpenText,
  Disc3,
  MessageCircleMore,
  PanelRightClose,
  PanelRightOpen,
} from 'lucide-react';
import { AnimatePresence, motion } from 'motion/react';
import {
  useChat,
  useRemoteParticipants,
  useSessionContext,
  useSessionMessages,
  useTrackVolume,
  useVoiceAssistant,
} from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import {
  AgentControlBar,
  type AgentControlBarControls,
} from '@/components/agents-ui/agent-control-bar';
import { TileLayout } from '@/components/app/tile-layout';
import { Button } from '@/components/ui/button';
import { useAgentActionEvents } from '@/hooks/useAgentActionEvents';
import { useAwarenessProactive } from '@/hooks/useAwarenessProactive';
import {
  TRUST_CENTER_OPS_COMMAND_QUEUE_KEY,
  claimStoredPendingOpsCommand,
  updateStoredOpsCommandStatus,
} from '@/lib/orchestration-storage';
import {
  readStoredResearchSchedules,
  writeStoredResearchSchedules,
} from '@/lib/research-dashboard-storage';
import { cn } from '@/lib/shadcn/utils';
import type { ParticipantIdentity, ReconnectState, ResearchSchedule } from '@/lib/types/realtime';
import { Shimmer } from '../ai-elements/shimmer';
import { ActionConfirmationPrompt } from './action-confirmation-prompt';
import { CodingWorkspace } from './coding-workspace';

const MotionBottom = motion.create('div');
const MotionMessage = motion.create(Shimmer);

const BOTTOM_VIEW_MOTION_PROPS = {
  variants: {
    visible: {
      opacity: 1,
      translateY: '0%',
    },
    hidden: {
      opacity: 0,
      translateY: '100%',
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.3,
    delay: 0.5,
    ease: 'easeOut' as const,
  },
};

const SHIMMER_MOTION_PROPS = {
  variants: {
    visible: {
      opacity: 1,
      transition: {
        ease: 'easeIn' as const,
        duration: 0.5,
        delay: 0.8,
      },
    },
    hidden: {
      opacity: 0,
      transition: {
        ease: 'easeIn' as const,
        duration: 0.5,
        delay: 0,
      },
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
};

interface SessionViewProps {
  appConfig: AppConfig;
  reconnectState: ReconnectState;
  onManualDisconnect?: () => void;
}

interface VantaEffect {
  options: { chaos: number };
  setOptions: (options: { chaos: number }) => void;
  destroy: () => void;
}

interface VantaScriptWindow extends Window {
  p5?: unknown;
  VANTA?: {
    TRUNK?: (options: Record<string, unknown>) => VantaEffect;
  };
}

const VantaController = ({
  vantaRef,
}: {
  vantaRef: React.MutableRefObject<VantaEffect | null>;
}) => {
  const { audioTrack } = useVoiceAssistant();
  const volume = useTrackVolume(audioTrack);

  useEffect(() => {
    const effect = vantaRef.current;
    if (!effect) return;

    const baseChaos = 3.0;
    const voiceChaos = volume * 7.0;
    const finalChaos = baseChaos + voiceChaos;

    if (Math.abs(effect.options.chaos - finalChaos) > 0.05) {
      effect.setOptions({ chaos: finalChaos });
    }
  }, [volume, vantaRef]);

  return null;
};

const VantaOrb = ({
  isConnected,
  color,
  vantaRef,
}: {
  isConnected: boolean;
  color: number;
  vantaRef: React.MutableRefObject<VantaEffect | null>;
}) => {
  const localRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let vantaEffect: VantaEffect | null = null;
    let attempts = 0;
    let initTimer: NodeJS.Timeout;

    const tryInitVanta = () => {
      const el = localRef.current;
      const win = window as VantaScriptWindow;
      const hasVanta = !!win.VANTA?.TRUNK;
      const hasP5 = !!win.p5;

      if (el && hasVanta && hasP5) {
        try {
          vantaEffect =
            win.VANTA?.TRUNK?.({
              el,
              p5: win.p5,
              mouseControls: false,
              touchControls: false,
              gyroControls: false,
              minHeight: 200.0,
              minWidth: 200.0,
              scale: 1.0,
              scaleMobile: 1.0,
              color,
              backgroundColor: 0x000000,
              spacing: 0.0,
              chaos: 3.0,
            }) ?? null;

          vantaRef.current = vantaEffect;
        } catch (error) {
          console.error('Vanta Orb Init Error:', error);
          attempts++;
          if (attempts < 10) initTimer = setTimeout(tryInitVanta, 500);
        }
      } else {
        attempts++;
        if (attempts < 50) initTimer = setTimeout(tryInitVanta, 100);
      }
    };

    tryInitVanta();

    return () => {
      clearTimeout(initTimer);
      if (vantaEffect) {
        try {
          if (vantaRef.current === vantaEffect) {
            vantaRef.current = null;
          }
          vantaEffect.destroy();
        } catch (error) {
          console.error('Vanta Orb destroy error:', error);
        }
      }
    };
  }, [isConnected, color, vantaRef]);

  return (
    <div
      ref={localRef}
      className="h-[1000px] w-[1000px]"
      style={{
        transform: 'scale(0.5) translateY(-15%)',
        transformOrigin: 'center center',
      }}
    />
  );
};

export const SessionView = ({
  appConfig,
  reconnectState,
  onManualDisconnect,
  ...props
}: React.ComponentProps<'section'> & SessionViewProps) => {
  const session = useSessionContext();
  const { send } = useChat();
  const { messages } = useSessionMessages(session);
  const [chatOpen, setChatOpen] = useState(false);
  const [integrationsMenuOpen, setIntegrationsMenuOpen] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const vantaEffectRef = useRef<VantaEffect | null>(null);
  const opsDispatcherIdRef = useRef(
    `session-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
  );
  const isDispatchingOpsCommandRef = useRef(false);
  const {
    events,
    pendingConfirmation,
    isConfirming,
    latestWorkerStatus,
    latestProjectAnalysis,
    latestProposedCodeChange,
    latestCommandExecution,
    latestGitStatus,
    latestGitDiffSummary,
    codingHistory,
    activeCodexTask,
    codexTaskEvents,
    codexTaskHistory,
    voiceInteractivity,
    securitySession,
    confirmPendingAction,
    cancelPendingAction,
  } = useAgentActionEvents();
  const { contextLabel, silentMode, setSilentMode } = useAwarenessProactive();

  const participants = useRemoteParticipants();
  const agentParticipant = participants.find((p) => !p.isLocal);
  const agentPersona = (agentParticipant?.attributes?.agent_persona ??
    'jarvis') as ParticipantIdentity;

  const PERSONA_COLORS = {
    alice: 0xff69b4,
    jarvis: 0x1da3b9,
    default: 0x1da3b9,
    faria_lima: 0xa0a0a0,
    mona: 0xff4da6,
    rpg: 0x7a3eea,
  };
  const modeColorHex = securitySession.personaColorHex;
  const modeColor =
    modeColorHex && /^#?[0-9a-fA-F]{6}$/.test(modeColorHex)
      ? Number.parseInt(modeColorHex.replace('#', ''), 16)
      : undefined;
  const modeFallbackColor =
    PERSONA_COLORS[(securitySession.personaMode ?? 'default') as keyof typeof PERSONA_COLORS];
  const currentColor =
    modeColor ??
    modeFallbackColor ??
    PERSONA_COLORS[agentPersona as keyof typeof PERSONA_COLORS] ??
    PERSONA_COLORS.jarvis;

  useEffect(() => {
    const loadScript = (src: string): Promise<boolean> => {
      return new Promise((resolve) => {
        if (typeof document === 'undefined') return resolve(false);
        if (document.querySelector(`script[src="${src}"]`)) return resolve(true);

        const script = document.createElement('script');
        script.src = src;
        script.async = true;
        script.onload = () => resolve(true);
        script.onerror = () => resolve(false);
        document.body.appendChild(script);
      });
    };

    const setup = async () => {
      await loadScript('https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.4.0/p5.min.js');
      await loadScript('https://cdn.jsdelivr.net/npm/vanta@0.5.24/dist/vanta.trunk.min.js');
    };

    setup();
  }, []);

  const controls: AgentControlBarControls = {
    leave: true,
    microphone: true,
    chat: appConfig.supportsChatInput,
    camera: appConfig.supportsVideoInput,
    screenShare: appConfig.supportsScreenShare,
  };

  useEffect(() => {
    const lastMessage = messages.at(-1);
    const lastMessageIsLocal = lastMessage?.from?.isLocal === true;
    if (scrollAreaRef.current && lastMessageIsLocal) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    if (!session.isConnected || typeof window === 'undefined') {
      return;
    }

    const runDueSchedules = () => {
      const parsed: ResearchSchedule[] = readStoredResearchSchedules();

      if (!Array.isArray(parsed) || parsed.length === 0) {
        return;
      }

      const now = new Date();
      const today = now.toISOString().slice(0, 10);
      const minutesNow = now.getHours() * 60 + now.getMinutes();
      let changed = false;

      const nextSchedules = parsed.map((schedule) => {
        if (!schedule?.timeOfDay || !schedule.prompt || schedule.lastRunOn === today) {
          return schedule;
        }

        const [hoursText, minutesText] = schedule.timeOfDay.split(':');
        const hours = Number.parseInt(hoursText ?? '', 10);
        const minutes = Number.parseInt(minutesText ?? '', 10);
        if (!Number.isFinite(hours) || !Number.isFinite(minutes)) {
          return schedule;
        }

        const scheduledMinutes = hours * 60 + minutes;
        if (minutesNow < scheduledMinutes) {
          return schedule;
        }

        changed = true;
        void send(schedule.prompt);
        return {
          ...schedule,
          lastRunOn: today,
        };
      });

      if (changed) {
        writeStoredResearchSchedules(nextSchedules);
      }
    };

    runDueSchedules();
    const timer = window.setInterval(runDueSchedules, 60_000);
    return () => window.clearInterval(timer);
  }, [send, session.isConnected]);

  useEffect(() => {
    if (!session.isConnected || typeof window === 'undefined') {
      return;
    }

    let cancelled = false;

    const processOpsQueue = async () => {
      if (cancelled || isDispatchingOpsCommandRef.current) {
        return;
      }

      const claimed = claimStoredPendingOpsCommand(opsDispatcherIdRef.current);
      if (!claimed) {
        return;
      }

      isDispatchingOpsCommandRef.current = true;
      try {
        await send(claimed.prompt);
        updateStoredOpsCommandStatus(claimed.id, 'sent', {
          dispatcherId: opsDispatcherIdRef.current,
          setDispatchTimestamp: true,
        });
      } catch (error) {
        updateStoredOpsCommandStatus(claimed.id, 'failed', {
          dispatcherId: opsDispatcherIdRef.current,
          error: error instanceof Error ? error.message : 'Falha ao enviar comando operacional.',
        });
      } finally {
        isDispatchingOpsCommandRef.current = false;
        if (!cancelled) {
          window.setTimeout(() => {
            void processOpsQueue();
          }, 150);
        }
      }
    };

    const handleStorage = (event: StorageEvent) => {
      if (event.key === TRUST_CENTER_OPS_COMMAND_QUEUE_KEY) {
        void processOpsQueue();
      }
    };

    void processOpsQueue();
    window.addEventListener('storage', handleStorage);
    const timer = window.setInterval(() => {
      void processOpsQueue();
    }, 1500);

    return () => {
      cancelled = true;
      window.removeEventListener('storage', handleStorage);
      window.clearInterval(timer);
    };
  }, [send, session.isConnected]);

  const handleDisconnect = () => {
    if (onManualDisconnect) onManualDisconnect();

    try {
      if (session.end) session.end();
    } catch (error) {
      console.warn('Erro ao desconectar sessao:', error);
    }
  };

  const handleConfirmAction = async () => {
    await confirmPendingAction();
  };

  const handleCancelAction = () => {
    cancelPendingAction();
    void send('Cancelar acao pendente.');
  };
  const hasCodingContext =
    securitySession.codingMode === 'coding' ||
    !!securitySession.activeProjectName ||
    !!activeCodexTask ||
    codexTaskHistory.length > 0 ||
    !!latestWorkerStatus ||
    !!latestProjectAnalysis ||
    !!latestProposedCodeChange ||
    !!latestCommandExecution ||
    !!latestGitStatus ||
    !!latestGitDiffSummary;
  const isCodingWorkspace = hasCodingContext;
  const shouldShowCodexPanel =
    !isCodingWorkspace &&
    (!!latestWorkerStatus ||
      !!latestProjectAnalysis ||
      !!latestProposedCodeChange ||
      !!latestCommandExecution ||
      !!latestGitStatus ||
      !!latestGitDiffSummary);

  if (isCodingWorkspace) {
    return (
      <section className="relative flex h-svh w-svw flex-col overflow-hidden bg-black" {...props}>
        <CodingWorkspace
          securitySession={securitySession}
          activeCodexTask={activeCodexTask}
          codexTaskEvents={codexTaskEvents}
          codexTaskHistory={codexTaskHistory}
          contextLabel={contextLabel}
          silentMode={silentMode}
          integrationsMenuOpen={integrationsMenuOpen}
          onToggleSilentMode={() => setSilentMode(!silentMode)}
          onToggleIntegrations={() => setIntegrationsMenuOpen((current) => !current)}
          onSendPrompt={send}
        />

        <div className="pointer-events-none absolute inset-x-0 bottom-4 z-40 px-4">
          <div className="mx-auto w-full max-w-6xl">
            {reconnectState.connectionState !== 'connected' && (
              <div className="pointer-events-auto mx-auto mb-3 flex w-full max-w-4xl items-center justify-between rounded-lg border border-white/20 bg-black/60 px-3 py-2 text-xs text-white">
                <span>
                  {reconnectState.isReconnecting
                    ? `Reconectando... tentativa ${reconnectState.attempt} de ${reconnectState.maxAttempts}`
                    : 'Desconectado. Tente reconectar manualmente.'}
                </span>
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  onClick={() => void reconnectState.reconnectNow()}
                  disabled={reconnectState.isReconnecting}
                >
                  Reconectar
                </Button>
              </div>
            )}

            <div className="pointer-events-auto mx-auto w-full max-w-4xl">
              <ActionConfirmationPrompt
                pendingConfirmation={pendingConfirmation}
                isConfirming={isConfirming}
                onConfirm={handleConfirmAction}
                onCancel={handleCancelAction}
              />
            </div>

            <div className="pointer-events-auto relative mx-auto max-w-4xl bg-transparent pb-2 opacity-85 transition-opacity duration-200 focus-within:opacity-100 hover:opacity-100">
              <AgentControlBar
                variant="livekit"
                controls={controls}
                isChatOpen={chatOpen}
                isConnected={session.isConnected}
                onDisconnect={handleDisconnect}
                onIsChatOpenChange={setChatOpen}
              />
            </div>
          </div>
        </div>

        <AnimatePresence>
          {integrationsMenuOpen && (
            <motion.aside
              initial={{ opacity: 0, x: 16 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 16 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
              className="pointer-events-auto fixed top-24 right-4 z-[120] w-72 rounded-3xl border border-white/10 bg-black/55 p-3 shadow-2xl backdrop-blur-xl"
            >
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-white">Conexoes</p>
                  <p className="text-[11px] text-white/50">Autorizacoes e webhooks</p>
                </div>
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  onClick={() => setIntegrationsMenuOpen(false)}
                >
                  <PanelRightClose className="size-4" />
                </Button>
              </div>

              <div className="space-y-2">
                <button
                  type="button"
                  className="flex w-full items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-3 py-3 text-left transition-colors hover:bg-white/10"
                  onClick={() => {
                    setIntegrationsMenuOpen(false);
                    window.open('/api/spotify/login', '_blank', 'noopener,noreferrer');
                  }}
                >
                  <div className="rounded-xl bg-emerald-500/15 p-2 text-emerald-300">
                    <Disc3 className="size-5" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-white">Spotify</p>
                    <p className="truncate text-[11px] text-white/55">
                      Conectar conta e controlar playback
                    </p>
                  </div>
                </button>

                <button
                  type="button"
                  className="flex w-full items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-3 py-3 text-left transition-colors hover:bg-white/10"
                  onClick={() => {
                    setIntegrationsMenuOpen(false);
                    window.open('/api/onenote/login', '_blank', 'noopener,noreferrer');
                  }}
                >
                  <div className="rounded-xl bg-violet-500/15 p-2 text-violet-300">
                    <BookOpenText className="size-5" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-white">OneNote</p>
                    <p className="truncate text-[11px] text-white/55">
                      Consultar e atualizar cadernos e paginas
                    </p>
                  </div>
                </button>

                <button
                  type="button"
                  className="flex w-full items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-3 py-3 text-left transition-colors hover:bg-white/10"
                  onClick={() => {
                    setIntegrationsMenuOpen(false);
                    window.open('/api/whatsapp/webhook', '_blank', 'noopener,noreferrer');
                  }}
                >
                  <div className="rounded-xl bg-sky-500/15 p-2 text-sky-300">
                    <MessageCircleMore className="size-5" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-white">WhatsApp</p>
                    <p className="truncate text-[11px] text-white/55">
                      Abrir webhook e validar recebimento
                    </p>
                  </div>
                </button>
              </div>
            </motion.aside>
          )}
        </AnimatePresence>
      </section>
    );
  }

  return (
    <section className="relative flex h-svh w-svw flex-col overflow-hidden bg-black" {...props}>
      <VantaController vantaRef={vantaEffectRef} />

      <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
        <div className="absolute inset-0 flex items-center justify-center overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={session.isConnected ? `vanta-${agentPersona}` : 'vanta-disconnected'}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 1.5, ease: 'easeInOut' }}
              className="p5-canvas-container absolute inset-0 flex items-center justify-center"
            >
              <VantaOrb
                isConnected={session.isConnected}
                color={currentColor}
                vantaRef={vantaEffectRef}
              />
            </motion.div>
          </AnimatePresence>
        </div>

        <div className="relative z-10">
          <TileLayout chatOpen={chatOpen} />
        </div>
      </div>

      <div className="pointer-events-none flex-1" />

      <div className="pointer-events-none absolute inset-x-0 top-4 z-50 px-3">
        <div className="mx-auto w-full max-w-3xl">
          <AnimatePresence>
            <motion.div
              key="top-hud"
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              className="pointer-events-auto mx-auto w-full max-w-2xl rounded-2xl border border-white/10 bg-black/20 px-3 py-2 backdrop-blur-xl"
            >
              <div className="flex flex-wrap items-center gap-2 text-[11px] text-white/90">
                <span
                  className={cn(
                    'rounded-full border px-2 py-1',
                    securitySession.authenticated
                      ? 'border-emerald-300/30 bg-emerald-500/10 text-emerald-200'
                      : 'border-white/10 bg-white/5 text-white/70'
                  )}
                >
                  {securitySession.authenticated
                    ? `Privado: ${securitySession.authMethod ?? 'ok'}`
                    : securitySession.stepUpRequired
                      ? 'Privado: step-up'
                      : 'Privado: bloqueado'}
                </span>
                <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1">
                  {securitySession.personaLabel ?? securitySession.personaMode ?? 'Jarvez Classico'}
                </span>
                {securitySession.activeCharacterName && (
                  <span className="rounded-full border border-amber-300/30 bg-amber-500/10 px-2 py-1 text-amber-100">
                    {securitySession.activeCharacterName}
                  </span>
                )}
                {securitySession.codingMode === 'coding' && (
                  <span className="rounded-full border border-cyan-300/30 bg-cyan-500/10 px-2 py-1 text-cyan-100">
                    Codex Mode
                  </span>
                )}
                {securitySession.activeProjectName && (
                  <span className="rounded-full border border-sky-300/30 bg-sky-500/10 px-2 py-1 text-sky-100">
                    {securitySession.activeProjectName}
                  </span>
                )}
                {securitySession.autonomyNotice?.active && (
                  <span
                    className={cn(
                      'rounded-full border px-2 py-1',
                      securitySession.autonomyNotice.level === 'critical'
                        ? 'border-rose-300/30 bg-rose-500/10 text-rose-100'
                        : securitySession.autonomyNotice.level === 'warning'
                          ? 'border-amber-300/30 bg-amber-500/10 text-amber-100'
                          : 'border-cyan-300/30 bg-cyan-500/10 text-cyan-100'
                    )}
                    title={securitySession.autonomyNotice.message ?? undefined}
                  >
                    {securitySession.autonomyNotice.domain
                      ? `Autonomia reduzida: ${securitySession.autonomyNotice.domain}`
                      : 'Autonomia reduzida'}
                  </span>
                )}
                {voiceInteractivity?.state && (
                  <span
                    className={cn(
                      'rounded-full border px-2 py-1',
                      voiceInteractivity.state === 'error'
                        ? 'border-rose-300/30 bg-rose-500/10 text-rose-100'
                        : voiceInteractivity.state === 'speaking'
                          ? 'border-cyan-300/30 bg-cyan-500/10 text-cyan-100'
                          : voiceInteractivity.state === 'listening'
                            ? 'border-emerald-300/30 bg-emerald-500/10 text-emerald-100'
                            : voiceInteractivity.state === 'background'
                              ? 'border-violet-300/30 bg-violet-500/10 text-violet-100'
                              : 'border-white/10 bg-white/5 text-white/80'
                    )}
                    title={voiceInteractivity.display_message ?? undefined}
                  >
                    {voiceInteractivity.display_message ??
                      ({
                        idle: 'Pronto',
                        listening: 'Ouvindo',
                        transcribing: 'Transcrevendo',
                        thinking: 'Pensando',
                        confirming: 'Confirmando',
                        executing: 'Executando',
                        background: 'Em segundo plano',
                        speaking: 'Falando',
                        error: 'Erro',
                      }[voiceInteractivity.state] ?? 'Estado')}
                  </span>
                )}
                <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-white/70">
                  {contextLabel}
                </span>
                <div className="ml-auto flex items-center gap-2">
                  <Button
                    type="button"
                    size="sm"
                    variant="secondary"
                    onClick={() => setIntegrationsMenuOpen((current) => !current)}
                  >
                    {integrationsMenuOpen ? (
                      <PanelRightClose className="size-4" />
                    ) : (
                      <PanelRightOpen className="size-4" />
                    )}
                    <span>Integracoes</span>
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="secondary"
                    onClick={() => setSilentMode(!silentMode)}
                  >
                    {silentMode ? 'Ativar proativo' : 'Modo silencioso'}
                  </Button>
                </div>
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      <MotionBottom
        {...BOTTOM_VIEW_MOTION_PROPS}
        className="relative z-40 mx-auto mb-4 w-full max-w-3xl px-3"
      >
        {appConfig.isPreConnectBufferEnabled && (
          <AnimatePresence>
            {messages.length === 0 && (
              <MotionMessage
                key="pre-connect-message"
                duration={2}
                aria-hidden={messages.length > 0}
                {...SHIMMER_MOTION_PROPS}
                className="pointer-events-none mx-auto block w-full max-w-2xl pb-8 text-center text-sm font-semibold"
              >
                O Jarvis esta ouvindo, pode falar...
              </MotionMessage>
            )}
          </AnimatePresence>
        )}

        {reconnectState.connectionState !== 'connected' && (
          <div className="mx-auto mb-3 flex w-full max-w-2xl items-center justify-between rounded-lg border border-white/20 bg-black/40 px-3 py-2 text-xs text-white">
            <span>
              {reconnectState.isReconnecting
                ? `Reconectando... tentativa ${reconnectState.attempt} de ${reconnectState.maxAttempts}`
                : 'Desconectado. Tente reconectar manualmente.'}
            </span>
            <Button
              type="button"
              size="sm"
              variant="secondary"
              onClick={() => void reconnectState.reconnectNow()}
              disabled={reconnectState.isReconnecting}
            >
              Reconectar
            </Button>
          </div>
        )}

        <ActionConfirmationPrompt
          pendingConfirmation={pendingConfirmation}
          isConfirming={isConfirming}
          onConfirm={handleConfirmAction}
          onCancel={handleCancelAction}
        />

        <AnimatePresence>
          {integrationsMenuOpen && (
            <motion.aside
              initial={{ opacity: 0, x: 16 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 16 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
              className="pointer-events-auto fixed top-24 right-4 z-[120] w-72 rounded-3xl border border-white/10 bg-black/55 p-3 shadow-2xl backdrop-blur-xl"
            >
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-white">Conexoes</p>
                  <p className="text-[11px] text-white/50">Autorizacoes e webhooks</p>
                </div>
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  onClick={() => setIntegrationsMenuOpen(false)}
                >
                  <PanelRightClose className="size-4" />
                </Button>
              </div>

              <div className="space-y-2">
                <button
                  type="button"
                  className="flex w-full items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-3 py-3 text-left transition-colors hover:bg-white/10"
                  onClick={() => {
                    setIntegrationsMenuOpen(false);
                    window.open('/api/spotify/login', '_blank', 'noopener,noreferrer');
                  }}
                >
                  <div className="rounded-xl bg-emerald-500/15 p-2 text-emerald-300">
                    <Disc3 className="size-5" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-white">Spotify</p>
                    <p className="truncate text-[11px] text-white/55">
                      Conectar conta e controlar playback
                    </p>
                  </div>
                </button>

                <button
                  type="button"
                  className="flex w-full items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-3 py-3 text-left transition-colors hover:bg-white/10"
                  onClick={() => {
                    setIntegrationsMenuOpen(false);
                    window.open('/api/onenote/login', '_blank', 'noopener,noreferrer');
                  }}
                >
                  <div className="rounded-xl bg-violet-500/15 p-2 text-violet-300">
                    <BookOpenText className="size-5" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-white">OneNote</p>
                    <p className="truncate text-[11px] text-white/55">
                      Consultar e atualizar cadernos e paginas
                    </p>
                  </div>
                </button>

                <button
                  type="button"
                  className="flex w-full items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-3 py-3 text-left transition-colors hover:bg-white/10"
                  onClick={() => {
                    setIntegrationsMenuOpen(false);
                    window.open('/api/whatsapp/webhook', '_blank', 'noopener,noreferrer');
                  }}
                >
                  <div className="rounded-xl bg-sky-500/15 p-2 text-sky-300">
                    <MessageCircleMore className="size-5" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-white">WhatsApp</p>
                    <p className="truncate text-[11px] text-white/55">
                      Abrir webhook e validar recebimento
                    </p>
                  </div>
                </button>
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        <div className="relative mx-auto max-w-2xl bg-transparent pb-3 opacity-75 transition-opacity duration-200 focus-within:opacity-100 hover:opacity-100 md:pb-12">
          <AgentControlBar
            variant="livekit"
            controls={controls}
            isChatOpen={chatOpen}
            isConnected={session.isConnected}
            onDisconnect={handleDisconnect}
            onIsChatOpenChange={setChatOpen}
          />
        </div>
      </MotionBottom>
    </section>
  );
};
