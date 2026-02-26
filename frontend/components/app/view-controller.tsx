'use client';

import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { SessionView } from '@/components/app/session-view';
import { WelcomeView } from '@/components/app/welcome-view';
import type { ReconnectState } from '@/lib/types/realtime';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionSessionView = motion.create(SessionView);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: {
      opacity: 1,
    },
    hidden: {
      opacity: 0,
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.5,
    ease: 'linear' as const,
  },
};

interface ViewControllerProps {
  appConfig: AppConfig;
  reconnectState: ReconnectState;
}

export function ViewController({ appConfig, reconnectState }: ViewControllerProps) {
  const { isConnected, start } = useSessionContext();
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    if (isConnected) setIsActive(true);
  }, [isConnected]);

  const handleStart = async () => {
    setIsActive(true);
    await start();
  };

  const handleDisconnect = () => {
    setIsActive(false);
  };

  return (
    <AnimatePresence mode="wait">
      {!isActive && !isConnected && (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          startButtonText={appConfig.startButtonText}
          onStartCall={handleStart}
        />
      )}

      {(isActive || isConnected) && (
        <MotionSessionView
          key="session-view"
          {...VIEW_MOTION_PROPS}
          appConfig={appConfig}
          reconnectState={reconnectState}
          onManualDisconnect={handleDisconnect}
        />
      )}
    </AnimatePresence>
  );
}
