import type {
  AutomationState,
  BrowserTaskState,
  DomainTrustScore,
  ExecutionTraceStep,
  ModelRouteDecision,
  OpsCommandRequest,
  OpsCommandStatus,
  OpsRiskTier,
  PolicyEvent,
  SubagentState,
  WorkflowState,
} from '@/lib/types/realtime';

export const ORCHESTRATION_ROUTE_KEY = 'jarvez:orchestration-route';
export const ORCHESTRATION_SUBAGENTS_KEY = 'jarvez:orchestration-subagents';
export const TRUST_CENTER_POLICY_KEY = 'jarvez:trust-policy-events';
export const TRUST_CENTER_TRACES_KEY = 'jarvez:trust-traces';
export const TRUST_CENTER_EVAL_BASELINE_KEY = 'jarvez:trust-eval-baseline';
export const TRUST_CENTER_EVAL_METRICS_KEY = 'jarvez:trust-eval-metrics';
export const TRUST_CENTER_EVAL_SUMMARY_KEY = 'jarvez:trust-eval-summary';
export const TRUST_CENTER_SLO_REPORT_KEY = 'jarvez:trust-slo-report';
export const TRUST_CENTER_PROVIDERS_HEALTH_KEY = 'jarvez:trust-providers-health';
export const TRUST_CENTER_FEATURE_FLAGS_KEY = 'jarvez:trust-feature-flags';
export const TRUST_CENTER_CANARY_STATE_KEY = 'jarvez:trust-canary-state';
export const TRUST_CENTER_INCIDENT_SNAPSHOT_KEY = 'jarvez:trust-incident-snapshot';
export const TRUST_CENTER_PLAYBOOK_REPORT_KEY = 'jarvez:trust-playbook-report';
export const TRUST_CENTER_AUTO_REMEDIATION_KEY = 'jarvez:trust-auto-remediation';
export const TRUST_CENTER_CANARY_PROMOTION_KEY = 'jarvez:trust-canary-promotion';
export const TRUST_CENTER_CONTROL_TICK_KEY = 'jarvez:trust-control-tick';
export const TRUST_CENTER_OPS_COMMAND_QUEUE_KEY = 'jarvez:trust-ops-command-queue';
export const TRUST_CENTER_DOMAIN_TRUST_KEY = 'jarvez:trust-domain-trust';
export const TRUST_CENTER_BACKEND_DOMAIN_TRUST_KEY = 'jarvez:trust-domain-trust-backend';
export const TRUST_CENTER_TRUST_DRIFT_ALERT_KEY = 'jarvez:trust-drift-alert-signature';
export const ORCHESTRATION_BROWSER_TASK_KEY = 'jarvez:browser-task';
export const ORCHESTRATION_WORKFLOW_STATE_KEY = 'jarvez:workflow-state';
export const ORCHESTRATION_AUTOMATION_STATE_KEY = 'jarvez:automation-state';
export const ORCHESTRATION_WHATSAPP_CHANNEL_KEY = 'jarvez:whatsapp-channel';

const OPS_COMMAND_TERMINAL_STATUS: ReadonlySet<OpsCommandStatus> = new Set(['sent', 'failed']);
const MAX_OPS_COMMAND_ENTRIES = 60;
const OPS_COMMAND_DISPATCHING_STALE_MS = 45_000;
const OPS_COMMAND_TRACE_MATCH_WINDOW_MS = 10 * 60_000;
const DEFAULT_NO_EVIDENCE_TIMEOUT_MS = 45_000;
const MAX_NO_EVIDENCE_TIMEOUT_MS = 30 * 60_000;
const MAX_AUTO_RETRIES_HARD_LIMIT = 5;
const DEFAULT_DOMAIN_TRUST_SCORE = 0.7;
const DOMAIN_TRUST_DRIFT_THRESHOLD = 0.18;
const DOMAIN_TRUST_TIMEOUT_DRIFT_MS = 15_000;

type DomainTrustOutcome = 'success' | 'failure' | 'no_evidence';

const DOMAIN_TRUST_OUTCOME_DELTA: Record<DomainTrustOutcome, number> = {
  success: 0.06,
  failure: -0.12,
  no_evidence: -0.18,
};

function clampScore(value: number): number {
  if (!Number.isFinite(value)) return DEFAULT_DOMAIN_TRUST_SCORE;
  if (value < 0) return 0;
  if (value > 1) return 1;
  return value;
}

function recommendationFromScore(score: number): { timeoutMs: number; maxAutoRetries: number } {
  if (score >= 0.85) {
    return { timeoutMs: 30_000, maxAutoRetries: 2 };
  }
  if (score >= 0.65) {
    return { timeoutMs: 45_000, maxAutoRetries: 1 };
  }
  if (score >= 0.45) {
    return { timeoutMs: 60_000, maxAutoRetries: 0 };
  }
  return { timeoutMs: 90_000, maxAutoRetries: 0 };
}

function isLowRiskTier(riskTier?: OpsRiskTier): boolean {
  return riskTier === 'R0' || riskTier === 'R1';
}

function clampInteger(value: number, min: number, max: number): number {
  if (!Number.isFinite(value)) return min;
  return Math.max(min, Math.min(max, Math.trunc(value)));
}

function extractActionNameFromPrompt(prompt: string): string | undefined {
  const match = /(?:^|\n)\s*action_name=([a-zA-Z0-9_]+)/.exec(prompt);
  if (!match || typeof match[1] !== 'string') return undefined;
  return match[1];
}

function inferDomainFromActionName(actionName?: string): string | undefined {
  if (!actionName) return undefined;
  if (actionName.startsWith('whatsapp_')) return 'whatsapp';
  if (
    actionName.startsWith('ac_') ||
    actionName.startsWith('thinq_') ||
    actionName.startsWith('home_')
  ) {
    return 'home';
  }
  if (
    actionName.startsWith('run_local_command') ||
    actionName.startsWith('git_') ||
    actionName.startsWith('code_') ||
    actionName.startsWith('project_') ||
    actionName.startsWith('codex_')
  ) {
    return 'shell';
  }
  if (
    actionName.startsWith('ops_') ||
    actionName.startsWith('autonomy_') ||
    actionName.startsWith('policy_') ||
    actionName.startsWith('evals_') ||
    actionName.startsWith('providers_')
  ) {
    return 'ops';
  }
  return 'general';
}

function inferDomainFromPrompt(prompt: string): string | undefined {
  return inferDomainFromActionName(extractActionNameFromPrompt(prompt));
}

function normalizeDomainTrustScores(value: unknown): DomainTrustScore[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((item): item is DomainTrustScore => Boolean(item && typeof item === 'object'))
    .map<DomainTrustScore>((item) => {
      const score = clampScore(Number(item.score));
      const domainAutonomyUpdatedAt = Number(item.domainAutonomyUpdatedAt);
      return {
        domain: typeof item.domain === 'string' && item.domain ? item.domain : 'general',
        score,
        samples: clampInteger(Number(item.samples ?? 0), 0, 100_000),
        successCount: clampInteger(Number(item.successCount ?? 0), 0, 100_000),
        failureCount: clampInteger(Number(item.failureCount ?? 0), 0, 100_000),
        noEvidenceCount: clampInteger(Number(item.noEvidenceCount ?? 0), 0, 100_000),
        updatedAt: Number.isFinite(Number(item.updatedAt)) ? Number(item.updatedAt) : Date.now(),
        source: item.source === 'backend' ? 'backend' : 'local',
        autonomyMode: typeof item.autonomyMode === 'string' ? item.autonomyMode : undefined,
        domainAutonomyMode:
          typeof item.domainAutonomyMode === 'string' && item.domainAutonomyMode
            ? item.domainAutonomyMode
            : null,
        effectiveAutonomyMode:
          typeof item.effectiveAutonomyMode === 'string' ? item.effectiveAutonomyMode : undefined,
        domainAutonomyReason:
          typeof item.domainAutonomyReason === 'string' && item.domainAutonomyReason
            ? item.domainAutonomyReason
            : null,
        domainAutonomySource:
          typeof item.domainAutonomySource === 'string' && item.domainAutonomySource
            ? item.domainAutonomySource
            : null,
        domainAutonomyUpdatedAt: Number.isFinite(domainAutonomyUpdatedAt)
          ? domainAutonomyUpdatedAt
          : null,
        trustDriftActive: Boolean(item.trustDriftActive),
        recommendation: {
          timeoutMs: normalizeNoEvidenceTimeoutMs(item.recommendation?.timeoutMs),
          maxAutoRetries: normalizeMaxAutoRetries(item.recommendation?.maxAutoRetries, true),
        },
      };
    })
    .sort((a, b) => a.domain.localeCompare(b.domain));
}

function normalizeBackendDomainTrustScores(value: unknown): DomainTrustScore[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((item): item is Record<string, unknown> => Boolean(item && typeof item === 'object'))
    .map<DomainTrustScore>((item) => {
      const score = clampScore(Number(item.score));
      const updatedAt = Date.parse(String(item.updated_at ?? ''));
      const recommendation =
        item.recommendation && typeof item.recommendation === 'object'
          ? (item.recommendation as Record<string, unknown>)
          : undefined;
      const domainAutonomyUpdatedAt = Date.parse(String(item.domain_autonomy_updated_at ?? ''));
      return {
        domain: typeof item.domain === 'string' && item.domain ? item.domain : 'general',
        score,
        samples: clampInteger(Number(item.samples ?? 0), 0, 100_000),
        successCount: clampInteger(Number(item.success_count ?? 0), 0, 100_000),
        failureCount: clampInteger(Number(item.failure_count ?? 0), 0, 100_000),
        noEvidenceCount: clampInteger(Number(item.no_evidence_count ?? 0), 0, 100_000),
        updatedAt: Number.isFinite(updatedAt) ? updatedAt : Date.now(),
        source: 'backend',
        autonomyMode: typeof item.autonomy_mode === 'string' ? item.autonomy_mode : undefined,
        domainAutonomyMode:
          typeof item.domain_autonomy_mode === 'string' && item.domain_autonomy_mode
            ? item.domain_autonomy_mode
            : null,
        effectiveAutonomyMode:
          typeof item.effective_autonomy_mode === 'string'
            ? item.effective_autonomy_mode
            : undefined,
        domainAutonomyReason:
          typeof item.domain_autonomy_reason === 'string' && item.domain_autonomy_reason
            ? item.domain_autonomy_reason
            : null,
        domainAutonomySource:
          typeof item.domain_autonomy_source === 'string' && item.domain_autonomy_source
            ? item.domain_autonomy_source
            : null,
        domainAutonomyUpdatedAt: Number.isFinite(domainAutonomyUpdatedAt)
          ? domainAutonomyUpdatedAt
          : null,
        trustDriftActive: Boolean(item.trust_drift_active),
        recommendation: {
          timeoutMs: normalizeNoEvidenceTimeoutMs(recommendation?.timeout_ms),
          maxAutoRetries: normalizeMaxAutoRetries(recommendation?.max_auto_retries, true),
        },
      };
    })
    .sort((a, b) => a.domain.localeCompare(b.domain));
}

function writeStoredDomainTrustScores(scores: DomainTrustScore[]) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(TRUST_CENTER_DOMAIN_TRUST_KEY, JSON.stringify(scores));
}

function writeStoredBackendDomainTrustScoresInternal(scores: DomainTrustScore[]) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(TRUST_CENTER_BACKEND_DOMAIN_TRUST_KEY, JSON.stringify(scores));
}

function readStoredDomainTrustScoresInternal(): DomainTrustScore[] {
  if (typeof window === 'undefined') return [];
  const raw = window.localStorage.getItem(TRUST_CENTER_DOMAIN_TRUST_KEY);
  if (!raw) return [];
  try {
    return normalizeDomainTrustScores(JSON.parse(raw));
  } catch {
    window.localStorage.removeItem(TRUST_CENTER_DOMAIN_TRUST_KEY);
    return [];
  }
}

function readStoredBackendDomainTrustScoresInternal(): DomainTrustScore[] {
  if (typeof window === 'undefined') return [];
  const raw = window.localStorage.getItem(TRUST_CENTER_BACKEND_DOMAIN_TRUST_KEY);
  if (!raw) return [];
  try {
    return normalizeDomainTrustScores(JSON.parse(raw));
  } catch {
    window.localStorage.removeItem(TRUST_CENTER_BACKEND_DOMAIN_TRUST_KEY);
    return [];
  }
}

function upsertDomainTrustScore(
  domain: string,
  outcome: DomainTrustOutcome
): DomainTrustScore | null {
  if (typeof window === 'undefined') return null;
  const normalizedDomain = domain && domain.trim() ? domain.trim() : 'general';
  const current = readStoredDomainTrustScoresInternal();
  const index = current.findIndex((item) => item.domain === normalizedDomain);
  const previous =
    index >= 0
      ? current[index]
      : {
          domain: normalizedDomain,
          score: DEFAULT_DOMAIN_TRUST_SCORE,
          samples: 0,
          successCount: 0,
          failureCount: 0,
          noEvidenceCount: 0,
          updatedAt: Date.now(),
          source: 'local',
          recommendation: recommendationFromScore(DEFAULT_DOMAIN_TRUST_SCORE),
        };

  const delta = DOMAIN_TRUST_OUTCOME_DELTA[outcome];
  const nextScore = clampScore(previous.score + delta);
  const updated: DomainTrustScore = {
    domain: normalizedDomain,
    score: nextScore,
    samples: previous.samples + 1,
    successCount: previous.successCount + (outcome === 'success' ? 1 : 0),
    failureCount: previous.failureCount + (outcome === 'failure' ? 1 : 0),
    noEvidenceCount: previous.noEvidenceCount + (outcome === 'no_evidence' ? 1 : 0),
    updatedAt: Date.now(),
    source: 'local',
    recommendation: recommendationFromScore(nextScore),
  };

  const nextScores =
    index >= 0
      ? current.map((item, itemIndex) => (itemIndex === index ? updated : item))
      : [...current, updated];
  writeStoredDomainTrustScores(nextScores.sort((a, b) => a.domain.localeCompare(b.domain)));
  return updated;
}

function getDomainTrustScore(domain?: string): DomainTrustScore | null {
  if (!domain) return null;
  const normalizedDomain = domain.trim();
  if (!normalizedDomain) return null;
  const scores = readStoredDomainTrustScoresInternal();
  return scores.find((item) => item.domain === normalizedDomain) ?? null;
}

function getBackendDomainTrustScore(domain?: string): DomainTrustScore | null {
  if (!domain) return null;
  const normalizedDomain = domain.trim();
  if (!normalizedDomain) return null;
  const scores = readStoredBackendDomainTrustScoresInternal();
  return scores.find((item) => item.domain === normalizedDomain) ?? null;
}

function getEffectiveDomainTrustScore(domain?: string): DomainTrustScore | null {
  return getBackendDomainTrustScore(domain) ?? getDomainTrustScore(domain);
}

function isDomainTrustDrifted(domain?: string): boolean {
  if (!domain) return false;
  const backend = getBackendDomainTrustScore(domain);
  const local = getDomainTrustScore(domain);
  if (!backend || !local) return false;
  const scoreDelta = Math.abs(backend.score - local.score);
  const timeoutDelta = Math.abs(backend.recommendation.timeoutMs - local.recommendation.timeoutMs);
  const retryDelta = Math.abs(
    backend.recommendation.maxAutoRetries - local.recommendation.maxAutoRetries
  );
  return (
    scoreDelta >= DOMAIN_TRUST_DRIFT_THRESHOLD ||
    timeoutDelta >= DOMAIN_TRUST_TIMEOUT_DRIFT_MS ||
    retryDelta > 0
  );
}

function applyTrustDriftGuardrail(input: {
  domain?: string;
  riskTier?: OpsRiskTier;
  autoRetryOnNoEvidence?: boolean;
  maxAutoRetries?: number;
  noEvidenceTimeoutMs?: number;
  trustRecommendation?: { timeoutMs: number; maxAutoRetries: number };
}): {
  autoRetryOnNoEvidence?: boolean;
  maxAutoRetries?: number;
  noEvidenceTimeoutMs?: number;
  driftGuardrailApplied: boolean;
  driftGuardrailReason?: string;
} {
  if (!isDomainTrustDrifted(input.domain)) {
    return {
      autoRetryOnNoEvidence: input.autoRetryOnNoEvidence,
      maxAutoRetries: input.maxAutoRetries,
      noEvidenceTimeoutMs: input.noEvidenceTimeoutMs,
      driftGuardrailApplied: false,
    };
  }

  const effectiveAutoRetry = Boolean(input.autoRetryOnNoEvidence);
  const normalizedRetries = normalizeMaxAutoRetries(input.maxAutoRetries, effectiveAutoRetry);
  const guardedRetries = Math.max(0, normalizedRetries - 1);
  const guardedAutoRetry = effectiveAutoRetry && guardedRetries > 0;
  const baselineTimeout = normalizeNoEvidenceTimeoutMs(
    input.noEvidenceTimeoutMs ?? input.trustRecommendation?.timeoutMs
  );
  const guardedTimeout = normalizeNoEvidenceTimeoutMs(
    Math.max(
      baselineTimeout + 15_000,
      (input.trustRecommendation?.timeoutMs ?? baselineTimeout) + 15_000
    )
  );

  return {
    autoRetryOnNoEvidence: guardedAutoRetry,
    maxAutoRetries: guardedRetries,
    noEvidenceTimeoutMs: guardedTimeout,
    driftGuardrailApplied: true,
    driftGuardrailReason: `Trust drift ativo no dominio ${input.domain ?? 'general'}; fila em modo conservador.`,
  };
}

function applyDomainTrustEvents(events: Array<{ domain: string; outcome: DomainTrustOutcome }>) {
  for (const event of events) {
    if (!event.domain) continue;
    upsertDomainTrustScore(event.domain, event.outcome);
  }
}

function normalizeNoEvidenceTimeoutMs(value: unknown): number {
  const n = Number(value);
  if (!Number.isFinite(n)) return DEFAULT_NO_EVIDENCE_TIMEOUT_MS;
  return clampInteger(n, 5_000, MAX_NO_EVIDENCE_TIMEOUT_MS);
}

function normalizeMaxAutoRetries(value: unknown, autoRetryEnabled: boolean): number {
  const fallback = autoRetryEnabled ? 1 : 0;
  const n = Number(value);
  if (!Number.isFinite(n)) return fallback;
  return clampInteger(n, 0, MAX_AUTO_RETRIES_HARD_LIMIT);
}

function normalizeOpsCommandQueue(value: unknown): OpsCommandRequest[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((item): item is OpsCommandRequest => Boolean(item && typeof item === 'object'))
    .map((item) => {
      const createdAt = Number(item.createdAt);
      const updatedAt = Number(item.updatedAt);
      const status = item.status;
      return {
        id: String(item.id ?? ''),
        label: String(item.label ?? ''),
        prompt: String(item.prompt ?? ''),
        expectedActionName:
          typeof item.expectedActionName === 'string' && item.expectedActionName
            ? item.expectedActionName
            : extractActionNameFromPrompt(String(item.prompt ?? '')),
        domain:
          typeof item.domain === 'string' && item.domain
            ? item.domain
            : inferDomainFromPrompt(String(item.prompt ?? '')),
        executionTrace:
          item.executionTrace &&
          typeof item.executionTrace === 'object' &&
          typeof item.executionTrace.traceId === 'string' &&
          typeof item.executionTrace.actionName === 'string'
            ? (item.executionTrace as ExecutionTraceStep)
            : undefined,
        riskTier: typeof item.riskTier === 'string' && item.riskTier ? item.riskTier : undefined,
        autoRetryOnNoEvidence:
          typeof item.autoRetryOnNoEvidence === 'boolean' ? item.autoRetryOnNoEvidence : undefined,
        maxAutoRetries: normalizeMaxAutoRetries(
          item.maxAutoRetries,
          typeof item.autoRetryOnNoEvidence === 'boolean'
            ? item.autoRetryOnNoEvidence
            : isLowRiskTier(typeof item.riskTier === 'string' ? item.riskTier : undefined)
        ),
        retryCount: clampInteger(Number(item.retryCount ?? 0), 0, MAX_AUTO_RETRIES_HARD_LIMIT),
        noEvidenceTimeoutMs: normalizeNoEvidenceTimeoutMs(item.noEvidenceTimeoutMs),
        driftGuardrailApplied: item.driftGuardrailApplied === true,
        driftGuardrailReason:
          typeof item.driftGuardrailReason === 'string' && item.driftGuardrailReason
            ? item.driftGuardrailReason
            : undefined,
        lastDispatchAt: Number.isFinite(Number(item.lastDispatchAt))
          ? Number(item.lastDispatchAt)
          : undefined,
        status:
          status === 'pending' ||
          status === 'dispatching' ||
          status === 'sent' ||
          status === 'failed'
            ? status
            : 'pending',
        createdAt: Number.isFinite(createdAt) ? createdAt : Date.now(),
        updatedAt: Number.isFinite(updatedAt) ? updatedAt : Date.now(),
        dispatcherId:
          typeof item.dispatcherId === 'string' && item.dispatcherId
            ? item.dispatcherId
            : undefined,
        error: typeof item.error === 'string' && item.error ? item.error : undefined,
      };
    })
    .filter((item) => item.id && item.prompt)
    .sort((a, b) => a.createdAt - b.createdAt);
}

function compactOpsCommandQueue(queue: OpsCommandRequest[]): OpsCommandRequest[] {
  const pending = queue.filter((item) => !OPS_COMMAND_TERMINAL_STATUS.has(item.status));
  const terminal = queue
    .filter((item) => OPS_COMMAND_TERMINAL_STATUS.has(item.status))
    .sort((a, b) => b.updatedAt - a.updatedAt)
    .slice(0, 24);
  return [...pending, ...terminal].slice(-MAX_OPS_COMMAND_ENTRIES);
}

function writeStoredOpsCommandQueue(queue: OpsCommandRequest[]) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(
    TRUST_CENTER_OPS_COMMAND_QUEUE_KEY,
    JSON.stringify(compactOpsCommandQueue(queue))
  );
}

function reviveStaleDispatchingCommands(
  queue: OpsCommandRequest[],
  staleAfterMs: number = OPS_COMMAND_DISPATCHING_STALE_MS
): { queue: OpsCommandRequest[]; revived: boolean } {
  const now = Date.now();
  let revived = false;
  const next = queue.map((item) => {
    if (item.status !== 'dispatching') return item;
    if (now - item.updatedAt <= staleAfterMs) return item;
    revived = true;
    return {
      ...item,
      status: 'pending' as const,
      dispatcherId: undefined,
      error: 'Dispatch anterior expirou; comando reenfileirado automaticamente.',
      updatedAt: now,
    };
  });
  return { queue: next, revived };
}

function applyNoEvidenceSlaPolicy(queue: OpsCommandRequest[]): {
  queue: OpsCommandRequest[];
  changed: boolean;
  trustEvents: Array<{ domain: string; outcome: DomainTrustOutcome }>;
} {
  const now = Date.now();
  let changed = false;
  const trustEvents: Array<{ domain: string; outcome: DomainTrustOutcome }> = [];
  const next = queue.map((item) => {
    if (item.status !== 'sent' || item.executionTrace) return item;
    const resolvedDomain = item.domain ?? inferDomainFromPrompt(item.prompt);

    const startedAt = Number(item.lastDispatchAt ?? item.updatedAt);
    const timeoutMs = normalizeNoEvidenceTimeoutMs(item.noEvidenceTimeoutMs);
    const elapsed = now - startedAt;
    if (!Number.isFinite(elapsed) || elapsed < timeoutMs) return item;

    const autoRetryEnabled =
      typeof item.autoRetryOnNoEvidence === 'boolean'
        ? item.autoRetryOnNoEvidence
        : isLowRiskTier(item.riskTier);
    const maxAutoRetries = normalizeMaxAutoRetries(item.maxAutoRetries, autoRetryEnabled);
    const retryCount = clampInteger(Number(item.retryCount ?? 0), 0, MAX_AUTO_RETRIES_HARD_LIMIT);

    if (autoRetryEnabled && retryCount < maxAutoRetries) {
      changed = true;
      if (resolvedDomain) {
        trustEvents.push({ domain: resolvedDomain, outcome: 'no_evidence' });
      }
      return {
        ...item,
        domain: resolvedDomain,
        status: 'pending' as const,
        dispatcherId: undefined,
        retryCount: retryCount + 1,
        error: `Sem evidencia apos ${Math.round(timeoutMs / 1000)}s; auto-retry ${retryCount + 1}/${maxAutoRetries}.`,
        updatedAt: now,
      };
    }

    changed = true;
    if (resolvedDomain) {
      trustEvents.push({ domain: resolvedDomain, outcome: 'no_evidence' });
    }
    return {
      ...item,
      domain: resolvedDomain,
      status: 'failed' as const,
      error: `Sem evidencia de execucao apos ${Math.round(timeoutMs / 1000)}s.`,
      updatedAt: now,
    };
  });

  return { queue: next, changed, trustEvents };
}

function applyQueueRuntimePolicies(queue: OpsCommandRequest[]): {
  queue: OpsCommandRequest[];
  changed: boolean;
  trustEvents: Array<{ domain: string; outcome: DomainTrustOutcome }>;
} {
  const recovered = reviveStaleDispatchingCommands(queue);
  const sla = applyNoEvidenceSlaPolicy(recovered.queue);
  return {
    queue: sla.queue,
    changed: recovered.revived || sla.changed,
    trustEvents: sla.trustEvents,
  };
}

export function readStoredModelRoute(): ModelRouteDecision | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(ORCHESTRATION_ROUTE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as ModelRouteDecision;
  } catch {
    window.localStorage.removeItem(ORCHESTRATION_ROUTE_KEY);
    return null;
  }
}

export function writeStoredModelRoute(route: ModelRouteDecision) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(ORCHESTRATION_ROUTE_KEY, JSON.stringify(route));
}

export function readStoredSubagents(): SubagentState[] {
  if (typeof window === 'undefined') return [];
  const raw = window.localStorage.getItem(ORCHESTRATION_SUBAGENTS_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as SubagentState[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    window.localStorage.removeItem(ORCHESTRATION_SUBAGENTS_KEY);
    return [];
  }
}

export function writeStoredSubagents(states: SubagentState[]) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(ORCHESTRATION_SUBAGENTS_KEY, JSON.stringify(states));
}

export function readStoredPolicyEvents(): PolicyEvent[] {
  if (typeof window === 'undefined') return [];
  const raw = window.localStorage.getItem(TRUST_CENTER_POLICY_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as PolicyEvent[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    window.localStorage.removeItem(TRUST_CENTER_POLICY_KEY);
    return [];
  }
}

export function writeStoredPolicyEvents(events: PolicyEvent[]) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(TRUST_CENTER_POLICY_KEY, JSON.stringify(events));
}

export function appendStoredPolicyEvent(
  event: PolicyEvent,
  maxEntries: number = 40
): PolicyEvent[] {
  const current = readStoredPolicyEvents();
  if (event.signature) {
    const existing = current.find(
      (item) =>
        item.signature === event.signature &&
        item.event_type === event.event_type &&
        item.decision === event.decision
    );
    if (existing) {
      return current;
    }
  }
  const next = [
    {
      ...event,
      timestamp: Number.isFinite(Number(event.timestamp)) ? Number(event.timestamp) : Date.now(),
      source: event.source ?? 'synthetic',
    },
    ...current,
  ].slice(0, maxEntries);
  writeStoredPolicyEvents(next);
  return next;
}

export function readStoredTrustDriftAlertSignature(): string | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(TRUST_CENTER_TRUST_DRIFT_ALERT_KEY);
  return raw && raw.trim() ? raw : null;
}

export function writeStoredTrustDriftAlertSignature(signature: string | null) {
  if (typeof window === 'undefined') return;
  if (!signature) {
    window.localStorage.removeItem(TRUST_CENTER_TRUST_DRIFT_ALERT_KEY);
    return;
  }
  window.localStorage.setItem(TRUST_CENTER_TRUST_DRIFT_ALERT_KEY, signature);
}

export function readStoredExecutionTraces(): ExecutionTraceStep[] {
  if (typeof window === 'undefined') return [];
  const raw = window.localStorage.getItem(TRUST_CENTER_TRACES_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as ExecutionTraceStep[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    window.localStorage.removeItem(TRUST_CENTER_TRACES_KEY);
    return [];
  }
}

export function writeStoredExecutionTraces(traces: ExecutionTraceStep[]) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(TRUST_CENTER_TRACES_KEY, JSON.stringify(traces));
}

export function readStoredEvalBaselineSummary(): Record<string, unknown> | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(TRUST_CENTER_EVAL_BASELINE_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch {
    window.localStorage.removeItem(TRUST_CENTER_EVAL_BASELINE_KEY);
    return null;
  }
}

export function writeStoredEvalBaselineSummary(summary: Record<string, unknown>) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(TRUST_CENTER_EVAL_BASELINE_KEY, JSON.stringify(summary));
}

export function readStoredEvalMetrics(): Array<Record<string, unknown>> {
  if (typeof window === 'undefined') return [];
  const raw = window.localStorage.getItem(TRUST_CENTER_EVAL_METRICS_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as Array<Record<string, unknown>>;
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    window.localStorage.removeItem(TRUST_CENTER_EVAL_METRICS_KEY);
    return [];
  }
}

export function writeStoredEvalMetrics(metrics: Array<Record<string, unknown>>) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(TRUST_CENTER_EVAL_METRICS_KEY, JSON.stringify(metrics));
}

export function readStoredEvalMetricsSummary(): Record<string, unknown> | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(TRUST_CENTER_EVAL_SUMMARY_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch {
    window.localStorage.removeItem(TRUST_CENTER_EVAL_SUMMARY_KEY);
    return null;
  }
}

export function writeStoredEvalMetricsSummary(summary: Record<string, unknown>) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(TRUST_CENTER_EVAL_SUMMARY_KEY, JSON.stringify(summary));
}

export function readStoredSloReport(): Record<string, unknown> | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(TRUST_CENTER_SLO_REPORT_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch {
    window.localStorage.removeItem(TRUST_CENTER_SLO_REPORT_KEY);
    return null;
  }
}

export function writeStoredSloReport(report: Record<string, unknown>) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(TRUST_CENTER_SLO_REPORT_KEY, JSON.stringify(report));
}

export function readStoredProvidersHealth(): Array<Record<string, unknown>> {
  if (typeof window === 'undefined') return [];
  const raw = window.localStorage.getItem(TRUST_CENTER_PROVIDERS_HEALTH_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as Array<Record<string, unknown>>;
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    window.localStorage.removeItem(TRUST_CENTER_PROVIDERS_HEALTH_KEY);
    return [];
  }
}

export function writeStoredProvidersHealth(rows: Array<Record<string, unknown>>) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(TRUST_CENTER_PROVIDERS_HEALTH_KEY, JSON.stringify(rows));
}

export function readStoredFeatureFlags(): Record<string, unknown> | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(TRUST_CENTER_FEATURE_FLAGS_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch {
    window.localStorage.removeItem(TRUST_CENTER_FEATURE_FLAGS_KEY);
    return null;
  }
}

export function writeStoredFeatureFlags(value: Record<string, unknown>) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(TRUST_CENTER_FEATURE_FLAGS_KEY, JSON.stringify(value));
}

export function readStoredCanaryState(): Record<string, unknown> | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(TRUST_CENTER_CANARY_STATE_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch {
    window.localStorage.removeItem(TRUST_CENTER_CANARY_STATE_KEY);
    return null;
  }
}

export function writeStoredCanaryState(value: Record<string, unknown>) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(TRUST_CENTER_CANARY_STATE_KEY, JSON.stringify(value));
}

export function readStoredIncidentSnapshot(): Record<string, unknown> | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(TRUST_CENTER_INCIDENT_SNAPSHOT_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch {
    window.localStorage.removeItem(TRUST_CENTER_INCIDENT_SNAPSHOT_KEY);
    return null;
  }
}

export function writeStoredIncidentSnapshot(value: Record<string, unknown>) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(TRUST_CENTER_INCIDENT_SNAPSHOT_KEY, JSON.stringify(value));
}

export function readStoredPlaybookReport(): Record<string, unknown> | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(TRUST_CENTER_PLAYBOOK_REPORT_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch {
    window.localStorage.removeItem(TRUST_CENTER_PLAYBOOK_REPORT_KEY);
    return null;
  }
}

export function writeStoredPlaybookReport(value: Record<string, unknown>) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(TRUST_CENTER_PLAYBOOK_REPORT_KEY, JSON.stringify(value));
}

export function readStoredAutoRemediation(): Record<string, unknown> | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(TRUST_CENTER_AUTO_REMEDIATION_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch {
    window.localStorage.removeItem(TRUST_CENTER_AUTO_REMEDIATION_KEY);
    return null;
  }
}

export function writeStoredAutoRemediation(value: Record<string, unknown>) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(TRUST_CENTER_AUTO_REMEDIATION_KEY, JSON.stringify(value));
}

export function readStoredCanaryPromotion(): Record<string, unknown> | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(TRUST_CENTER_CANARY_PROMOTION_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch {
    window.localStorage.removeItem(TRUST_CENTER_CANARY_PROMOTION_KEY);
    return null;
  }
}

export function writeStoredCanaryPromotion(value: Record<string, unknown>) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(TRUST_CENTER_CANARY_PROMOTION_KEY, JSON.stringify(value));
}

export function readStoredControlTick(): Record<string, unknown> | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(TRUST_CENTER_CONTROL_TICK_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch {
    window.localStorage.removeItem(TRUST_CENTER_CONTROL_TICK_KEY);
    return null;
  }
}

export function writeStoredControlTick(value: Record<string, unknown>) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(TRUST_CENTER_CONTROL_TICK_KEY, JSON.stringify(value));
}

export function readStoredBrowserTask(): BrowserTaskState | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(ORCHESTRATION_BROWSER_TASK_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as BrowserTaskState;
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch {
    window.localStorage.removeItem(ORCHESTRATION_BROWSER_TASK_KEY);
    return null;
  }
}

export function writeStoredBrowserTask(value: BrowserTaskState | null) {
  if (typeof window === 'undefined') return;
  if (!value) {
    window.localStorage.removeItem(ORCHESTRATION_BROWSER_TASK_KEY);
    return;
  }
  window.localStorage.setItem(ORCHESTRATION_BROWSER_TASK_KEY, JSON.stringify(value));
}

export function readStoredWorkflowState(): WorkflowState | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(ORCHESTRATION_WORKFLOW_STATE_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as WorkflowState;
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch {
    window.localStorage.removeItem(ORCHESTRATION_WORKFLOW_STATE_KEY);
    return null;
  }
}

export function writeStoredWorkflowState(value: WorkflowState | null) {
  if (typeof window === 'undefined') return;
  if (!value) {
    window.localStorage.removeItem(ORCHESTRATION_WORKFLOW_STATE_KEY);
    return;
  }
  window.localStorage.setItem(ORCHESTRATION_WORKFLOW_STATE_KEY, JSON.stringify(value));
}

export function readStoredAutomationState(): AutomationState | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(ORCHESTRATION_AUTOMATION_STATE_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as AutomationState;
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch {
    window.localStorage.removeItem(ORCHESTRATION_AUTOMATION_STATE_KEY);
    return null;
  }
}

export function writeStoredAutomationState(value: AutomationState | null) {
  if (typeof window === 'undefined') return;
  if (!value) {
    window.localStorage.removeItem(ORCHESTRATION_AUTOMATION_STATE_KEY);
    return;
  }
  window.localStorage.setItem(ORCHESTRATION_AUTOMATION_STATE_KEY, JSON.stringify(value));
}

export function readStoredWhatsAppChannelStatus(): Record<string, unknown> | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(ORCHESTRATION_WHATSAPP_CHANNEL_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch {
    window.localStorage.removeItem(ORCHESTRATION_WHATSAPP_CHANNEL_KEY);
    return null;
  }
}

export function writeStoredWhatsAppChannelStatus(value: Record<string, unknown> | null) {
  if (typeof window === 'undefined') return;
  if (!value) {
    window.localStorage.removeItem(ORCHESTRATION_WHATSAPP_CHANNEL_KEY);
    return;
  }
  window.localStorage.setItem(ORCHESTRATION_WHATSAPP_CHANNEL_KEY, JSON.stringify(value));
}

export function readStoredOpsCommandQueue(): OpsCommandRequest[] {
  if (typeof window === 'undefined') return [];
  const raw = window.localStorage.getItem(TRUST_CENTER_OPS_COMMAND_QUEUE_KEY);
  if (!raw) return [];
  try {
    return normalizeOpsCommandQueue(JSON.parse(raw));
  } catch {
    window.localStorage.removeItem(TRUST_CENTER_OPS_COMMAND_QUEUE_KEY);
    return [];
  }
}

export function readStoredDomainTrustScores(): DomainTrustScore[] {
  return readStoredDomainTrustScoresInternal();
}

export function readStoredBackendDomainTrustScores(): DomainTrustScore[] {
  return readStoredBackendDomainTrustScoresInternal();
}

export function writeStoredBackendDomainTrustScores(rows: Array<Record<string, unknown>>) {
  writeStoredBackendDomainTrustScoresInternal(normalizeBackendDomainTrustScores(rows));
}

export function enqueueStoredOpsCommand(
  command: Omit<OpsCommandRequest, 'updatedAt'>
): OpsCommandRequest {
  const resolvedDomain =
    command.domain && command.domain.trim()
      ? command.domain.trim()
      : inferDomainFromPrompt(command.prompt);
  const resolvedRiskTier =
    command.riskTier && command.riskTier.trim() ? command.riskTier : undefined;
  const trustScore = getEffectiveDomainTrustScore(resolvedDomain);
  const trustRecommendation = trustScore?.recommendation;
  const autoRetryOnNoEvidence =
    typeof command.autoRetryOnNoEvidence === 'boolean'
      ? command.autoRetryOnNoEvidence
      : isLowRiskTier(resolvedRiskTier) && (trustRecommendation?.maxAutoRetries ?? 1) > 0;
  const requestedMaxAutoRetries = normalizeMaxAutoRetries(
    command.maxAutoRetries ?? trustRecommendation?.maxAutoRetries,
    autoRetryOnNoEvidence
  );
  const requestedTimeoutMs = normalizeNoEvidenceTimeoutMs(
    command.noEvidenceTimeoutMs ?? trustRecommendation?.timeoutMs
  );
  const driftGuardrail = applyTrustDriftGuardrail({
    domain: resolvedDomain,
    riskTier: resolvedRiskTier,
    autoRetryOnNoEvidence,
    maxAutoRetries: requestedMaxAutoRetries,
    noEvidenceTimeoutMs: requestedTimeoutMs,
    trustRecommendation,
  });
  const nextCommand: OpsCommandRequest = {
    ...command,
    expectedActionName:
      command.expectedActionName && command.expectedActionName.trim()
        ? command.expectedActionName.trim()
        : extractActionNameFromPrompt(command.prompt),
    domain: resolvedDomain,
    riskTier: resolvedRiskTier,
    autoRetryOnNoEvidence: driftGuardrail.autoRetryOnNoEvidence,
    maxAutoRetries: driftGuardrail.maxAutoRetries,
    retryCount: clampInteger(Number(command.retryCount ?? 0), 0, MAX_AUTO_RETRIES_HARD_LIMIT),
    noEvidenceTimeoutMs: driftGuardrail.noEvidenceTimeoutMs,
    driftGuardrailApplied: driftGuardrail.driftGuardrailApplied,
    driftGuardrailReason: driftGuardrail.driftGuardrailReason,
    lastDispatchAt: Number.isFinite(Number(command.lastDispatchAt))
      ? Number(command.lastDispatchAt)
      : undefined,
    updatedAt: Date.now(),
  };
  if (typeof window === 'undefined') return nextCommand;
  const current = readStoredOpsCommandQueue().filter((item) => item.id !== nextCommand.id);
  writeStoredOpsCommandQueue([...current, nextCommand]);
  return nextCommand;
}

export function claimStoredPendingOpsCommand(dispatcherId: string): OpsCommandRequest | null {
  if (typeof window === 'undefined') return null;
  const runtime = applyQueueRuntimePolicies(readStoredOpsCommandQueue());
  const queue = runtime.queue;
  if (runtime.trustEvents.length > 0) {
    applyDomainTrustEvents(runtime.trustEvents);
  }
  if (runtime.changed) {
    writeStoredOpsCommandQueue(queue);
  }
  const target = queue.find((item) => item.status === 'pending');
  if (!target) return null;
  const now = Date.now();
  const claimed: OpsCommandRequest = {
    ...target,
    status: 'dispatching',
    dispatcherId,
    lastDispatchAt: now,
    updatedAt: now,
    error: undefined,
  };
  writeStoredOpsCommandQueue(queue.map((item) => (item.id === target.id ? claimed : item)));
  return claimed;
}

export function updateStoredOpsCommandStatus(
  id: string,
  status: OpsCommandStatus,
  options?: { dispatcherId?: string; error?: string; setDispatchTimestamp?: boolean }
) {
  if (typeof window === 'undefined') return;
  const now = Date.now();
  const queue = readStoredOpsCommandQueue();
  const current = queue.find((item) => item.id === id);
  const updated = queue.map((item) =>
    item.id === id
      ? {
          ...item,
          status,
          dispatcherId: options?.dispatcherId ?? item.dispatcherId,
          error: options?.error,
          lastDispatchAt: options?.setDispatchTimestamp ? now : item.lastDispatchAt,
          updatedAt: now,
        }
      : item
  );
  writeStoredOpsCommandQueue(updated);
  if (
    status === 'failed' &&
    current &&
    current.status !== 'failed' &&
    (current.domain || inferDomainFromPrompt(current.prompt)) &&
    !current.executionTrace
  ) {
    upsertDomainTrustScore(
      current.domain ?? inferDomainFromPrompt(current.prompt) ?? 'general',
      'failure'
    );
  }
}

export function retryStoredOpsCommand(id: string): OpsCommandRequest | null {
  if (typeof window === 'undefined') return null;
  const queue = readStoredOpsCommandQueue();
  const target = queue.find((item) => item.id === id);
  if (!target) return null;
  const retried: OpsCommandRequest = {
    ...target,
    status: 'pending',
    dispatcherId: undefined,
    lastDispatchAt: undefined,
    executionTrace: undefined,
    error: undefined,
    updatedAt: Date.now(),
  };
  writeStoredOpsCommandQueue(queue.map((item) => (item.id === id ? retried : item)));
  return retried;
}

export function removeStoredOpsCommand(id: string): boolean {
  if (typeof window === 'undefined') return false;
  const queue = readStoredOpsCommandQueue();
  const next = queue.filter((item) => item.id !== id);
  if (next.length === queue.length) return false;
  writeStoredOpsCommandQueue(next);
  return true;
}

export function clearStoredTerminalOpsCommands(): number {
  if (typeof window === 'undefined') return 0;
  const queue = readStoredOpsCommandQueue();
  const next = queue.filter((item) => !OPS_COMMAND_TERMINAL_STATUS.has(item.status));
  writeStoredOpsCommandQueue(next);
  return queue.length - next.length;
}

export function attachTraceToOpsCommand(trace: ExecutionTraceStep): OpsCommandRequest | null {
  if (typeof window === 'undefined') return null;
  const queue = readStoredOpsCommandQueue();
  const candidates = queue
    .filter((item) => item.status === 'sent' && !item.executionTrace)
    .filter((item) => {
      const expected = item.expectedActionName ?? extractActionNameFromPrompt(item.prompt);
      if (!expected || expected !== trace.actionName) return false;
      const baseline = item.lastDispatchAt ?? item.updatedAt ?? item.createdAt;
      if (!Number.isFinite(baseline)) return false;
      return (
        trace.timestamp >= baseline - 60_000 &&
        trace.timestamp <= baseline + OPS_COMMAND_TRACE_MATCH_WINDOW_MS
      );
    })
    .sort((a, b) => {
      const aBaseline = a.lastDispatchAt ?? a.updatedAt ?? a.createdAt;
      const bBaseline = b.lastDispatchAt ?? b.updatedAt ?? b.createdAt;
      return Math.abs(trace.timestamp - aBaseline) - Math.abs(trace.timestamp - bBaseline);
    });

  const target = candidates[0];
  if (!target) return null;

  const updated: OpsCommandRequest = {
    ...target,
    expectedActionName: target.expectedActionName ?? extractActionNameFromPrompt(target.prompt),
    domain: target.domain ?? inferDomainFromActionName(trace.actionName),
    executionTrace: trace,
    updatedAt: Date.now(),
  };

  writeStoredOpsCommandQueue(queue.map((item) => (item.id === target.id ? updated : item)));
  if (updated.domain) {
    upsertDomainTrustScore(updated.domain, trace.success ? 'success' : 'failure');
  }
  return updated;
}

export function sweepStoredOpsCommandQueue(): OpsCommandRequest[] {
  if (typeof window === 'undefined') return [];
  const runtime = applyQueueRuntimePolicies(readStoredOpsCommandQueue());
  if (runtime.trustEvents.length > 0) {
    applyDomainTrustEvents(runtime.trustEvents);
  }
  if (runtime.changed) {
    writeStoredOpsCommandQueue(runtime.queue);
  }
  return runtime.queue;
}
