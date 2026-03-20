import type { SecuritySessionState } from '@/lib/types/realtime';

export function getSecurityAccessChip(session: SecuritySessionState): {
  label: string;
  className: string;
} {
  const status = session.authState?.status ?? (session.authenticated ? 'recovery_mode' : 'locked');

  if (status === 'unlock_in_progress') {
    return {
      label: 'Destravando...',
      className: 'border-cyan-300/30 bg-cyan-500/10 text-cyan-100',
    };
  }
  if (status === 'unlocked_by_voice') {
    return {
      label: `Desbloqueado por voz${session.authState?.profile_name ? `: ${session.authState.profile_name}` : ''}`,
      className: 'border-emerald-300/30 bg-emerald-500/10 text-emerald-100',
    };
  }
  if (status === 'unlocked_by_face') {
    return {
      label: `Desbloqueado por rosto${session.authState?.profile_name ? `: ${session.authState.profile_name}` : ''}`,
      className: 'border-emerald-300/30 bg-emerald-500/10 text-emerald-100',
    };
  }
  if (status === 'unlocked_combined') {
    return {
      label: `Desbloqueado${session.authState?.profile_name ? `: ${session.authState.profile_name}` : ''}`,
      className: 'border-emerald-300/30 bg-emerald-500/10 text-emerald-100',
    };
  }
  if (status === 'recovery_mode') {
    return {
      label: 'Recovery local',
      className: 'border-amber-300/30 bg-amber-500/10 text-amber-100',
    };
  }
  if (session.stepUpRequired) {
    return {
      label: 'Step-up pendente',
      className: 'border-amber-300/30 bg-amber-500/10 text-amber-100',
    };
  }
  return {
    label: 'Bloqueado',
    className: 'border-white/10 bg-white/5 text-white/70',
  };
}

export function getRecognizedIdentityChip(session: SecuritySessionState): {
  label: string;
  className: string;
} | null {
  const name = session.recognizedIdentity?.name?.trim();
  if (!name || name.toLowerCase() === 'unknown') {
    return null;
  }
  const source = session.recognizedIdentity?.source ?? 'voice';
  return {
    label:
      source === 'face'
        ? `Rosto: ${name}`
        : source === 'voice+face'
          ? `Identidade: ${name}`
          : `Voz: ${name}`,
    className: 'border-fuchsia-300/30 bg-fuchsia-500/10 text-fuchsia-100',
  };
}

export function getUnlockActionAvailability(session: SecuritySessionState): {
  canUnlockWithVoice: boolean;
  canUnlockWithFace: boolean;
  recoveryAvailable: boolean;
  needsEnrollment: boolean;
} {
  const recommended = session.unlockOptions?.recommended_unlock_actions ?? [];
  const canUnlockWithVoice = recommended.includes('unlock_with_voice');
  const canUnlockWithFace = recommended.includes('unlock_with_face');
  return {
    canUnlockWithVoice,
    canUnlockWithFace,
    recoveryAvailable: session.unlockOptions?.recovery_available === true,
    needsEnrollment: !canUnlockWithVoice && !canUnlockWithFace,
  };
}
