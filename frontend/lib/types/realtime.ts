import type { UseSessionReturn } from '@livekit/components-react';

export type ParticipantIdentity = string;

export type ConnectionState = 'connected' | 'disconnected' | 'reconnecting';

export type RoomSessionState = UseSessionReturn;
export type VoiceInteractivityStateValue =
  | 'idle'
  | 'listening'
  | 'transcribing'
  | 'thinking'
  | 'confirming'
  | 'executing'
  | 'background'
  | 'speaking'
  | 'error';

export interface VoiceInteractivityState {
  state: VoiceInteractivityStateValue;
  source?: 'backend' | 'client' | string;
  activation_mode?:
    | 'button'
    | 'wake_word'
    | 'push_to_talk'
    | 'voice'
    | 'system'
    | 'unknown'
    | string;
  raw_client_state?: string;
  display_message?: string;
  spoken_message?: string;
  action_name?: string;
  trace_id?: string;
  error_code?: string;
  can_retry?: boolean;
  wake_word_available?: boolean;
  updated_at?: string;
}

export interface RecognizedIdentity {
  name?: string;
  confidence?: number;
  source?: 'voice' | 'face' | 'voice+face' | string;
  updated_at?: string;
}

export interface ToolCallEvent {
  name: string;
  status: 'started' | 'completed' | 'failed' | 'confirmation_required';
  timestamp: number;
  message?: string;
}

export interface ActionResultPayload {
  success: boolean;
  message: string;
  trace_id?: string;
  risk?: 'R0' | 'R1' | 'R2' | 'R3' | string;
  policy_decision?:
    | 'allow'
    | 'allow_with_log'
    | 'allow_with_guardrail'
    | 'deny'
    | 'require_confirmation'
    | string;
  evidence?: ActionEvidence;
  fallback_used?: boolean;
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
    recognized_identity?: RecognizedIdentity | null;
    persona_mode?: string;
    current_persona_mode?: string;
    applied_persona_mode?: string;
    persona_profile?: {
      label?: string;
      style?: string;
      color_hex?: string;
      voice_hint?: string;
    };
    active_character?: {
      name?: string;
      source?: string;
      summary?: string;
      activated_at?: string;
      page_id?: string;
      page_title?: string;
      section_name?: string;
    } | null;
    active_character_name?: string | null;
    active_character_cleared?: boolean;
    active_project?: {
      project_id?: string;
      name?: string;
      root_path?: string;
      aliases?: string[];
      selected_at?: string;
      selection_reason?: string;
      index_status?: string;
    } | null;
    active_project_name?: string | null;
    coding_mode?: 'default' | 'coding' | string;
    worker_status?: {
      success?: boolean;
      message?: string;
    };
    worker_info?: Record<string, unknown>;
    project_analysis?: {
      summary?: string;
      files?: string[];
      risks?: string[];
      validation_commands?: string[][];
      patch_preview?: string | null;
    };
    proposed_code_change?: {
      summary?: string;
      files?: string[];
      risks?: string[];
      validation_commands?: string[][];
      patch_preview?: string | null;
    };
    git_status?: {
      returncode?: number;
      stdout?: string;
      stderr?: string;
      success?: boolean;
    };
    git_diff_summary?: {
      summary?: string;
      files?: string[];
      risks?: string[];
      validation_commands?: string[][];
      patch_preview?: string | null;
    };
    command_execution?: {
      returncode?: number;
      stdout?: string;
      stderr?: string;
      success?: boolean;
      command_line?: string[];
    };
    codex_task?: CodexTaskState | null;
    codex_event?: CodexTaskEvent | null;
    codex_history?: CodexTaskHistoryEntry[];
    browser_task?: BrowserTaskState | null;
    workflow_state?: WorkflowState | null;
    automation_state?: AutomationState | null;
    whatsapp_channel?: {
      mode?: 'mcp' | 'legacy_v1' | 'disabled' | string;
      legacy_enabled?: boolean;
      mcp?: {
        enabled?: boolean;
        connected?: boolean;
        detail?: string | null;
        url_configured?: boolean;
        history_available?: boolean;
        messages_db_path?: string | null;
      };
      messages?: {
        total?: number;
        inbound_total?: number;
        outbound_total?: number;
        last_inbound_at?: string | null;
        last_outbound_at?: string | null;
      };
    };
    web_dashboard?: {
      query?: string;
      summary?: string;
      generated_at?: string;
      dashboard_url?: string;
      dashboard_opened?: boolean;
      images?: string[];
      results?: Array<{
        title?: string;
        url?: string;
        domain?: string;
        snippet?: string;
        page_title?: string;
        page_description?: string;
        image_url?: string;
      }>;
    };
    web_dashboard_schedule?: {
      id?: string;
      query?: string;
      cadence?: 'daily' | string;
      time_of_day?: string;
      prompt?: string;
      last_run_on?: string;
    };
    skills?: Array<{
      id?: string;
      name?: string;
      description?: string;
      path?: string;
      tags?: string[];
      source?: string;
      updated_at?: string;
    }>;
    skills_total?: number;
    skill_document?: {
      skill?: {
        id?: string;
        name?: string;
        description?: string;
        path?: string;
        tags?: string[];
        source?: string;
        updated_at?: string;
      };
      content?: string;
      excerpt?: string;
    };
    orchestration?: {
      request?: string;
      response_preview?: string;
      task_plan?: {
        task_type?: string;
        steps?: string[];
        assumptions?: string[];
        generated_at?: string;
      };
      model_route?: ModelRouteDecision;
    };
    model_route?: ModelRouteDecision;
    subagent_state?: SubagentState;
    subagent_states?: SubagentState[];
    policy?: PolicyEvent;
    autonomy_notice?: {
      active?: boolean;
      level?: 'info' | 'warning' | 'critical' | string;
      title?: string;
      message?: string;
      domain?: string;
      scenario?: string;
      decision?: string;
      signature?: string;
      spoken_message?: string;
      spoken_channel?: 'agent_audio' | 'browser_tts' | string;
      trace_id?: string;
    };
    autonomy_mode?: string;
    kill_switch?: {
      global_enabled?: boolean;
      global_reason?: string;
      domains?: Record<string, string>;
      updated_at?: string;
    };
    risk_matrix?: Array<{
      action_name?: string;
      risk?: string;
      requires_confirmation?: boolean;
      requires_auth?: boolean;
      expose_to_model?: boolean;
      domain?: string;
      domain_trust_score?: number;
    }>;
    domain_trust?: Array<Record<string, unknown>>;
    eval_scenarios?: Array<{
      scenario_id?: string;
      name?: string;
      prompt?: string;
      expected?: string[];
    }>;
    eval_scenarios_total?: number;
    eval_baseline_summary?: {
      total?: number;
      passed?: number;
      failed?: number;
      score?: number;
      ran_at?: string;
    };
    eval_baseline_results?: Array<{
      scenario_id?: string;
      name?: string;
      task_type?: string;
      passed?: boolean;
      response_preview?: string;
      route?: ModelRouteDecision;
    }>;
    eval_metrics?: Array<Record<string, unknown>>;
    eval_metrics_updated_at?: string;
    eval_metrics_summary?: {
      total_actions?: number;
      providers?: Record<string, { total?: number; success?: number; failed?: number }>;
      risk_tiers?: Record<string, { total?: number; success?: number; failed?: number }>;
      trust_drift?: {
        active_total?: number;
        inactive_total?: number;
        by_domain?: Record<string, { total?: number; success?: number; failed?: number }>;
      };
      autonomy_notice?: {
        active_total?: number;
        inactive_total?: number;
        by_level?: Record<string, { total?: number; success?: number; failed?: number }>;
        by_channel?: Record<string, { total?: number; success?: number; failed?: number }>;
        by_domain?: Record<string, { total?: number; success?: number; failed?: number }>;
        unconfirmed_total?: number;
        unconfirmed_by_domain?: Record<string, number>;
      };
    };
    slo_report?: {
      total_actions?: number;
      latency?: {
        overall_p95_ms?: number;
        fallback_p95_ms?: number;
      };
      reliability?: {
        low_risk_success_rate?: number;
        false_success_proxy_rate?: number;
        trust_drift_active_rate?: number;
        autonomy_notice_agent_audio_rate?: number;
        autonomy_notice_browser_tts_rate?: number;
        autonomy_notice_unconfirmed_rate?: number;
      };
      targets?: {
        false_success_rate_max?: number;
        low_risk_success_rate_min?: number;
        fallback_p95_ms_max?: number;
      };
      slo_pass?: {
        false_success?: boolean;
        low_risk_success?: boolean;
        fallback_p95?: boolean;
      };
      by_provider?: Record<
        string,
        { total?: number; success?: number; failed?: number; p95_ms?: number }
      >;
      by_action?: Record<
        string,
        { total?: number; success?: number; failed?: number; p95_ms?: number }
      >;
    };
    providers_health?: Array<{
      provider?: string;
      configured?: boolean;
      supports_tools?: boolean;
      supports_realtime?: boolean;
      status?: string;
      ping_ok?: boolean;
      ping_preview?: string;
      error?: string;
    }>;
    feature_flags?: {
      values?: Record<string, boolean>;
      overrides?: Record<string, boolean>;
    };
    canary_state?: CanaryState;
    ops_incident_snapshot?: OpsIncidentSnapshot;
    ops_playbook_report?: OpsPlaybookReport;
    ops_auto_remediation?: OpsAutoRemediation;
    ops_canary_promotion?: OpsCanaryPromotion;
    ops_control_tick?: OpsControlTick;
  };
  error?: string;
}

export interface ActionEvidence {
  provider: string;
  request_id?: string;
  raw_status?: number;
  executed_at: string;
  started_at?: string;
}

export interface ModelRouteDecision {
  task_type?: string;
  risk?: string;
  primary_provider?: string;
  fallback_provider?: string;
  used_provider?: string;
  fallback_used?: boolean;
  reason?: string;
  generated_at?: string;
}

export interface PolicyEvent {
  action_name?: string;
  autonomy_mode?: string;
  risk?: string;
  decision?: string;
  reason?: string;
  domain?: string;
  trust_drift_active?: boolean;
  trust_drift?: Record<string, unknown> | null;
  source?: 'backend' | 'local' | 'synthetic';
  event_type?: string;
  signature?: string;
  timestamp?: number;
  metadata?: Record<string, unknown>;
}

export interface SubagentState {
  subagent_id?: string;
  participant_identity?: string;
  room?: string;
  request?: string;
  task_type?: string;
  risk?: string;
  status?: 'running' | 'completed' | 'failed' | 'cancelled' | string;
  created_at?: string;
  updated_at?: string;
  result_summary?: string | null;
  route_provider?: string | null;
  error?: string | null;
  finished_at?: string | null;
}

export interface ExecutionTraceStep {
  traceId: string;
  actionName: string;
  timestamp: number;
  risk?: string;
  policyDecision?: string;
  provider?: string;
  fallbackUsed?: boolean;
  success: boolean;
  message: string;
}

export interface OpsIncidentSnapshot {
  generated_at?: string;
  autonomy_mode?: string;
  canary_state?: CanaryState;
  canary_metrics?: {
    canary?: { total?: number; success?: number; failed?: number; success_rate?: number };
    stable?: { total?: number; success?: number; failed?: number; success_rate?: number };
  };
  feature_flags?: {
    values?: Record<string, boolean>;
    overrides?: Record<string, boolean>;
  };
  domain_autonomy_modes?: Array<{
    domain?: string;
    mode?: string;
    reason?: string;
    source?: string;
    updated_at?: string;
  }>;
  domain_autonomy_status?: Array<{
    domain?: string;
    autonomy_mode?: string;
    domain_autonomy_mode?: string | null;
    effective_autonomy_mode?: string;
    domain_autonomy_active?: boolean;
    containment_reason?: string | null;
    containment_reasons?: string[];
    containment_source?: string | null;
    domain_autonomy_updated_at?: string | null;
    trust_drift_active?: boolean;
    autonomy_notice_unconfirmed?: number;
  }>;
  kill_switch?: {
    global_enabled?: boolean;
    global_reason?: string;
    domains?: Record<string, string>;
    updated_at?: string;
  };
  providers_health?: Array<{
    provider?: string;
    configured?: boolean;
    supports_tools?: boolean;
    supports_realtime?: boolean;
    status?: string;
    ping_ok?: boolean;
    ping_preview?: string;
    error?: string;
  }>;
  metrics_summary?: {
    total_actions?: number;
    providers?: Record<string, { total?: number; success?: number; failed?: number }>;
    risk_tiers?: Record<string, { total?: number; success?: number; failed?: number }>;
  };
  slo_report?: {
    total_actions?: number;
    latency?: {
      overall_p95_ms?: number;
      fallback_p95_ms?: number;
    };
    reliability?: {
      low_risk_success_rate?: number;
      false_success_proxy_rate?: number;
      trust_drift_active_rate?: number;
    };
  };
  trust_drift?: {
    active_total?: number;
    domains?: Array<Record<string, unknown>>;
  };
  autonomy_notice?: {
    active_total?: number;
    inactive_total?: number;
    by_level?: Record<string, { total?: number; success?: number; failed?: number }>;
    by_channel?: Record<string, { total?: number; success?: number; failed?: number }>;
    by_domain?: Record<string, { total?: number; success?: number; failed?: number }>;
    unconfirmed_total?: number;
    unconfirmed_by_domain?: Record<string, number>;
  };
  alerts?: string[];
}

export interface CanaryState {
  global_enabled?: boolean;
  session_enrolled?: boolean;
  manual_enrolled?: boolean;
  rollout_percent?: number;
  assignment_bucket?: number;
  eligible_by_rollout?: boolean;
  active?: boolean;
  cohort?: 'canary' | 'stable' | string;
}

export interface OpsPlaybookChange {
  type?: string;
  target?: string;
  from?: string | number | boolean | null;
  to?: string | number | boolean | null;
  note?: string;
}

export interface OpsPlaybookReport {
  playbook?: string;
  dry_run?: boolean;
  applied?: boolean;
  changes?: OpsPlaybookChange[];
  step_reports?: Array<Record<string, unknown>>;
  steps_executed?: string[];
  notes?: string[];
  before?: Record<string, unknown>;
  after?: Record<string, unknown>;
  generated_at?: string;
}

export interface OpsAutoRemediation {
  executed?: boolean;
  dry_run?: boolean;
  reason?: string;
  scenario?: string;
  signal?: {
    provider_outage?: boolean;
    reliability_breach?: boolean;
    latency_spike?: boolean;
    canary_degraded?: boolean;
    trust_drift_breach?: boolean;
    autonomy_notice_delivery_breach?: boolean;
    autonomy_notice_unconfirmed_rate?: number;
    autonomy_notice_delivery_domains?: string[];
    trust_drift_active_domains?: string[];
    recommended_scenario?: string;
    reasons?: string[];
  };
  cooldown_remaining_seconds?: number;
  generated_at?: string;
}

export interface OpsCanaryPromotion {
  executed?: boolean;
  promoted?: boolean;
  dry_run?: boolean;
  force?: boolean;
  step_if_passed?: boolean;
  rollback_on_fail?: boolean;
  gate?: Record<string, unknown>;
  cooldown_remaining_seconds?: number;
  rollout_status?: { success?: boolean; message?: string };
  rollback_status?: { success?: boolean; message?: string };
  generated_at?: string;
}

export interface OpsControlTick {
  executed?: boolean;
  dry_run?: boolean;
  auto_remediate?: boolean;
  auto_promote_canary?: boolean;
  remediation_triggered?: boolean;
  remediation_scenario?: string | null;
  promotion_skipped_reason?: string | null;
  remediation_status?: { success?: boolean; message?: string };
  promotion_status?: { success?: boolean; message?: string };
  generated_at?: string;
}

export type OpsCommandStatus = 'pending' | 'dispatching' | 'sent' | 'failed';
export type OpsRiskTier = 'R0' | 'R1' | 'R2' | 'R3' | string;

export interface OpsCommandRequest {
  id: string;
  label: string;
  prompt: string;
  expectedActionName?: string;
  domain?: string;
  riskTier?: OpsRiskTier;
  autoRetryOnNoEvidence?: boolean;
  maxAutoRetries?: number;
  retryCount?: number;
  noEvidenceTimeoutMs?: number;
  driftGuardrailApplied?: boolean;
  driftGuardrailReason?: string;
  lastDispatchAt?: number;
  executionTrace?: ExecutionTraceStep;
  status: OpsCommandStatus;
  createdAt: number;
  updatedAt: number;
  dispatcherId?: string;
  error?: string;
}

export interface DomainTrustScore {
  domain: string;
  score: number;
  samples: number;
  successCount: number;
  failureCount: number;
  noEvidenceCount: number;
  updatedAt: number;
  source?: 'local' | 'backend';
  autonomyMode?: string;
  domainAutonomyMode?: string | null;
  effectiveAutonomyMode?: string;
  domainAutonomyReason?: string | null;
  domainAutonomySource?: string | null;
  domainAutonomyUpdatedAt?: number | null;
  trustDriftActive?: boolean;
  recommendation: {
    timeoutMs: number;
    maxAutoRetries: number;
  };
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

export interface CodingHistoryEntry {
  id: string;
  timestamp: number;
  actionName: string;
  status: 'completed' | 'failed' | 'confirmation_required';
  message: string;
  projectName?: string;
}

export interface CodexTaskState {
  task_id?: string;
  status?: 'running' | 'completed' | 'failed' | 'cancelled' | string;
  project_id?: string;
  project_name?: string;
  working_directory?: string;
  request?: string;
  started_at?: string;
  finished_at?: string;
  current_phase?: string;
  summary?: string;
  exit_code?: number;
  raw_last_event?: Record<string, unknown>;
  command_preview?: string;
  error?: string;
}

export interface CodexTaskEvent {
  task_id?: string;
  phase?: string;
  message?: string;
  timestamp?: string;
  raw_event_type?: string;
}

export type CodexTaskHistoryEntry = CodexTaskState;

export interface BrowserTaskState {
  task_id?: string;
  status?: 'running' | 'completed' | 'failed' | 'cancelled' | string;
  request?: string;
  summary?: string;
  allowed_domains?: string[];
  read_only?: boolean;
  started_at?: string;
  finished_at?: string;
  error?: string;
  evidence?: Record<string, unknown> | null;
}

export interface WorkflowState {
  workflow_id?: string;
  workflow_type?: string;
  status?: 'planning' | 'awaiting_confirmation' | 'running' | 'completed' | 'failed' | 'cancelled' | string;
  project_id?: string;
  project_name?: string;
  summary?: string;
  current_step?: string;
  started_at?: string;
  finished_at?: string;
  error?: string;
}

export interface AutomationRunRow {
  automation_type?: string;
  source?: string;
  stage?: string;
  action_name?: string;
  success?: boolean;
  message?: string;
  error?: string | null;
  dry_run?: boolean;
  trace_id?: string;
  executed_at?: string;
  schedule_id?: string | null;
}

export interface AutomationSchedulerStatus {
  id?: string | null;
  automation_type?: string;
  query?: string;
  enabled?: boolean;
  status?: 'due' | 'pending' | 'cooldown' | 'already_ran' | 'disabled' | 'skipped' | string;
  reason?: string;
  timezone?: string;
  time_of_day?: string | null;
  next_due_at?: string;
  last_run_at?: string;
  cooldown_remaining_seconds?: number;
}

export interface AutomationState {
  automation_id?: string;
  automation_type?: string;
  status?: 'idle' | 'executing' | 'dry_run_complete' | 'executed' | 'scheduled' | 'running' | 'completed' | 'failed' | string;
  summary?: string;
  dry_run?: boolean;
  last_run_at?: string;
  next_run_at?: string;
  cooldown_remaining_seconds?: number;
  evidence?: Record<string, unknown> | null;
  last_cycle_at?: string;
  last_scheduler_due_at?: string | null;
  recent_runs?: AutomationRunRow[];
  loop?: {
    recent_runs?: AutomationRunRow[];
    daily_briefing?: {
      last_run_by_schedule?: Record<string, string>;
      recent_status?: AutomationSchedulerStatus[];
    };
    arrival?: {
      last_trigger_at?: string | null;
      last_live_run_at?: string | null;
      last_presence_state?: string | null;
    };
  };
  scheduler_status?: AutomationSchedulerStatus[];
  arrival_status?: Record<string, unknown>;
  loop_enabled?: boolean;
}

export interface SecuritySessionState {
  authenticated: boolean;
  identityBound: boolean;
  expiresIn: number;
  authMethod?: string;
  stepUpRequired: boolean;
  voiceScore?: number;
  personaMode?: string;
  personaColorHex?: string;
  personaLabel?: string;
  activeCharacterName?: string;
  activeCharacterSource?: string;
  activeCharacterSummary?: string;
  activeProjectId?: string;
  activeProjectName?: string;
  activeProjectRootPath?: string;
  activeProjectIndexStatus?: string;
  codingMode?: string;
  autonomyNotice?: {
    active?: boolean;
    level?: 'info' | 'warning' | 'critical' | string;
    title?: string;
    message?: string;
    domain?: string;
    scenario?: string;
    decision?: string;
    signature?: string;
    spoken_message?: string;
    spoken_channel?: 'agent_audio' | 'browser_tts' | string;
    trace_id?: string;
  } | null;
}

export interface SessionSnapshot {
  security_session?: {
    security_status?: {
      authenticated?: boolean;
      identity_bound?: boolean;
      expires_in?: number;
      auth_method?: string;
      step_up_required?: boolean;
    };
    persona_mode?: string;
    persona_profile?: {
      label?: string;
      style?: string;
      color_hex?: string;
      voice_hint?: string;
    };
    active_character?: {
      name?: string;
      source?: string;
      summary?: string;
    } | null;
    active_project?: {
      project_id?: string;
      name?: string;
      root_path?: string;
      index_status?: string;
    } | null;
    coding_mode?: string;
  };
  research_schedules?: Array<Record<string, unknown>> | null;
  model_route?: ModelRouteDecision | null;
  subagent_states?: SubagentState[] | null;
  policy_events?: PolicyEvent[] | null;
  execution_traces?: ExecutionTraceStep[] | null;
  eval_baseline_summary?: Record<string, unknown> | null;
  eval_metrics?: Array<Record<string, unknown>> | null;
  eval_metrics_summary?: Record<string, unknown> | null;
  slo_report?: Record<string, unknown> | null;
  providers_health?: Array<Record<string, unknown>> | null;
  feature_flags?: Record<string, unknown> | null;
  canary_state?: CanaryState | null;
  incident_snapshot?: OpsIncidentSnapshot | null;
  playbook_report?: OpsPlaybookReport | null;
  auto_remediation?: OpsAutoRemediation | null;
  canary_promotion?: OpsCanaryPromotion | null;
  control_tick?: OpsControlTick | null;
  active_codex_task?: CodexTaskState | null;
  codex_history?: CodexTaskHistoryEntry[] | null;
  browser_tasks?: BrowserTaskState | BrowserTaskState[] | null;
  workflow_state?: WorkflowState | null;
  automation_state?: AutomationState | null;
  recognized_identity?: RecognizedIdentity | null;
  whatsapp_channel?: Record<string, unknown> | null;
  voice_interactivity?: VoiceInteractivityState | null;
}

export interface ResearchDashboardResult {
  title: string;
  url: string;
  domain: string;
  snippet?: string;
  pageTitle?: string;
  pageDescription?: string;
  imageUrl?: string;
}

export interface ResearchDashboard {
  query: string;
  summary: string;
  generatedAt?: string;
  images: string[];
  results: ResearchDashboardResult[];
}

export interface ResearchSchedule {
  id: string;
  query: string;
  cadence: 'daily' | string;
  timeOfDay: string;
  prompt: string;
  lastRunOn?: string;
}

export interface ReconnectState {
  connectionState: ConnectionState;
  attempt: number;
  maxAttempts: number;
  isReconnecting: boolean;
  reconnectNow: () => Promise<void>;
}
