import { useEffect, useMemo, useRef, useState } from 'react';
import { toast } from 'sonner';

type AwarenessContext = 'coding' | 'study' | 'watching_video' | 'browsing' | 'idle';

const CONTEXT_COOLDOWN_MS = 5 * 60 * 1000;
const IDLE_THRESHOLD_MS = 60 * 1000;

function detectContext(idle: boolean): AwarenessContext {
  if (idle || document.visibilityState !== 'visible') {
    return 'idle';
  }

  const title = document.title.toLowerCase();
  const path = window.location.pathname.toLowerCase();
  const href = window.location.href.toLowerCase();

  if (title.includes('youtube') || href.includes('youtube') || href.includes('watch')) {
    return 'watching_video';
  }
  if (title.includes('vscode') || title.includes('code') || path.includes('code')) {
    return 'coding';
  }
  if (
    title.includes('study') ||
    title.includes('aula') ||
    title.includes('curso') ||
    path.includes('study')
  ) {
    return 'study';
  }
  return 'browsing';
}

function proactiveMessage(context: AwarenessContext): string | null {
  if (context === 'coding') return 'Contexto coding detectado. Quer revisar TODOs e prioridades?';
  if (context === 'study')
    return 'Contexto de estudo detectado. Posso montar um mini plano de foco.';
  if (context === 'watching_video')
    return 'Video detectado. Quer um resumo rapido dos pontos principais depois?';
  return null;
}

export function useAwarenessProactive() {
  const [silentMode, setSilentMode] = useState(false);
  const [context, setContext] = useState<AwarenessContext>('browsing');
  const [idle, setIdle] = useState(false);
  const lastActivityRef = useRef<number>(Date.now());
  const contextCooldownRef = useRef<Record<AwarenessContext, number>>({
    coding: 0,
    study: 0,
    watching_video: 0,
    browsing: 0,
    idle: 0,
  });

  useEffect(() => {
    const onUserActivity = () => {
      lastActivityRef.current = Date.now();
      if (idle) setIdle(false);
    };

    const interval = window.setInterval(() => {
      const isIdleNow = Date.now() - lastActivityRef.current > IDLE_THRESHOLD_MS;
      if (isIdleNow !== idle) setIdle(isIdleNow);
    }, 2_000);

    window.addEventListener('mousemove', onUserActivity);
    window.addEventListener('keydown', onUserActivity);
    window.addEventListener('click', onUserActivity);
    window.addEventListener('scroll', onUserActivity);
    document.addEventListener('visibilitychange', onUserActivity);

    return () => {
      window.clearInterval(interval);
      window.removeEventListener('mousemove', onUserActivity);
      window.removeEventListener('keydown', onUserActivity);
      window.removeEventListener('click', onUserActivity);
      window.removeEventListener('scroll', onUserActivity);
      document.removeEventListener('visibilitychange', onUserActivity);
    };
  }, [idle]);

  useEffect(() => {
    const nextContext = detectContext(idle);
    if (nextContext !== context) {
      setContext(nextContext);
    }
  }, [context, idle]);

  useEffect(() => {
    if (silentMode) return;

    const message = proactiveMessage(context);
    if (!message) return;

    const now = Date.now();
    const last = contextCooldownRef.current[context];
    if (now - last < CONTEXT_COOLDOWN_MS) return;

    contextCooldownRef.current[context] = now;
    toast.message(message);
  }, [context, silentMode]);

  const contextLabel = useMemo(() => {
    if (context === 'coding') return 'coding';
    if (context === 'study') return 'study';
    if (context === 'watching_video') return 'video';
    if (context === 'idle') return 'idle';
    return 'browsing';
  }, [context]);

  return {
    context,
    contextLabel,
    idle,
    silentMode,
    setSilentMode,
  };
}
