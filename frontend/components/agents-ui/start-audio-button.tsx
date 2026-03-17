import { type ComponentProps, type MouseEvent, type PointerEvent, useRef } from 'react';
import { Room } from 'livekit-client';
import { useEnsureRoom, useStartAudio } from '@livekit/components-react';
import { Button } from '@/components/ui/button';

/**
 * Props for the StartAudioButton component.
 */
export interface StartAudioButtonProps extends ComponentProps<'button'> {
  /**
   * The size of the button.
   * @defaultValue 'default'
   */
  size?: 'default' | 'sm' | 'lg' | 'icon' | 'icon-sm' | 'icon-lg';
  /**
   * The variant of the button.
   * @defaultValue 'default'
   */
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  /**
   * The LiveKit room instance. If not provided, uses the room from context.
   */
  room?: Room;
  /**
   * The label text to display on the button.
   */
  label: string;
}

/**
 * A button that allows users to start audio playback.
 * Required for browsers that block autoplay of audio.
 * Only renders when audio playback is blocked.
 *
 * @extends ComponentProps<'button'>
 *
 * @example
 * ```tsx
 * <StartAudioButton label="Click to allow audio playback" />
 * ```
 */
export function StartAudioButton({
  size = 'default',
  variant = 'default',
  label,
  room,
  ...props
}: StartAudioButtonProps) {
  const roomEnsured = useEnsureRoom(room);
  const { mergedProps } = useStartAudio({ room: roomEnsured, props });
  const holdTimerRef = useRef<number | null>(null);
  const holdTriggeredRef = useRef(false);
  const suppressClickRef = useRef(false);

  const clearHoldTimer = () => {
    if (holdTimerRef.current) {
      window.clearTimeout(holdTimerRef.current);
      holdTimerRef.current = null;
    }
  };

  const dispatchVoiceEvent = (type: string, detail: Record<string, unknown>) => {
    if (typeof window === 'undefined') {
      return;
    }
    window.dispatchEvent(new CustomEvent(type, { detail }));
  };

  const handlePointerDown = (event: PointerEvent<HTMLButtonElement>) => {
    const mergedOnPointerDown = mergedProps.onPointerDown as
      | ((event: PointerEvent<HTMLButtonElement>) => void)
      | undefined;
    mergedOnPointerDown?.(event);
    if (typeof window === 'undefined') {
      return;
    }
    clearHoldTimer();
    holdTriggeredRef.current = false;
    holdTimerRef.current = window.setTimeout(() => {
      holdTriggeredRef.current = true;
      suppressClickRef.current = true;
      dispatchVoiceEvent('jarvez:voice-activation', {
        mode: 'push_to_talk',
        hold: true,
      });
    }, 280);
  };

  const handlePointerUp = (event: PointerEvent<HTMLButtonElement>) => {
    const mergedOnPointerUp = mergedProps.onPointerUp as
      | ((event: PointerEvent<HTMLButtonElement>) => void)
      | undefined;
    mergedOnPointerUp?.(event);
    clearHoldTimer();
    if (!holdTriggeredRef.current) {
      return;
    }
    dispatchVoiceEvent('jarvez:voice-deactivation', {
      mode: 'push_to_talk',
      hold: true,
    });
    holdTriggeredRef.current = false;
  };

  const handlePointerCancel = (event: PointerEvent<HTMLButtonElement>) => {
    const mergedOnPointerCancel = mergedProps.onPointerCancel as
      | ((event: PointerEvent<HTMLButtonElement>) => void)
      | undefined;
    mergedOnPointerCancel?.(event);
    clearHoldTimer();
    if (!holdTriggeredRef.current) {
      return;
    }
    dispatchVoiceEvent('jarvez:voice-deactivation', {
      mode: 'push_to_talk',
      hold: true,
    });
    holdTriggeredRef.current = false;
  };

  const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
    const mergedOnClick = mergedProps.onClick as
      | ((event: MouseEvent<HTMLButtonElement>) => void)
      | undefined;
    mergedOnClick?.(event);
    if (suppressClickRef.current) {
      suppressClickRef.current = false;
      event.preventDefault();
      return;
    }
    if (!event.defaultPrevented && typeof window !== 'undefined') {
      dispatchVoiceEvent('jarvez:voice-toggle', { mode: 'button' });
    }
  };

  return (
    <Button
      size={size}
      variant={variant}
      {...props}
      {...mergedProps}
      onClick={handleClick}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerCancel}
      onPointerLeave={handlePointerCancel}
    >
      {label}
    </Button>
  );
}
