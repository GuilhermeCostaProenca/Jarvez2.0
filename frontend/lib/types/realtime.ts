import type { UseSessionReturn } from '@livekit/components-react';

export type ParticipantIdentity = string;

export type ConnectionState = 'connected' | 'disconnected' | 'reconnecting';

export type RoomSessionState = UseSessionReturn;

export interface ToolCallEvent {
  name: string;
  status: 'started' | 'completed' | 'failed';
  timestamp: number;
}

export interface ReconnectState {
  connectionState: ConnectionState;
  attempt: number;
  maxAttempts: number;
  isReconnecting: boolean;
  reconnectNow: () => Promise<void>;
}
