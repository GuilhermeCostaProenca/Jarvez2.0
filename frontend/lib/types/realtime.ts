import type { UseSessionReturn } from '@livekit/components-react';

export type ParticipantIdentity = string;

export type ConnectionState = 'connected' | 'disconnected' | 'reconnecting';

export type RoomSessionState = UseSessionReturn;

export interface ToolCallEvent {
  name: string;
  status: 'started' | 'completed' | 'failed' | 'confirmation_required';
  timestamp: number;
  message?: string;
}

export interface ActionResultPayload {
  success: boolean;
  message: string;
  data?: {
    confirmation_required?: boolean;
    confirmation_token?: string;
    expires_in?: number;
    action_name?: string;
    params?: Record<string, unknown>;
    authentication_required?: boolean;
    security_status?: {
      authenticated?: boolean;
      identity_bound?: boolean;
      expires_in?: number;
      auth_method?: 'pin' | 'passphrase' | 'voice' | 'voice+pin' | string;
      step_up_required?: boolean;
    };
    auth_method?: 'pin' | 'passphrase' | 'voice' | 'voice+pin' | string;
    voice_score?: number;
    step_up_required?: boolean;
    private_access_granted?: boolean;
  };
  error?: string;
}

export interface PendingActionConfirmation {
  token: string;
  message: string;
  expiresIn: number;
  actionName?: string;
  params?: Record<string, unknown>;
}

export interface ActionExecutionEvent extends ToolCallEvent {
  callId: string;
  actionName: string;
}

export interface SecuritySessionState {
  authenticated: boolean;
  identityBound: boolean;
  expiresIn: number;
  authMethod?: string;
  stepUpRequired: boolean;
  voiceScore?: number;
}

export interface ReconnectState {
  connectionState: ConnectionState;
  attempt: number;
  maxAttempts: number;
  isReconnecting: boolean;
  reconnectNow: () => Promise<void>;
}
