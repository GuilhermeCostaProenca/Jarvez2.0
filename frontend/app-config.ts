export interface AppConfig {
  pageTitle: string;
  pageDescription: string;
  companyName: string;

  supportsChatInput: boolean;
  supportsVideoInput: boolean;
  supportsScreenShare: boolean;
  isPreConnectBufferEnabled: boolean;

  logo: string;
  startButtonText: string;
  accent?: string;
  logoDark?: string;
  accentDark?: string;
  audioVisualizerType?: 'bar' | 'aura' | 'wave' | 'grid' | 'radial';
  audioVisualizerColor?: string;
  audioVisualizerAuraColorShift?: number;
  audioVisualizerWaveLineWidth?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerBarCount?: number;

  // agent dispatch configuration
  agentName?: string;

  // LiveKit Cloud Sandbox configuration
  sandboxId?: string;
}

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'Jarvez',
  pageTitle: 'Jarvez - Assistente de Voz',
  pageDescription: 'Seu assistente de voz pessoal.',

  supportsChatInput: true,
  supportsVideoInput: true,
  supportsScreenShare: true,
  isPreConnectBufferEnabled: true,

  logo: '/jarvez-logo.svg',
  accent: '#0f766e',
  logoDark: '/jarvez-logo-dark.svg',
  accentDark: '#14b8a6',
  audioVisualizerType: 'bar',
  audioVisualizerColor: '#43d9f0',
  audioVisualizerAuraColorShift: 15,
  audioVisualizerWaveLineWidth: 3,
  audioVisualizerGridRowCount: 9,
  audioVisualizerGridColumnCount: 9,
  audioVisualizerRadialBarCount: 25,
  audioVisualizerRadialRadius: 12,
  audioVisualizerBarCount: 12,
  startButtonText: 'Iniciar Chamada',

  // agent dispatch configuration
  agentName: process.env.AGENT_NAME ?? undefined,

  // LiveKit Cloud Sandbox configuration
  sandboxId: undefined,
};
