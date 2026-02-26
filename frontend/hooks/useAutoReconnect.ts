import { useCallback, useEffect, useRef, useState } from 'react';
import { RoomEvent } from 'livekit-client';
import type { ConnectionState, ReconnectState, RoomSessionState } from '@/lib/types/realtime';

const MAX_ATTEMPTS = 5;
const BASE_DELAY_MS = 1000;
const MAX_DELAY_MS = 10000;

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function useAutoReconnect(session: RoomSessionState): ReconnectState {
  const { room, start, isConnected } = session;

  const [attempt, setAttempt] = useState(0);
  const [connectionState, setConnectionState] = useState<ConnectionState>(
    isConnected ? 'connected' : 'disconnected'
  );

  const reconnectingRef = useRef(false);
  const mountedRef = useRef(true);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const reconnectNow = useCallback(async () => {
    if (reconnectingRef.current) return;

    reconnectingRef.current = true;
    if (mountedRef.current) {
      setConnectionState('reconnecting');
      setAttempt(0);
    }

    for (let currentAttempt = 1; currentAttempt <= MAX_ATTEMPTS; currentAttempt++) {
      if (mountedRef.current) {
        setAttempt(currentAttempt);
      }

      try {
        await start();
        if (mountedRef.current) {
          setConnectionState('connected');
          setAttempt(0);
        }
        reconnectingRef.current = false;
        return;
      } catch (error) {
        if (currentAttempt === MAX_ATTEMPTS) {
          if (mountedRef.current) {
            setConnectionState('disconnected');
          }
          reconnectingRef.current = false;
          return;
        }

        const delay = Math.min(BASE_DELAY_MS * 2 ** (currentAttempt - 1), MAX_DELAY_MS);
        await sleep(delay);
        console.warn(`Reconnect attempt ${currentAttempt} failed:`, error);
      }
    }

    reconnectingRef.current = false;
  }, [start]);

  useEffect(() => {
    if (isConnected) {
      setConnectionState('connected');
      setAttempt(0);
      reconnectingRef.current = false;
    }
  }, [isConnected]);

  useEffect(() => {
    if (!room) return;

    const handleDisconnected = () => {
      if (mountedRef.current) {
        setConnectionState('disconnected');
      }
      void reconnectNow();
    };

    room.on(RoomEvent.Disconnected, handleDisconnected);
    return () => {
      room.off(RoomEvent.Disconnected, handleDisconnected);
    };
  }, [room, reconnectNow]);

  return {
    connectionState,
    attempt,
    maxAttempts: MAX_ATTEMPTS,
    isReconnecting: connectionState === 'reconnecting',
    reconnectNow,
  };
}
