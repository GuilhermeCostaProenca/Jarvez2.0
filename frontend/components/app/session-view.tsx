'use client';

import React, { useEffect, useRef, useState } from 'react';
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
import { cn } from '@/lib/shadcn/utils';
import type { ParticipantIdentity, ReconnectState } from '@/lib/types/realtime';
import { Shimmer } from '../ai-elements/shimmer';
import { ActionConfirmationPrompt } from './action-confirmation-prompt';

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
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const vantaEffectRef = useRef<VantaEffect | null>(null);
  const {
    events,
    pendingConfirmation,
    isConfirming,
    securitySession,
    confirmPendingAction,
    cancelPendingAction,
  } = useAgentActionEvents();

  const participants = useRemoteParticipants();
  const agentParticipant = participants.find((p) => !p.isLocal);
  const agentPersona = (agentParticipant?.attributes?.agent_persona ??
    'jarvis') as ParticipantIdentity;

  const PERSONA_COLORS = {
    alice: 0xff69b4,
    jarvis: 0x1da3b9,
  };
  const currentColor =
    PERSONA_COLORS[agentPersona as keyof typeof PERSONA_COLORS] ?? PERSONA_COLORS.jarvis;

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

      <MotionBottom
        {...BOTTOM_VIEW_MOTION_PROPS}
        className="relative z-10 mx-auto mb-4 w-full max-w-3xl px-3"
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

        <div className="mx-auto mb-3 flex w-full max-w-2xl items-center justify-between rounded-lg border border-white/20 bg-black/40 px-3 py-2 text-xs text-white">
          <span>
            {securitySession.authenticated
              ? `Sessao privada autenticada (${securitySession.expiresIn}s restantes)`
              : 'Sessao privada bloqueada. Autentique com PIN para liberar conteudo sensivel.'}
          </span>
        </div>

        <ActionConfirmationPrompt
          pendingConfirmation={pendingConfirmation}
          isConfirming={isConfirming}
          onConfirm={handleConfirmAction}
          onCancel={handleCancelAction}
        />

        {events.length > 0 && (
          <div className="mx-auto mb-3 w-full max-w-2xl rounded-lg border border-white/20 bg-black/40 px-3 py-2 text-xs text-white/90">
            <p className="mb-2 font-semibold text-white">Acoes recentes</p>
            <div className="space-y-1">
              {events.slice(0, 3).map((event) => (
                <div key={event.callId} className="flex items-center justify-between gap-2">
                  <span className="truncate">
                    <span
                      className={cn(
                        'mr-2 font-semibold',
                        event.status === 'completed' && 'text-emerald-300',
                        event.status === 'failed' && 'text-rose-300',
                        event.status === 'confirmation_required' && 'text-amber-300'
                      )}
                    >
                      {event.status === 'completed' && 'SUCESSO'}
                      {event.status === 'failed' && 'FALHA'}
                      {event.status === 'confirmation_required' && 'CONFIRMAR'}
                    </span>
                    {event.message ?? event.actionName}
                  </span>
                  <span className="shrink-0 text-[11px] text-white/60">
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="relative mx-auto max-w-2xl bg-transparent pb-3 md:pb-12">
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
