'use client';

import { type ComponentProps, useEffect, useRef, useState } from 'react';
import { Track } from 'livekit-client';
import { Loader, MessageSquareTextIcon, Pin, SendHorizontal } from 'lucide-react';
import { motion } from 'motion/react';
import { useChat } from '@livekit/components-react';
import { AgentDisconnectButton } from '@/components/agents-ui/agent-disconnect-button';
import { AgentTrackControl } from '@/components/agents-ui/agent-track-control';
import {
  AgentTrackToggle,
  agentTrackToggleVariants,
} from '@/components/agents-ui/agent-track-toggle';
import { Button } from '@/components/ui/button';
import { Toggle } from '@/components/ui/toggle';
import {
  type UseInputControlsProps,
  useInputControls,
  usePublishPermissions,
} from '@/hooks/agents-ui/use-agent-control-bar';
import { cn } from '@/lib/shadcn/utils';

const TOGGLE_VARIANT_1 = [
  '[&_[data-state=off]]:bg-[#1da3b9]/10 [&_[data-state=off]]:hover:bg-[#1da3b9]/20',
  '[&_[data-state=off]_~_button]:bg-[#1da3b9]/10 [&_[data-state=off]_~_button]:hover:bg-[#1da3b9]/20',
  '[&_[data-state=off]]:border-[#1da3b9]/20 [&_[data-state=off]]:hover:border-[#1da3b9]/40',
  '[&_[data-state=off]_~_button]:border-[#1da3b9]/20 [&_[data-state=off]_~_button]:hover:border-[#1da3b9]/40',
  '[&_[data-state=off]]:text-destructive [&_[data-state=off]]:hover:text-destructive',
  'bg-[#1da3b9]/5 border-[#1da3b9]/10 text-white', // Estilo base/ON azulado
  'dark:bg-[#1da3b9]/5',
];

const TOGGLE_VARIANT_2 = [
  'data-[state=off]:bg-[#1da3b9]/10 data-[state=off]:hover:bg-[#1da3b9]/20',
  'data-[state=off]:border-[#1da3b9]/20 data-[state=off]:hover:border-[#1da3b9]/40',
  'data-[state=off]:text-white/70 data-[state=off]:hover:text-white',
  // Estado ON usando o Azul Ciano da Orb (#1da3b9)
  'data-[state=on]:bg-[#1da3b9]/30 data-[state=on]:hover:bg-[#1da3b9]/40',
  'data-[state=on]:border-[#1da3b9]/50 data-[state=on]:text-[#43d9f0]',
  'dark:data-[state=on]:bg-[#1da3b9]/30 dark:data-[state=on]:text-[#43d9f0]',
];

const MOTION_PROPS = {
  variants: {
    hidden: {
      height: 0,
      opacity: 0,
      marginBottom: 0,
    },
    visible: {
      height: 'auto',
      opacity: 1,
      marginBottom: 12,
    },
  },
  initial: 'hidden',
  transition: {
    duration: 0.3,
    ease: 'easeOut' as const,
  },
};

interface AgentChatInputProps {
  chatOpen: boolean;
  onSend?: (message: string) => void;
  className?: string;
}

function AgentChatInput({ chatOpen, onSend = async () => { }, className }: AgentChatInputProps) {
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [isSending, setIsSending] = useState(false);
  const [message, setMessage] = useState<string>('');

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    try {
      setIsSending(true);
      await onSend(message);
      setMessage('');
    } catch (error) {
      console.error(error);
    } finally {
      setIsSending(false);
    }
  };

  const isDisabled = isSending || message.trim().length === 0;

  useEffect(() => {
    if (chatOpen) return;
    // when not disabled refocus on input
    inputRef.current?.focus();
  }, [chatOpen]);

  return (
    <form
      onSubmit={handleSubmit}
      className={cn('mb-3 flex grow items-end gap-2 rounded-md pl-1 text-sm', className)}
    >
      <textarea
        autoFocus
        ref={inputRef}
        value={message}
        disabled={!chatOpen}
        placeholder="Digite algo..."
        onChange={(e) => setMessage(e.target.value)}
        className="field-sizing-content max-h-16 min-h-8 flex-1 py-2 [scrollbar-width:thin] focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
      />
      <Button
        size="icon"
        type="submit"
        disabled={isDisabled}
        variant={isDisabled ? 'secondary' : 'default'}
        title={isSending ? 'Enviando...' : 'Enviar'}
        className="self-end disabled:cursor-not-allowed"
      >
        {isSending ? <Loader className="animate-spin" /> : <SendHorizontal />}
      </Button>
    </form>
  );
}

/**
 * Configuration for which controls to display in the AgentControlBar.
 */
export interface AgentControlBarControls {
  /**
   * Whether to show the leave/disconnect button.
   * @defaultValue true
   */
  leave?: boolean;
  /**
   * Whether to show the camera toggle control.
   * @defaultValue true (if camera publish permission is granted)
   */
  camera?: boolean;
  /**
   * Whether to show the microphone toggle control.
   * @defaultValue true (if microphone publish permission is granted)
   */
  microphone?: boolean;
  /**
   * Whether to show the screen share toggle control.
   * @defaultValue true (if screen share publish permission is granted)
   */
  screenShare?: boolean;
  /**
   * Whether to show the chat toggle control.
   * @defaultValue true (if data publish permission is granted)
   */
  chat?: boolean;
}

export interface AgentControlBarProps extends UseInputControlsProps {
  /**
   * The visual style of the control bar.
   * @default 'default'
   */
  variant?: 'default' | 'outline' | 'livekit';
  /**
   * This takes an object with the following keys: `leave`, `microphone`, `screenShare`, `camera`, `chat`.
   * Each key maps to a boolean value that determines whether the control is displayed.
   *
   * @default
   * {
   *   leave: true,
   *   microphone: true,
   *   screenShare: true,
   *   camera: true,
   *   chat: true,
   * }
   */
  controls?: AgentControlBarControls;
  /**
   * Whether to save user choices.
   * @default true
   */
  saveUserChoices?: boolean;
  /**
   * Whether the agent is connected to a session.
   * @default false
   */
  isConnected?: boolean;
  /**
   * Whether the chat input interface is open.
   * @default false
   */
  isChatOpen?: boolean;
  /**
   * The callback for when the user disconnects.
   */
  onDisconnect?: () => void;
  /**
   * The callback for when the chat is opened or closed.
   */
  onIsChatOpenChange?: (open: boolean) => void;
  /**
   * The callback for when a device error occurs.
   */
  onDeviceError?: (error: { source: Track.Source; error: Error }) => void;
}

/**
 * A control bar specifically designed for voice assistant interfaces.
 * Provides controls for microphone, camera, screen share, chat, and disconnect.
 * Includes an expandable chat input for text-based interaction with the agent.
 *
 * @extends ComponentProps<'div'>
 *
 * @example
 * ```tsx
 * <AgentControlBar
 *   variant="livekit"
 *   isConnected={true}
 *   onDisconnect={() => handleDisconnect()}
 *   controls={{
 *     microphone: true,
 *     camera: true,
 *     screenShare: false,
 *     chat: true,
 *     leave: true,
 *   }}
 * />
 * ```
 */
export function AgentControlBar({
  variant = 'default',
  controls,
  isChatOpen = false,
  isConnected = false,
  saveUserChoices = true,
  onDisconnect,
  onDeviceError,
  onIsChatOpenChange,
  className,
  ...props
}: AgentControlBarProps & ComponentProps<'div'>) {
  const { send } = useChat();
  const publishPermissions = usePublishPermissions();
  const [isChatOpenUncontrolled, setIsChatOpenUncontrolled] = useState(isChatOpen);
  const {
    micTrackRef, // Sync'ed with hook
    cameraToggle,
    microphoneToggle,
    screenShareToggle,
    handleAudioDeviceChange,
    handleVideoDeviceChange,
    handleMicrophoneDeviceSelectError,
    handleCameraDeviceSelectError,
  } = useInputControls({ onDeviceError, saveUserChoices });

  // --- Lógica de Auto-Hide Inteligente ---
  const [isVisible, setIsVisible] = useState(true);
  const [isLocked, setIsLocked] = useState(false); // Novo estado para travar a barra
  const hideTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const handleMouseMove = () => {
      setIsVisible(true);
      if (hideTimeoutRef.current) clearTimeout(hideTimeoutRef.current);

      // Não oculta se: Chat aberto OU Barra travada
      if (!isChatOpen && !isChatOpenUncontrolled && !isLocked) {
        hideTimeoutRef.current = setTimeout(() => {
          setIsVisible(false);
        }, 3000); // 3 segundos de inatividade
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    handleMouseMove(); // Inicia o timer

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      if (hideTimeoutRef.current) clearTimeout(hideTimeoutRef.current);
    };
  }, [isChatOpen, isChatOpenUncontrolled, isLocked]);

  const handleSendMessage = async (message: string) => {
    await send(message);
  };

  const visibleControls = {
    leave: controls?.leave ?? true,
    microphone: controls?.microphone ?? publishPermissions.microphone,
    screenShare: controls?.screenShare ?? publishPermissions.screenShare,
    camera: controls?.camera ?? publishPermissions.camera,
    chat: controls?.chat ?? publishPermissions.data,
  };

  const isEmpty = Object.values(visibleControls).every((value) => !value);

  if (isEmpty) {
    console.warn('AgentControlBar: `visibleControls` contains only false values.');
    return null;
  }

  return (
    <motion.div
      initial={false}
      animate={{
        y: isVisible || isChatOpen || isChatOpenUncontrolled || isLocked ? 0 : 20,
        opacity: isVisible || isChatOpen || isChatOpenUncontrolled || isLocked ? 1 : 0
      }}
      transition={{ duration: 0.4, ease: "easeInOut" }}
      className={cn(
        "relative mx-auto w-fit min-w-[300px] z-50",
        !isVisible && !isChatOpen && !isChatOpenUncontrolled && !isLocked && "pointer-events-none transition-all"
      )}
      onMouseEnter={() => {
        setIsVisible(true);
        if (hideTimeoutRef.current) clearTimeout(hideTimeoutRef.current);
      }}
    >
      <div
        aria-label="Controles do assistente de voz"
        className={cn(
          'backdrop-blur-xl bg-black/40 border-[#1da3b9]/20 flex flex-col border p-3 shadow-2xl shadow-[#1da3b9]/5',
          variant === 'livekit' ? 'rounded-[31px]' : 'rounded-xl',
          className
        )}
        {...props}
      >
        <motion.div
          {...MOTION_PROPS}
          inert={!(isChatOpen || isChatOpenUncontrolled)}
          animate={isChatOpen || isChatOpenUncontrolled ? 'visible' : 'hidden'}
          className="border-input/50 flex w-full items-start overflow-hidden border-b"
        >
          <AgentChatInput
            chatOpen={isChatOpen || isChatOpenUncontrolled}
            onSend={handleSendMessage}
            className={cn(variant === 'livekit' && '[&_button]:rounded-full')}
          />
        </motion.div>

        <div className="flex gap-1">
          <div className="flex grow gap-1 items-center">
            {/* Botão Discreto de Trava (Pin) */}
            <button
              onClick={() => setIsLocked(!isLocked)}
              className={cn(
                "p-2 rounded-full transition-all duration-300 mr-2",
                isLocked ? "text-[#43d9f0] bg-[#1da3b9]/20" : "text-white/40 hover:text-white/60 hover:bg-white/5"
              )}
              title={isLocked ? "Auto-hide desativado" : "Ativar auto-hide"}
            >
              <motion.div
                animate={{ rotate: isLocked ? 45 : 0 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <Pin className="size-4" />
              </motion.div>
            </button>

            {/* Toggle Microphone */}
            {visibleControls.microphone && (
              <AgentTrackControl
                variant={variant === 'outline' ? 'outline' : 'default'}
                kind="audioinput"
                aria-label="Alternar microfone"
                source={Track.Source.Microphone}
                pressed={microphoneToggle.enabled}
                disabled={microphoneToggle.pending}
                audioTrack={micTrackRef}
                onPressedChange={microphoneToggle.toggle}
                onActiveDeviceChange={handleAudioDeviceChange}
                onMediaDeviceError={handleMicrophoneDeviceSelectError}
                className={cn(
                  variant === 'livekit' && [
                    TOGGLE_VARIANT_1,
                    'rounded-full [&_button:first-child]:rounded-l-full [&_button:last-child]:rounded-r-full',
                  ]
                )}
              />
            )}

            {/* Toggle Camera */}
            {visibleControls.camera && (
              <AgentTrackControl
                variant={variant === 'outline' ? 'outline' : 'default'}
                kind="videoinput"
                aria-label="Alternar câmera"
                source={Track.Source.Camera}
                pressed={cameraToggle.enabled}
                pending={cameraToggle.pending}
                disabled={cameraToggle.pending}
                onPressedChange={cameraToggle.toggle}
                onMediaDeviceError={handleCameraDeviceSelectError}
                onActiveDeviceChange={handleVideoDeviceChange}
                className={cn(
                  variant === 'livekit' && [
                    TOGGLE_VARIANT_1,
                    'rounded-full [&_button:first-child]:rounded-l-full [&_button:last-child]:rounded-r-full',
                  ]
                )}
              />
            )}

            {/* Toggle Screen Share */}
            {visibleControls.screenShare && (
              <AgentTrackToggle
                variant={variant === 'outline' ? 'outline' : 'default'}
                aria-label="Alternar compartilhamento de tela"
                source={Track.Source.ScreenShare}
                pressed={screenShareToggle.enabled}
                disabled={screenShareToggle.pending}
                onPressedChange={screenShareToggle.toggle}
                className={cn(variant === 'livekit' && [TOGGLE_VARIANT_2, 'rounded-full'])}
              />
            )}

            {/* Toggle Transcript */}
            {visibleControls.chat && (
              <Toggle
                variant={variant === 'outline' ? 'outline' : 'default'}
                pressed={isChatOpen || isChatOpenUncontrolled}
                aria-label="Alternar transcrição"
                onPressedChange={(state: boolean) => {
                  if (!onIsChatOpenChange) setIsChatOpenUncontrolled(state);
                  else onIsChatOpenChange(state);
                }}
                className={agentTrackToggleVariants({
                  variant: variant === 'outline' ? 'outline' : 'default',
                  className: cn(variant === 'livekit' && [TOGGLE_VARIANT_2, 'rounded-full']),
                })}
              >
                <MessageSquareTextIcon />
              </Toggle>
            )}
          </div>

          {/* Disconnect */}
          {visibleControls.leave && (
            <AgentDisconnectButton
              onClick={onDisconnect}
              disabled={!isConnected}
              className={cn(
                variant === 'livekit' &&
                'bg-destructive/10 dark:bg-destructive/10 text-destructive hover:bg-destructive/20 dark:hover:bg-destructive/20 focus:bg-destructive/20 focus-visible:ring-destructive/20 dark:focus-visible:ring-destructive/4 rounded-full font-mono text-xs font-bold tracking-wider'
              )}
            >
              <span className="hidden md:inline">ENCERRAR CHAMADA</span>
              <span className="inline md:hidden">SAIR</span>
            </AgentDisconnectButton>
          )}
        </div>
      </div>
    </motion.div>
  );
}
