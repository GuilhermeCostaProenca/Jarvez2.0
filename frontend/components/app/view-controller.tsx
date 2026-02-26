'use client';

import { AnimatePresence, motion } from 'motion/react';
import { useState, useEffect } from 'react';
import { useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { SessionView } from '@/components/app/session-view';
import { WelcomeView } from '@/components/app/welcome-view';

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
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const { isConnected, start } = useSessionContext();
  const [isActive, setIsActive] = useState(false);

  // Ativa a sessão quando a conexão é estabelecida ou quando start é chamado
  useEffect(() => {
    if (isConnected) setIsActive(true);
  }, [isConnected]);

  const handleStart = async (opts?: any) => {
    setIsActive(true);
    await start(opts);
  };

  const handleDisconnect = () => {
    setIsActive(false);
  };

  return (
    <AnimatePresence mode="wait">
      {/* Welcome view */}
      {!isActive && !isConnected && (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          startButtonText={appConfig.startButtonText}
          onStartCall={handleStart}
        />
      )}
      {/* Session view */}
      {(isActive || isConnected) && (
        <MotionSessionView
          key="session-view"
          {...VIEW_MOTION_PROPS}
          appConfig={appConfig}
          onManualDisconnect={handleDisconnect}
        />
      )}
    </AnimatePresence>
  );
}
