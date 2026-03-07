'use client';

import { useEffect, useMemo, useState } from 'react';
import { ShieldCheck, ShieldX, Timer, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  appendStoredPolicyEvent,
  clearStoredTerminalOpsCommands,
  enqueueStoredOpsCommand,
  readStoredAutoRemediation,
  readStoredBackendDomainTrustScores,
  readStoredCanaryPromotion,
  readStoredCanaryState,
  readStoredControlTick,
  readStoredDomainTrustScores,
  readStoredEvalBaselineSummary,
  readStoredEvalMetrics,
  readStoredEvalMetricsSummary,
  readStoredExecutionTraces,
  readStoredFeatureFlags,
  readStoredIncidentSnapshot,
  readStoredPlaybookReport,
  readStoredPolicyEvents,
  readStoredProvidersHealth,
  readStoredSloReport,
  readStoredTrustDriftAlertSignature,
  removeStoredOpsCommand,
  retryStoredOpsCommand,
  sweepStoredOpsCommandQueue,
  writeStoredTrustDriftAlertSignature,
} from '@/lib/orchestration-storage';
import type {
  DomainTrustScore,
  ExecutionTraceStep,
  OpsCommandRequest,
  OpsRiskTier,
  PolicyEvent,
} from '@/lib/types/realtime';

function formatDate(value: number) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(date);
}

function buildOpsActionPrompt(actionName: string, params?: Record<string, unknown>) {
  const json = params ? JSON.stringify(params) : '{}';
  return [
    'Use exatamente uma tool:',
    `action_name=${actionName}`,
    `params=${json}`,
    'Nao execute outras actions nesta resposta.',
  ].join('\n');
}

type CommandFilter = 'all' | 'pending' | 'dispatching' | 'sent' | 'failed';

interface OpsCommandPreset {
  id: string;
  label: string;
  prompt: string;
  domain: string;
  riskTier: OpsRiskTier;
  autoRetryOnNoEvidence?: boolean;
  maxAutoRetries?: number;
  noEvidenceTimeoutMs?: number;
  guarded?: boolean;
}

interface CommandTimingHint {
  elapsedMs: number;
  timeoutMs: number;
  remainingMs: number;
  overdue: boolean;
}

type DomainTrustComparisonState = 'aligned' | 'drift' | 'backend_only' | 'local_only';

interface DomainTrustComparison {
  domain: string;
  backend?: DomainTrustScore;
  local?: DomainTrustScore;
  scoreDelta: number;
  recommendationDeltaMs: number;
  retryDelta: number;
  state: DomainTrustComparisonState;
}

const DOMAIN_TRUST_DRIFT_THRESHOLD = 0.18;
const DOMAIN_TRUST_TIMEOUT_DRIFT_MS = 15_000;

function formatDurationShort(ms: number): string {
  if (ms <= 0) return '0s';
  const totalSeconds = Math.ceil(ms / 1000);
  if (totalSeconds < 60) return `${totalSeconds}s`;
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  if (minutes < 60) return `${minutes}m${seconds > 0 ? ` ${seconds}s` : ''}`;
  const hours = Math.floor(minutes / 60);
  const remMinutes = minutes % 60;
  return `${hours}h${remMinutes > 0 ? ` ${remMinutes}m` : ''}`;
}

function getCommandTimingHint(command: OpsCommandRequest): CommandTimingHint | null {
  if (command.status !== 'sent' || command.executionTrace) return null;
  const baseline = command.lastDispatchAt ?? command.updatedAt;
  if (!Number.isFinite(baseline)) return null;
  const timeoutMs =
    typeof command.noEvidenceTimeoutMs === 'number' && command.noEvidenceTimeoutMs > 0
      ? command.noEvidenceTimeoutMs
      : 45_000;
  const elapsedMs = Math.max(0, Date.now() - baseline);
  const remainingMs = Math.max(0, timeoutMs - elapsedMs);
  return {
    elapsedMs,
    timeoutMs,
    remainingMs,
    overdue: elapsedMs >= timeoutMs,
  };
}

function formatUpdatedAge(timestamp?: number): string {
  if (!timestamp || !Number.isFinite(timestamp)) return '-';
  const deltaMs = Math.max(0, Date.now() - timestamp);
  return formatDurationShort(deltaMs);
}

function buildDomainTrustComparisons(
  backendScores: DomainTrustScore[],
  localScores: DomainTrustScore[]
): DomainTrustComparison[] {
  const backendByDomain = new Map(backendScores.map((score) => [score.domain, score]));
  const localByDomain = new Map(localScores.map((score) => [score.domain, score]));
  const allDomains = new Set([...backendByDomain.keys(), ...localByDomain.keys()]);
  return Array.from(allDomains)
    .sort((a, b) => a.localeCompare(b))
    .map((domain) => {
      const backend = backendByDomain.get(domain);
      const local = localByDomain.get(domain);
      const scoreDelta = Math.abs((backend?.score ?? 0) - (local?.score ?? 0));
      const recommendationDeltaMs = Math.abs(
        (backend?.recommendation.timeoutMs ?? 0) - (local?.recommendation.timeoutMs ?? 0)
      );
      const retryDelta = Math.abs(
        (backend?.recommendation.maxAutoRetries ?? 0) - (local?.recommendation.maxAutoRetries ?? 0)
      );
      let state: DomainTrustComparisonState = 'aligned';
      if (backend && !local) {
        state = 'backend_only';
      } else if (!backend && local) {
        state = 'local_only';
      } else if (
        scoreDelta >= DOMAIN_TRUST_DRIFT_THRESHOLD ||
        recommendationDeltaMs >= DOMAIN_TRUST_TIMEOUT_DRIFT_MS ||
        retryDelta > 0
      ) {
        state = 'drift';
      }
      return {
        domain,
        backend,
        local,
        scoreDelta,
        recommendationDeltaMs,
        retryDelta,
        state,
      };
    });
}

function buildTrustDriftSignature(items: DomainTrustComparison[]): string {
  return items
    .filter((item) => item.state === 'drift')
    .map(
      (item) =>
        `${item.domain}:${item.backend?.score.toFixed(2) ?? '-'}:${item.local?.score.toFixed(2) ?? '-'}`
    )
    .join('|');
}

function buildTrustDriftRows(items: DomainTrustComparison[]) {
  return items
    .filter((item) => item.state === 'drift')
    .map((item) => ({
      domain: item.domain,
      active: true,
      state: item.state,
      score_delta: Number(item.scoreDelta.toFixed(4)),
      recommendation_delta_ms: item.recommendationDeltaMs,
      retry_delta: item.retryDelta,
    }));
}

const OPS_SAFE_PRESETS: OpsCommandPreset[] = [
  {
    id: 'policy-domain-trust',
    label: 'Trust score backend',
    prompt: buildOpsActionPrompt('policy_domain_trust_status'),
    domain: 'ops',
    riskTier: 'R0',
    autoRetryOnNoEvidence: true,
    maxAutoRetries: 1,
    noEvidenceTimeoutMs: 30_000,
  },
  {
    id: 'incident-snapshot',
    label: 'Snapshot incidente',
    prompt: buildOpsActionPrompt('ops_incident_snapshot'),
    domain: 'ops',
    riskTier: 'R0',
    autoRetryOnNoEvidence: true,
    maxAutoRetries: 1,
    noEvidenceTimeoutMs: 30_000,
  },
  {
    id: 'canary-status',
    label: 'Status canario',
    prompt: buildOpsActionPrompt('ops_canary_status'),
    domain: 'ops',
    riskTier: 'R0',
    autoRetryOnNoEvidence: true,
    maxAutoRetries: 1,
    noEvidenceTimeoutMs: 30_000,
  },
  {
    id: 'control-loop-dry-run',
    label: 'Control loop (dry-run)',
    prompt: buildOpsActionPrompt('ops_control_loop_tick', { dry_run: true }),
    domain: 'ops',
    riskTier: 'R1',
    autoRetryOnNoEvidence: true,
    maxAutoRetries: 1,
    noEvidenceTimeoutMs: 45_000,
  },
  {
    id: 'auto-remediation-dry-run',
    label: 'Auto-remediacao (dry-run)',
    prompt: buildOpsActionPrompt('ops_auto_remediate', { dry_run: true }),
    domain: 'ops',
    riskTier: 'R1',
    autoRetryOnNoEvidence: true,
    maxAutoRetries: 1,
    noEvidenceTimeoutMs: 45_000,
  },
  {
    id: 'canary-promote-dry-run',
    label: 'Promover canario (dry-run)',
    prompt: buildOpsActionPrompt('ops_canary_promote', { dry_run: true }),
    domain: 'ops',
    riskTier: 'R1',
    autoRetryOnNoEvidence: true,
    maxAutoRetries: 1,
    noEvidenceTimeoutMs: 45_000,
  },
  {
    id: 'flags-status',
    label: 'Flags status',
    prompt: buildOpsActionPrompt('ops_feature_flags_status'),
    domain: 'ops',
    riskTier: 'R0',
    autoRetryOnNoEvidence: true,
    maxAutoRetries: 1,
    noEvidenceTimeoutMs: 30_000,
  },
];

const OPS_GUARDED_PRESETS: OpsCommandPreset[] = [
  {
    id: 'control-loop-apply',
    label: 'Control loop (aplicar)',
    prompt: buildOpsActionPrompt('ops_control_loop_tick', { dry_run: false }),
    domain: 'ops',
    riskTier: 'R3',
    autoRetryOnNoEvidence: false,
    maxAutoRetries: 0,
    noEvidenceTimeoutMs: 60_000,
    guarded: true,
  },
  {
    id: 'auto-remediation-apply',
    label: 'Auto-remediacao (aplicar)',
    prompt: buildOpsActionPrompt('ops_auto_remediate', { dry_run: false }),
    domain: 'ops',
    riskTier: 'R3',
    autoRetryOnNoEvidence: false,
    maxAutoRetries: 0,
    noEvidenceTimeoutMs: 60_000,
    guarded: true,
  },
  {
    id: 'canary-pause',
    label: 'Pausar rollout canario',
    prompt: buildOpsActionPrompt('ops_canary_rollout_set', { operation: 'pause', dry_run: false }),
    domain: 'ops',
    riskTier: 'R3',
    autoRetryOnNoEvidence: false,
    maxAutoRetries: 0,
    noEvidenceTimeoutMs: 60_000,
    guarded: true,
  },
  {
    id: 'killswitch-enable',
    label: 'Ativar kill switch global',
    prompt: buildOpsActionPrompt('autonomy_killswitch', {
      operation: 'enable',
      reason: 'manual_trust_center',
    }),
    domain: 'ops',
    riskTier: 'R3',
    autoRetryOnNoEvidence: false,
    maxAutoRetries: 0,
    noEvidenceTimeoutMs: 60_000,
    guarded: true,
  },
];

const GUARD_CONFIRM_TEXT = 'CONFIRMAR';
const COMMON_AUTONOMY_DOMAINS = ['ops', 'shell', 'home', 'whatsapp'];

function extractDomainAutonomyModes(snapshot: Record<string, unknown> | null) {
  const rows = snapshot?.domain_autonomy_modes;
  if (!Array.isArray(rows)) {
    return [] as Array<{ domain: string; mode: string }>;
  }
  return rows
    .map((row) => {
      if (!row || typeof row !== 'object') {
        return null;
      }
      const payload = row as Record<string, unknown>;
      const domain = String(payload.domain ?? '')
        .trim()
        .toLowerCase();
      const mode = String(payload.mode ?? '')
        .trim()
        .toLowerCase();
      if (!domain || !mode) {
        return null;
      }
      return { domain, mode };
    })
    .filter((row): row is { domain: string; mode: string } => Boolean(row));
}

function extractDomainAutonomyStatuses(snapshot: Record<string, unknown> | null) {
  const rows = snapshot?.domain_autonomy_status;
  if (!Array.isArray(rows)) {
    return [] as Array<{
      domain: string;
      autonomyMode: string;
      domainAutonomyMode: string | null;
      effectiveAutonomyMode: string;
      containmentReason: string | null;
      containmentReasons: string[];
      containmentSource: string | null;
      domainAutonomyUpdatedAt: string | null;
      trustDriftActive: boolean;
      autonomyNoticeUnconfirmed: number;
    }>;
  }
  return rows
    .map((row) => {
      if (!row || typeof row !== 'object') {
        return null;
      }
      const payload = row as Record<string, unknown>;
      const domain = String(payload.domain ?? '')
        .trim()
        .toLowerCase();
      if (!domain) {
        return null;
      }
      const containmentReasons = Array.isArray(payload.containment_reasons)
        ? payload.containment_reasons
            .map((item) => String(item ?? '').trim())
            .filter((item) => Boolean(item))
        : [];
      return {
        domain,
        autonomyMode:
          String(payload.autonomy_mode ?? '')
            .trim()
            .toLowerCase() || 'aggressive',
        domainAutonomyMode:
          String(payload.domain_autonomy_mode ?? '')
            .trim()
            .toLowerCase() || null,
        effectiveAutonomyMode:
          String(payload.effective_autonomy_mode ?? '')
            .trim()
            .toLowerCase() || 'aggressive',
        containmentReason: String(payload.containment_reason ?? '').trim() || null,
        containmentReasons,
        containmentSource: String(payload.containment_source ?? '').trim() || null,
        domainAutonomyUpdatedAt: String(payload.domain_autonomy_updated_at ?? '').trim() || null,
        trustDriftActive: Boolean(payload.trust_drift_active),
        autonomyNoticeUnconfirmed: Number(payload.autonomy_notice_unconfirmed ?? 0) || 0,
      };
    })
    .filter(
      (
        row
      ): row is {
        domain: string;
        autonomyMode: string;
        domainAutonomyMode: string | null;
        effectiveAutonomyMode: string;
        containmentReason: string | null;
        containmentReasons: string[];
        containmentSource: string | null;
        domainAutonomyUpdatedAt: string | null;
        trustDriftActive: boolean;
        autonomyNoticeUnconfirmed: number;
      } => Boolean(row)
    );
}

function buildDomainAutonomyPreset(
  domain: string,
  operation: 'degrade' | 'restore'
): OpsCommandPreset {
  const normalizedDomain = domain.trim().toLowerCase();
  const playbook = operation === 'degrade' ? 'degrade_domain_autonomy' : 'restore_domain_autonomy';
  return {
    id: `domain-autonomy-${operation}-${normalizedDomain}`,
    label:
      operation === 'degrade'
        ? `Degradar autonomia: ${normalizedDomain}`
        : `Restaurar autonomia: ${normalizedDomain}`,
    prompt: buildOpsActionPrompt('ops_apply_playbook', {
      playbook,
      domain: normalizedDomain,
      dry_run: false,
      reason: `manual_trust_center_${playbook}`,
    }),
    domain: normalizedDomain,
    riskTier: 'R3',
    autoRetryOnNoEvidence: false,
    maxAutoRetries: 0,
    noEvidenceTimeoutMs: 60_000,
    guarded: true,
  };
}

export function TrustCenterView() {
  const [policyEvents, setPolicyEvents] = useState<PolicyEvent[]>([]);
  const [traces, setTraces] = useState<ExecutionTraceStep[]>([]);
  const [evalBaselineSummary, setEvalBaselineSummary] = useState<Record<string, unknown> | null>(
    null
  );
  const [evalMetrics, setEvalMetrics] = useState<Array<Record<string, unknown>>>([]);
  const [evalMetricsSummary, setEvalMetricsSummary] = useState<Record<string, unknown> | null>(
    null
  );
  const [sloReport, setSloReport] = useState<Record<string, unknown> | null>(null);
  const [providersHealth, setProvidersHealth] = useState<Array<Record<string, unknown>>>([]);
  const [featureFlags, setFeatureFlags] = useState<Record<string, unknown> | null>(null);
  const [canaryState, setCanaryState] = useState<Record<string, unknown> | null>(null);
  const [incidentSnapshot, setIncidentSnapshot] = useState<Record<string, unknown> | null>(null);
  const [playbookReport, setPlaybookReport] = useState<Record<string, unknown> | null>(null);
  const [autoRemediation, setAutoRemediation] = useState<Record<string, unknown> | null>(null);
  const [canaryPromotion, setCanaryPromotion] = useState<Record<string, unknown> | null>(null);
  const [controlTick, setControlTick] = useState<Record<string, unknown> | null>(null);
  const [opsCommands, setOpsCommands] = useState<OpsCommandRequest[]>([]);
  const [backendDomainTrustScores, setBackendDomainTrustScores] = useState<DomainTrustScore[]>([]);
  const [domainTrustScores, setDomainTrustScores] = useState<DomainTrustScore[]>([]);
  const [commandFilter, setCommandFilter] = useState<CommandFilter>('all');
  const [armedGuardedPreset, setArmedGuardedPreset] = useState<OpsCommandPreset | null>(null);
  const [guardPhrase, setGuardPhrase] = useState('');

  useEffect(() => {
    const sync = () => {
      setPolicyEvents(readStoredPolicyEvents());
      setTraces(readStoredExecutionTraces());
      setEvalBaselineSummary(readStoredEvalBaselineSummary());
      setEvalMetrics(readStoredEvalMetrics());
      setEvalMetricsSummary(readStoredEvalMetricsSummary());
      setSloReport(readStoredSloReport());
      setProvidersHealth(readStoredProvidersHealth());
      setFeatureFlags(readStoredFeatureFlags());
      setCanaryState(readStoredCanaryState());
      setIncidentSnapshot(readStoredIncidentSnapshot());
      setPlaybookReport(readStoredPlaybookReport());
      setAutoRemediation(readStoredAutoRemediation());
      setCanaryPromotion(readStoredCanaryPromotion());
      setControlTick(readStoredControlTick());
      setOpsCommands(sweepStoredOpsCommandQueue());
      setBackendDomainTrustScores(readStoredBackendDomainTrustScores());
      setDomainTrustScores(readStoredDomainTrustScores());
    };
    sync();
    window.addEventListener('storage', sync);
    const timer = window.setInterval(sync, 3000);
    return () => {
      window.removeEventListener('storage', sync);
      window.clearInterval(timer);
    };
  }, []);

  const queueOpsCommand = (preset: OpsCommandPreset) => {
    const now = Date.now();
    const random = Math.random().toString(36).slice(2, 8);
    enqueueStoredOpsCommand({
      id: `ops-${now}-${random}`,
      label: preset.label,
      prompt: preset.prompt,
      domain: preset.domain,
      riskTier: preset.riskTier,
      autoRetryOnNoEvidence: preset.autoRetryOnNoEvidence,
      maxAutoRetries: preset.maxAutoRetries,
      noEvidenceTimeoutMs: preset.noEvidenceTimeoutMs,
      status: 'pending',
      createdAt: now,
    });
    setOpsCommands(sweepStoredOpsCommandQueue());
  };

  const queueGuardedPreset = () => {
    if (!armedGuardedPreset || guardPhrase.trim().toUpperCase() !== GUARD_CONFIRM_TEXT) {
      return;
    }
    queueOpsCommand(armedGuardedPreset);
    setArmedGuardedPreset(null);
    setGuardPhrase('');
  };

  const retryCommand = (id: string) => {
    retryStoredOpsCommand(id);
    setOpsCommands(sweepStoredOpsCommandQueue());
  };

  const removeCommand = (id: string) => {
    removeStoredOpsCommand(id);
    setOpsCommands(sweepStoredOpsCommandQueue());
  };

  const clearTerminalCommands = () => {
    clearStoredTerminalOpsCommands();
    setOpsCommands(sweepStoredOpsCommandQueue());
  };

  const filteredCommands = opsCommands.filter((command) =>
    commandFilter === 'all' ? true : command.status === commandFilter
  );
  const effectiveDomainTrustScores =
    backendDomainTrustScores.length > 0 ? backendDomainTrustScores : domainTrustScores;
  const trustComparisons = useMemo(
    () => buildDomainTrustComparisons(backendDomainTrustScores, domainTrustScores),
    [backendDomainTrustScores, domainTrustScores]
  );
  const domainAutonomyModes = useMemo(
    () => extractDomainAutonomyModes(incidentSnapshot),
    [incidentSnapshot]
  );
  const domainAutonomyStatuses = useMemo(
    () => extractDomainAutonomyStatuses(incidentSnapshot),
    [incidentSnapshot]
  );
  const domainAutonomyCandidates = useMemo(() => {
    const domains = new Set(COMMON_AUTONOMY_DOMAINS);
    domainAutonomyModes.forEach((row) => domains.add(row.domain));
    domainAutonomyStatuses.forEach((row) => domains.add(row.domain));
    backendDomainTrustScores.forEach((row) => domains.add(row.domain));
    domainTrustScores.forEach((row) => domains.add(row.domain));
    const trustDriftDomains =
      ((incidentSnapshot?.trust_drift as Record<string, unknown> | undefined)?.domains as
        | Array<Record<string, unknown>>
        | undefined) ?? [];
    trustDriftDomains.forEach((row) => {
      const domain = String(row.domain ?? '')
        .trim()
        .toLowerCase();
      if (domain) {
        domains.add(domain);
      }
    });
    return Array.from(domains).sort((a, b) => a.localeCompare(b));
  }, [
    backendDomainTrustScores,
    domainAutonomyModes,
    domainAutonomyStatuses,
    domainTrustScores,
    incidentSnapshot,
  ]);
  const driftComparisons = trustComparisons.filter((item) => item.state === 'drift');
  const backendOnlyComparisons = trustComparisons.filter((item) => item.state === 'backend_only');
  const localOnlyComparisons = trustComparisons.filter((item) => item.state === 'local_only');

  useEffect(() => {
    if (backendDomainTrustScores.length === 0 || domainTrustScores.length === 0) {
      return;
    }
    const nextSignature =
      driftComparisons.length > 0 ? buildTrustDriftSignature(driftComparisons) : null;
    const previousSignature = readStoredTrustDriftAlertSignature();
    if (nextSignature && nextSignature !== previousSignature) {
      const nextEvents = appendStoredPolicyEvent({
        action_name: 'policy_domain_trust_drift_monitor',
        event_type: 'trust_drift_detected',
        source: 'synthetic',
        risk: 'R1',
        decision: 'allow_with_log',
        reason: `${String(driftComparisons.length)} dominios com drift entre trust backend e local.`,
        timestamp: Date.now(),
        signature: nextSignature,
        metadata: {
          drift_domains: driftComparisons.map((item) => item.domain),
          drift_count: driftComparisons.length,
        },
      });
      setPolicyEvents(nextEvents);
      const now = Date.now();
      enqueueStoredOpsCommand({
        id: `ops-trust-drift-sync-${now}`,
        label: 'Sync trust drift backend',
        prompt: buildOpsActionPrompt('policy_trust_drift_report', {
          signature: nextSignature,
          rows: buildTrustDriftRows(driftComparisons),
        }),
        domain: 'ops',
        riskTier: 'R0',
        autoRetryOnNoEvidence: true,
        maxAutoRetries: 1,
        noEvidenceTimeoutMs: 30_000,
        status: 'pending',
        createdAt: now,
      });
      setOpsCommands(sweepStoredOpsCommandQueue());
      writeStoredTrustDriftAlertSignature(nextSignature);
      return;
    }
    if (!nextSignature && previousSignature) {
      const nextEvents = appendStoredPolicyEvent({
        action_name: 'policy_domain_trust_drift_monitor',
        event_type: 'trust_drift_resolved',
        source: 'synthetic',
        risk: 'R0',
        decision: 'allow_with_log',
        reason: 'Drift de trust entre backend e local resolvido.',
        timestamp: Date.now(),
        signature: `resolved:${previousSignature}`,
      });
      setPolicyEvents(nextEvents);
      const now = Date.now();
      enqueueStoredOpsCommand({
        id: `ops-trust-drift-sync-${now}`,
        label: 'Sync trust drift backend (resolved)',
        prompt: buildOpsActionPrompt('policy_trust_drift_report', {
          signature: `resolved:${previousSignature}`,
          rows: [],
        }),
        domain: 'ops',
        riskTier: 'R0',
        autoRetryOnNoEvidence: true,
        maxAutoRetries: 1,
        noEvidenceTimeoutMs: 30_000,
        status: 'pending',
        createdAt: now,
      });
      setOpsCommands(sweepStoredOpsCommandQueue());
      writeStoredTrustDriftAlertSignature(null);
    }
  }, [backendDomainTrustScores.length, domainTrustScores.length, driftComparisons]);

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(248,113,113,0.1),_transparent_30%),radial-gradient(circle_at_top_right,_rgba(250,204,21,0.1),_transparent_28%),linear-gradient(180deg,#08050a_0%,#151024_100%)] px-4 py-8 text-white">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="rounded-[2rem] border border-white/10 bg-black/30 px-6 py-5 backdrop-blur-xl">
          <div className="mb-2 flex items-center gap-2 text-amber-200">
            <ShieldCheck className="size-5" />
            <span className="text-xs font-semibold tracking-[0.24em] uppercase">
              Jarvez Trust Center
            </span>
          </div>
          <h1 className="text-2xl font-semibold">Politicas, risco e trilhas de execucao</h1>
          <p className="mt-1 text-sm text-white/60">
            Rastreabilidade de decisoes de politica e evidencias de execucao das actions.
          </p>
        </header>

        <section className="grid gap-6 lg:grid-cols-2">
          <article className="rounded-[2rem] border border-white/10 bg-black/25 p-5 backdrop-blur-xl">
            <div className="mb-3 flex items-center gap-2 text-cyan-200">
              <Zap className="size-4" />
              <span className="text-xs font-semibold tracking-[0.2em] uppercase">
                Eventos de politica
              </span>
            </div>
            {policyEvents.length > 0 ? (
              <div className="space-y-3">
                {policyEvents.slice(0, 20).map((event, index) => (
                  <div
                    key={`${event.signature ?? event.action_name ?? 'action'}-${index}`}
                    className="rounded-[1.25rem] border border-white/10 bg-white/[0.03] px-4 py-3 text-sm"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-semibold">{event.action_name ?? 'action'}</p>
                      <p className="text-xs text-white/50">
                        {event.timestamp ? formatDate(event.timestamp) : '-'}
                      </p>
                    </div>
                    <p className="text-white/70">
                      risco={event.risk ?? '-'} | decisao={event.decision ?? '-'} | modo=
                      {event.autonomy_mode ?? '-'}
                    </p>
                    <p className="text-white/50">
                      source={event.source ?? 'backend'} | tipo={event.event_type ?? 'policy'}
                      {event.domain ? ` | domain=${event.domain}` : ''}
                    </p>
                    {event.reason ? <p className="mt-1 text-white/65">{event.reason}</p> : null}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-white/60">Sem eventos de politica registrados.</p>
            )}
          </article>

          <article className="rounded-[2rem] border border-white/10 bg-black/25 p-5 backdrop-blur-xl">
            <div className="mb-3 flex items-center gap-2 text-amber-300">
              <Timer className="size-4" />
              <span className="text-xs font-semibold tracking-[0.2em] uppercase">
                Trilhas de execucao
              </span>
            </div>
            {traces.length > 0 ? (
              <div className="space-y-3">
                {traces.slice(0, 25).map((trace) => (
                  <div
                    key={trace.traceId}
                    className="rounded-[1.25rem] border border-white/10 bg-white/[0.03] px-4 py-3 text-sm"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-semibold">{trace.actionName}</p>
                      <p className="text-xs text-white/60">{formatDate(trace.timestamp)}</p>
                    </div>
                    <p className="text-white/70">
                      trace={trace.traceId} | risk={trace.risk ?? '-'} | decision=
                      {trace.policyDecision ?? '-'}
                    </p>
                    <p className="text-white/70">
                      provider={trace.provider ?? '-'} | fallback=
                      {trace.fallbackUsed ? 'sim' : 'nao'}
                    </p>
                    <p className={trace.success ? 'text-emerald-300' : 'text-rose-300'}>
                      {trace.success ? (
                        <ShieldCheck className="mr-1 inline size-3.5" />
                      ) : (
                        <ShieldX className="mr-1 inline size-3.5" />
                      )}
                      {trace.message}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-white/60">Sem trilhas de execucao registradas.</p>
            )}
          </article>
        </section>

        <section className="rounded-[2rem] border border-white/10 bg-black/25 p-5 backdrop-blur-xl">
          <div className="mb-3 flex items-center gap-2 text-cyan-200">
            <Zap className="size-4" />
            <span className="text-xs font-semibold tracking-[0.2em] uppercase">
              Baseline e Metrics
            </span>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded-[1.25rem] border border-white/10 bg-white/[0.03] p-4 text-sm">
              <p className="text-white/55">Baseline score</p>
              <p className="mt-1 text-xl font-semibold text-white">
                {typeof evalBaselineSummary?.score === 'number'
                  ? String(evalBaselineSummary.score)
                  : '-'}
              </p>
            </div>
            <div className="rounded-[1.25rem] border border-white/10 bg-white/[0.03] p-4 text-sm">
              <p className="text-white/55">Cenarios</p>
              <p className="mt-1 text-xl font-semibold text-white">
                {typeof evalBaselineSummary?.total === 'number'
                  ? String(evalBaselineSummary.total)
                  : '-'}
              </p>
            </div>
            <div className="rounded-[1.25rem] border border-white/10 bg-white/[0.03] p-4 text-sm">
              <p className="text-white/55">Metrics salvas</p>
              <p className="mt-1 text-xl font-semibold text-white">{String(evalMetrics.length)}</p>
            </div>
          </div>
          {evalBaselineSummary ? (
            <p className="mt-3 text-xs text-white/60">
              Ultimo baseline em{' '}
              {typeof evalBaselineSummary.ran_at === 'string' ? evalBaselineSummary.ran_at : '-'}
            </p>
          ) : (
            <p className="mt-3 text-xs text-white/60">
              Execute `evals_run_baseline` para preencher esta secao.
            </p>
          )}
        </section>

        <section className="rounded-[2rem] border border-white/10 bg-black/25 p-5 backdrop-blur-xl">
          <div className="mb-3 flex items-center gap-2 text-amber-300">
            <ShieldCheck className="size-4" />
            <span className="text-xs font-semibold tracking-[0.2em] uppercase">
              SLO operacional
            </span>
          </div>
          {sloReport ? (
            <div className="grid gap-3 md:grid-cols-6">
              <div className="rounded-[1.25rem] border border-white/10 bg-white/[0.03] p-4 text-sm">
                <p className="text-white/55">p95 geral (ms)</p>
                <p className="mt-1 text-xl font-semibold text-white">
                  {String(
                    ((sloReport.latency as Record<string, unknown> | undefined)?.overall_p95_ms as
                      | number
                      | undefined) ?? 0
                  )}
                </p>
              </div>
              <div className="rounded-[1.25rem] border border-white/10 bg-white/[0.03] p-4 text-sm">
                <p className="text-white/55">Sucesso baixo risco</p>
                <p className="mt-1 text-xl font-semibold text-white">
                  {String(
                    ((sloReport.reliability as Record<string, unknown> | undefined)
                      ?.low_risk_success_rate as number | undefined) ?? 0
                  )}
                </p>
              </div>
              <div className="rounded-[1.25rem] border border-white/10 bg-white/[0.03] p-4 text-sm">
                <p className="text-white/55">False-success proxy</p>
                <p className="mt-1 text-xl font-semibold text-white">
                  {String(
                    ((sloReport.reliability as Record<string, unknown> | undefined)
                      ?.false_success_proxy_rate as number | undefined) ?? 0
                  )}
                </p>
              </div>
              <div className="rounded-[1.25rem] border border-white/10 bg-white/[0.03] p-4 text-sm">
                <p className="text-white/55">Trust drift ativo</p>
                <p className="mt-1 text-xl font-semibold text-white">
                  {String(
                    ((sloReport.reliability as Record<string, unknown> | undefined)
                      ?.trust_drift_active_rate as number | undefined) ?? 0
                  )}
                </p>
              </div>
              <div className="rounded-[1.25rem] border border-white/10 bg-white/[0.03] p-4 text-sm">
                <p className="text-white/55">Notice via agent audio</p>
                <p className="mt-1 text-xl font-semibold text-white">
                  {String(
                    ((sloReport.reliability as Record<string, unknown> | undefined)
                      ?.autonomy_notice_agent_audio_rate as number | undefined) ?? 0
                  )}
                </p>
              </div>
              <div className="rounded-[1.25rem] border border-white/10 bg-white/[0.03] p-4 text-sm">
                <p className="text-white/55">Notice via browser TTS</p>
                <p className="mt-1 text-xl font-semibold text-white">
                  {String(
                    ((sloReport.reliability as Record<string, unknown> | undefined)
                      ?.autonomy_notice_browser_tts_rate as number | undefined) ?? 0
                  )}
                </p>
              </div>
              <div className="rounded-[1.25rem] border border-white/10 bg-white/[0.03] p-4 text-sm">
                <p className="text-white/55">Notice nao confirmado</p>
                <p className="mt-1 text-xl font-semibold text-white">
                  {String(
                    ((sloReport.reliability as Record<string, unknown> | undefined)
                      ?.autonomy_notice_unconfirmed_rate as number | undefined) ?? 0
                  )}
                </p>
              </div>
              <div className="rounded-[1.25rem] border border-white/10 bg-white/[0.03] p-4 text-sm md:col-span-6">
                <p className="text-white/55">Status metas</p>
                <p className="mt-1 text-white/80">
                  false_success=
                  {String(
                    ((sloReport.slo_pass as Record<string, unknown> | undefined)?.false_success as
                      | boolean
                      | undefined) ?? false
                  )}
                  {' | '}
                  low_risk_success=
                  {String(
                    ((sloReport.slo_pass as Record<string, unknown> | undefined)
                      ?.low_risk_success as boolean | undefined) ?? false
                  )}
                  {' | '}
                  fallback_p95=
                  {String(
                    ((sloReport.slo_pass as Record<string, unknown> | undefined)?.fallback_p95 as
                      | boolean
                      | undefined) ?? false
                  )}
                </p>
              </div>
            </div>
          ) : (
            <p className="text-sm text-white/60">
              Use `evals_slo_report` para calcular e exibir os indicadores.
            </p>
          )}
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <article className="rounded-[2rem] border border-white/10 bg-black/25 p-5 backdrop-blur-xl">
            <div className="mb-3 flex items-center gap-2 text-cyan-200">
              <Zap className="size-4" />
              <span className="text-xs font-semibold tracking-[0.2em] uppercase">
                Resumo por provider/risco
              </span>
            </div>
            {evalMetricsSummary ? (
              <div className="space-y-4 text-sm">
                <div className="rounded-[1.25rem] border border-white/10 bg-white/[0.03] p-4">
                  <p className="text-white/55">Total actions observadas</p>
                  <p className="text-xl font-semibold text-white">
                    {typeof evalMetricsSummary.total_actions === 'number'
                      ? String(evalMetricsSummary.total_actions)
                      : '-'}
                  </p>
                </div>
                <div className="space-y-2">
                  <p className="text-xs font-semibold tracking-[0.2em] text-white/55 uppercase">
                    Providers
                  </p>
                  {Object.entries(
                    (evalMetricsSummary.providers as Record<string, Record<string, number>>) ?? {}
                  ).map(([provider, values]) => (
                    <div
                      key={provider}
                      className="rounded-[1rem] border border-white/10 bg-white/[0.03] px-3 py-2"
                    >
                      <p className="font-semibold">{provider}</p>
                      <p className="text-white/70">
                        total={String(values?.total ?? 0)} | success={String(values?.success ?? 0)}{' '}
                        | failed=
                        {String(values?.failed ?? 0)}
                      </p>
                    </div>
                  ))}
                </div>
                <div className="space-y-2">
                  <p className="text-xs font-semibold tracking-[0.2em] text-white/55 uppercase">
                    Risco
                  </p>
                  {Object.entries(
                    (evalMetricsSummary.risk_tiers as Record<string, Record<string, number>>) ?? {}
                  ).map(([risk, values]) => (
                    <div
                      key={risk}
                      className="rounded-[1rem] border border-white/10 bg-white/[0.03] px-3 py-2"
                    >
                      <p className="font-semibold">{risk}</p>
                      <p className="text-white/70">
                        total={String(values?.total ?? 0)} | success={String(values?.success ?? 0)}{' '}
                        | failed=
                        {String(values?.failed ?? 0)}
                      </p>
                    </div>
                  ))}
                </div>
                <div className="space-y-2">
                  <p className="text-xs font-semibold tracking-[0.2em] text-white/55 uppercase">
                    Trust drift
                  </p>
                  <div className="rounded-[1rem] border border-white/10 bg-white/[0.03] px-3 py-2">
                    <p className="font-semibold">Resumo</p>
                    <p className="text-white/70">
                      active_total=
                      {String(
                        ((evalMetricsSummary.trust_drift as Record<string, unknown> | undefined)
                          ?.active_total as number | undefined) ?? 0
                      )}{' '}
                      | inactive_total=
                      {String(
                        ((evalMetricsSummary.trust_drift as Record<string, unknown> | undefined)
                          ?.inactive_total as number | undefined) ?? 0
                      )}
                    </p>
                  </div>
                  {Object.entries(
                    ((evalMetricsSummary.trust_drift as Record<string, unknown> | undefined)
                      ?.by_domain as Record<string, Record<string, number>>) ?? {}
                  ).map(([domain, values]) => (
                    <div
                      key={domain}
                      className="rounded-[1rem] border border-white/10 bg-white/[0.03] px-3 py-2"
                    >
                      <p className="font-semibold">{domain}</p>
                      <p className="text-white/70">
                        total={String(values?.total ?? 0)} | success={String(values?.success ?? 0)}{' '}
                        | failed=
                        {String(values?.failed ?? 0)}
                      </p>
                    </div>
                  ))}
                </div>
                <div className="space-y-2">
                  <p className="text-xs font-semibold tracking-[0.2em] text-white/55 uppercase">
                    Autonomy notice
                  </p>
                  <div className="rounded-[1rem] border border-white/10 bg-white/[0.03] px-3 py-2">
                    <p className="font-semibold">Resumo</p>
                    <p className="text-white/70">
                      active_total=
                      {String(
                        ((evalMetricsSummary.autonomy_notice as Record<string, unknown> | undefined)
                          ?.active_total as number | undefined) ?? 0
                      )}{' '}
                      | inactive_total=
                      {String(
                        ((evalMetricsSummary.autonomy_notice as Record<string, unknown> | undefined)
                          ?.inactive_total as number | undefined) ?? 0
                      )}
                    </p>
                  </div>
                  {Object.entries(
                    ((evalMetricsSummary.autonomy_notice as Record<string, unknown> | undefined)
                      ?.by_channel as Record<string, Record<string, number>>) ?? {}
                  ).map(([channel, values]) => (
                    <div
                      key={channel}
                      className="rounded-[1rem] border border-white/10 bg-white/[0.03] px-3 py-2"
                    >
                      <p className="font-semibold">{channel}</p>
                      <p className="text-white/70">
                        total={String(values?.total ?? 0)} | success={String(values?.success ?? 0)}{' '}
                        | failed=
                        {String(values?.failed ?? 0)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-sm text-white/60">
                Execute `evals_metrics_summary` para preencher este bloco.
              </p>
            )}
          </article>

          <article className="rounded-[2rem] border border-white/10 bg-black/25 p-5 backdrop-blur-xl">
            <div className="mb-3 flex items-center gap-2 text-amber-300">
              <Timer className="size-4" />
              <span className="text-xs font-semibold tracking-[0.2em] uppercase">
                Providers e feature flags
              </span>
            </div>
            <div className="space-y-2">
              {providersHealth.length > 0 ? (
                providersHealth.map((row, index) => (
                  <div
                    key={`${String(row.provider ?? 'provider')}-${index}`}
                    className="rounded-[1rem] border border-white/10 bg-white/[0.03] px-3 py-2 text-sm"
                  >
                    <p className="font-semibold">{String(row.provider ?? 'provider')}</p>
                    <p className="text-white/70">
                      status={String(row.status ?? '-')} | configured=
                      {String(Boolean(row.configured))}
                      {row.ping_ok !== undefined
                        ? ` | ping_ok=${String(Boolean(row.ping_ok))}`
                        : ''}
                    </p>
                    {typeof row.error === 'string' && row.error ? (
                      <p className="text-rose-300">{row.error}</p>
                    ) : null}
                  </div>
                ))
              ) : (
                <p className="text-sm text-white/60">
                  Use `providers_health_check` para preencher este bloco.
                </p>
              )}
            </div>
            <div className="mt-4 rounded-[1rem] border border-white/10 bg-white/[0.03] p-3 text-xs text-white/70">
              <p className="mb-1 font-semibold tracking-[0.2em] text-white/55 uppercase">
                Feature flags
              </p>
              <pre className="overflow-x-auto whitespace-pre-wrap">
                {featureFlags
                  ? JSON.stringify(featureFlags, null, 2)
                  : 'Use ops_feature_flags_status para carregar.'}
              </pre>
            </div>
            <div className="mt-3 rounded-[1rem] border border-white/10 bg-white/[0.03] p-3 text-xs text-white/70">
              <p className="mb-1 font-semibold tracking-[0.2em] text-white/55 uppercase">Canario</p>
              <pre className="overflow-x-auto whitespace-pre-wrap">
                {canaryState
                  ? JSON.stringify(canaryState, null, 2)
                  : 'Use ops_canary_status para carregar.'}
              </pre>
            </div>
            <div className="mt-3 rounded-[1rem] border border-white/10 bg-white/[0.03] p-3 text-xs text-white/70">
              <p className="mb-1 font-semibold tracking-[0.2em] text-white/55 uppercase">
                Auto-remediacao
              </p>
              <pre className="overflow-x-auto whitespace-pre-wrap">
                {autoRemediation
                  ? JSON.stringify(autoRemediation, null, 2)
                  : 'Use ops_auto_remediate para simular ou aplicar correcao automatica.'}
              </pre>
            </div>
            <div className="mt-3 rounded-[1rem] border border-white/10 bg-white/[0.03] p-3 text-xs text-white/70">
              <p className="mb-1 font-semibold tracking-[0.2em] text-white/55 uppercase">
                Promocao canario
              </p>
              <pre className="overflow-x-auto whitespace-pre-wrap">
                {canaryPromotion
                  ? JSON.stringify(canaryPromotion, null, 2)
                  : 'Use ops_canary_promote para avaliar e promover rollout.'}
              </pre>
            </div>
            <div className="mt-3 rounded-[1rem] border border-white/10 bg-white/[0.03] p-3 text-xs text-white/70">
              <p className="mb-1 font-semibold tracking-[0.2em] text-white/55 uppercase">
                Control Loop Tick
              </p>
              <pre className="overflow-x-auto whitespace-pre-wrap">
                {controlTick
                  ? JSON.stringify(controlTick, null, 2)
                  : 'Use ops_control_loop_tick para rodar ciclo completo de operacao.'}
              </pre>
            </div>
          </article>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <article className="rounded-[2rem] border border-white/10 bg-black/25 p-5 backdrop-blur-xl">
            <div className="mb-3 flex items-center gap-2 text-cyan-200">
              <ShieldCheck className="size-4" />
              <span className="text-xs font-semibold tracking-[0.2em] uppercase">
                Snapshot de incidente
              </span>
            </div>
            {incidentSnapshot ? (
              <div className="space-y-3 text-sm">
                <p className="text-white/70">
                  gerado_em={String(incidentSnapshot.generated_at ?? '-')} | autonomia=
                  {String(incidentSnapshot.autonomy_mode ?? '-')}
                </p>
                <p className="text-white/70">
                  canario_ativo=
                  {String(
                    Boolean(
                      (incidentSnapshot.canary_state as Record<string, unknown> | undefined)
                        ?.active ?? false
                    )
                  )}{' '}
                  | coorte=
                  {String(
                    ((incidentSnapshot.canary_state as Record<string, unknown> | undefined)
                      ?.cohort as string | undefined) ?? '-'
                  )}
                </p>
                <p className="text-white/70">
                  rollout=
                  {String(
                    Number(
                      (incidentSnapshot.canary_state as Record<string, unknown> | undefined)
                        ?.rollout_percent ?? 0
                    )
                  )}
                  % | bucket=
                  {String(
                    Number(
                      (incidentSnapshot.canary_state as Record<string, unknown> | undefined)
                        ?.assignment_bucket ?? -1
                    )
                  )}
                </p>
                <p className="text-white/70">
                  trust_drift_ativo=
                  {String(
                    Number(
                      ((incidentSnapshot.trust_drift as Record<string, unknown> | undefined)
                        ?.active_total as number | undefined) ?? 0
                    )
                  )}
                </p>
                <p className="text-white/70">
                  autonomy_notice_ativo=
                  {String(
                    Number(
                      ((incidentSnapshot.autonomy_notice as Record<string, unknown> | undefined)
                        ?.active_total as number | undefined) ?? 0
                    )
                  )}{' '}
                  | domain_autonomy_modes=
                  {String(domainAutonomyModes.length)}
                </p>
                <div className="rounded-[1rem] border border-white/10 bg-white/[0.03] p-3">
                  <p className="mb-1 text-xs font-semibold tracking-[0.2em] text-white/55 uppercase">
                    Cohort metrics
                  </p>
                  <pre className="overflow-x-auto text-xs whitespace-pre-wrap">
                    {JSON.stringify(incidentSnapshot.canary_metrics ?? {}, null, 2)}
                  </pre>
                </div>
                <div className="rounded-[1rem] border border-white/10 bg-white/[0.03] p-3">
                  <p className="mb-1 text-xs font-semibold tracking-[0.2em] text-white/55 uppercase">
                    Trust drift
                  </p>
                  <pre className="overflow-x-auto text-xs whitespace-pre-wrap">
                    {JSON.stringify(incidentSnapshot.trust_drift ?? {}, null, 2)}
                  </pre>
                </div>
                <div className="rounded-[1rem] border border-white/10 bg-white/[0.03] p-3">
                  <p className="mb-1 text-xs font-semibold tracking-[0.2em] text-white/55 uppercase">
                    Autonomy notice
                  </p>
                  <pre className="overflow-x-auto text-xs whitespace-pre-wrap">
                    {JSON.stringify(incidentSnapshot.autonomy_notice ?? {}, null, 2)}
                  </pre>
                </div>
                <div className="rounded-[1rem] border border-white/10 bg-white/[0.03] p-3">
                  <p className="mb-2 text-xs font-semibold tracking-[0.2em] text-white/55 uppercase">
                    Domain autonomy modes
                  </p>
                  {domainAutonomyStatuses.length > 0 ? (
                    <div className="space-y-2">
                      {domainAutonomyStatuses.map((row) => (
                        <div
                          key={`${row.domain}-${row.effectiveAutonomyMode}`}
                          className="rounded-[1rem] border border-white/10 bg-black/20 px-3 py-2"
                        >
                          <p className="font-semibold">{row.domain}</p>
                          <p className="text-white/70">
                            floor={row.domainAutonomyMode ?? 'inherit'} | effective=
                            {row.effectiveAutonomyMode}
                          </p>
                          <p className="text-white/55">
                            reason={row.containmentReason ?? '-'} | source=
                            {row.containmentSource ?? '-'} | updated=
                            {row.domainAutonomyUpdatedAt
                              ? formatUpdatedAge(Date.parse(row.domainAutonomyUpdatedAt))
                              : '-'}
                          </p>
                          {row.trustDriftActive || row.autonomyNoticeUnconfirmed > 0 ? (
                            <p className="text-white/45">
                              drift={row.trustDriftActive ? 'sim' : 'nao'} | notice_unconfirmed=
                              {String(row.autonomyNoticeUnconfirmed)}
                            </p>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  ) : domainAutonomyModes.length > 0 ? (
                    <div className="space-y-2">
                      {domainAutonomyModes.map((row) => (
                        <div
                          key={`${row.domain}-${row.mode}`}
                          className="rounded-[1rem] border border-white/10 bg-black/20 px-3 py-2"
                        >
                          <p className="font-semibold">{row.domain}</p>
                          <p className="text-white/70">mode={row.mode}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-white/60">Nenhum floor por dominio ativo.</p>
                  )}
                </div>
                <div className="rounded-[1rem] border border-white/10 bg-white/[0.03] p-3">
                  <p className="mb-1 text-xs font-semibold tracking-[0.2em] text-white/55 uppercase">
                    Alertas
                  </p>
                  {Array.isArray(incidentSnapshot.alerts) && incidentSnapshot.alerts.length > 0 ? (
                    <div className="space-y-1">
                      {incidentSnapshot.alerts.slice(0, 6).map((alert, index) => (
                        <p key={`${String(alert)}-${index}`} className="text-rose-300">
                          {String(alert)}
                        </p>
                      ))}
                    </div>
                  ) : (
                    <p className="text-emerald-300">Sem alertas no ultimo snapshot.</p>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-sm text-white/60">
                Use `ops_incident_snapshot` para consolidar health, flags, kill switch e SLO.
              </p>
            )}
          </article>

          <article className="rounded-[2rem] border border-white/10 bg-black/25 p-5 backdrop-blur-xl">
            <div className="mb-3 flex items-center gap-2 text-amber-300">
              <ShieldCheck className="size-4" />
              <span className="text-xs font-semibold tracking-[0.2em] uppercase">
                Playbook aplicado
              </span>
            </div>
            {playbookReport ? (
              <div className="space-y-3 text-sm">
                <p className="text-white/70">
                  playbook={String(playbookReport.playbook ?? '-')} | dry_run=
                  {String(Boolean(playbookReport.dry_run))} | ajustes=
                  {String(
                    Array.isArray(playbookReport.changes) ? playbookReport.changes.length : 0
                  )}{' '}
                  | passos=
                  {String(
                    Array.isArray(playbookReport.step_reports)
                      ? playbookReport.step_reports.length
                      : 0
                  )}
                </p>
                <div className="rounded-[1rem] border border-white/10 bg-white/[0.03] p-3">
                  <p className="mb-1 text-xs font-semibold tracking-[0.2em] text-white/55 uppercase">
                    Mudancas
                  </p>
                  {Array.isArray(playbookReport.changes) && playbookReport.changes.length > 0 ? (
                    <div className="space-y-1">
                      {playbookReport.changes.slice(0, 8).map((change, index) => {
                        const row = change as Record<string, unknown>;
                        return (
                          <p
                            key={`${index}-${String(row.target ?? 'target')}`}
                            className="text-white/75"
                          >
                            {String(row.type ?? 'change')}: {String(row.target ?? '-')} (
                            {String(row.from ?? '-')}
                            {' -> '}
                            {String(row.to ?? '-')})
                          </p>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-white/60">Nenhuma mudanca direta registrada.</p>
                  )}
                </div>
                {Array.isArray(playbookReport.step_reports) &&
                playbookReport.step_reports.length > 0 ? (
                  <div className="rounded-[1rem] border border-white/10 bg-white/[0.03] p-3">
                    <p className="mb-1 text-xs font-semibold tracking-[0.2em] text-white/55 uppercase">
                      Passos
                    </p>
                    <div className="space-y-1">
                      {playbookReport.step_reports.slice(0, 8).map((step, index) => {
                        const row = step as Record<string, unknown>;
                        return (
                          <p
                            key={`${index}-${String(row.playbook ?? 'step')}`}
                            className="text-white/75"
                          >
                            {String(row.playbook ?? 'step')} | dry_run=
                            {String(Boolean(row.dry_run))}
                          </p>
                        );
                      })}
                    </div>
                  </div>
                ) : null}
                <p className="text-xs text-white/60">
                  Use `ops_canary_rollout_set`, `ops_apply_playbook`, `ops_rollback_scenario` e
                  `ops_auto_remediate` com `dry_run=true` antes de aplicar.
                </p>
              </div>
            ) : (
              <p className="text-sm text-white/60">
                Use `ops_apply_playbook` ou `ops_rollback_scenario` para resposta operacional
                rapida.
              </p>
            )}
          </article>
        </section>

        <section className="rounded-[2rem] border border-white/10 bg-black/25 p-5 backdrop-blur-xl">
          <div className="mb-3 flex items-center gap-2 text-cyan-200">
            <ShieldCheck className="size-4" />
            <span className="text-xs font-semibold tracking-[0.2em] uppercase">
              Comandos operacionais
            </span>
          </div>
          <p className="mb-3 text-sm text-white/65">
            Envia comandos para a sessao ativa do Jarvez (aba principal) via fila local.
          </p>
          <div className="grid gap-2 md:grid-cols-3">
            {OPS_SAFE_PRESETS.map((preset) => (
              <Button
                key={preset.id}
                type="button"
                variant="secondary"
                onClick={() => queueOpsCommand(preset)}
              >
                {preset.label}
              </Button>
            ))}
          </div>
          <div className="mt-3">
            <p className="mb-2 text-xs font-semibold tracking-[0.2em] text-rose-200 uppercase">
              Comandos criticos
            </p>
            <div className="grid gap-2 md:grid-cols-2">
              {OPS_GUARDED_PRESETS.map((preset) => (
                <Button
                  key={preset.id}
                  type="button"
                  variant="secondary"
                  className="border border-rose-300/30 bg-rose-500/10 text-rose-100 hover:bg-rose-500/20"
                  onClick={() => {
                    setArmedGuardedPreset(preset);
                    setGuardPhrase('');
                  }}
                >
                  {preset.label}
                </Button>
              ))}
            </div>
          </div>
          <div className="mt-4">
            <p className="mb-2 text-xs font-semibold tracking-[0.2em] text-amber-200 uppercase">
              Autonomia por dominio
            </p>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {domainAutonomyCandidates.map((domain) => {
                const currentMode =
                  domainAutonomyModes.find((row) => row.domain === domain)?.mode ?? 'inherit';
                const currentStatus = domainAutonomyStatuses.find((row) => row.domain === domain);
                const backendTrustRow = backendDomainTrustScores.find(
                  (row) => row.domain === domain
                );
                const effectiveMode =
                  currentStatus?.effectiveAutonomyMode ??
                  backendTrustRow?.effectiveAutonomyMode ??
                  backendTrustRow?.autonomyMode ??
                  'aggressive';
                const containmentReason =
                  currentStatus?.containmentReason ?? backendTrustRow?.domainAutonomyReason ?? '-';
                const containmentSource =
                  currentStatus?.containmentSource ?? backendTrustRow?.domainAutonomySource ?? '-';
                const updatedAt = currentStatus?.domainAutonomyUpdatedAt
                  ? Date.parse(currentStatus.domainAutonomyUpdatedAt)
                  : (backendTrustRow?.domainAutonomyUpdatedAt ?? null);
                return (
                  <div
                    key={`domain-autonomy-${domain}`}
                    className="rounded-[1rem] border border-white/10 bg-white/[0.03] p-3 text-sm"
                  >
                    <p className="font-semibold">{domain}</p>
                    <p className="mt-1 text-white/65">
                      floor={currentMode} | effective={effectiveMode}
                    </p>
                    <p className="mt-1 text-white/50">
                      reason={containmentReason} | source={containmentSource}
                    </p>
                    <p className="mt-1 text-white/40">
                      updated={updatedAt ? formatUpdatedAge(updatedAt) : '-'}
                    </p>
                    <div className="mt-3 flex gap-2">
                      <Button
                        type="button"
                        variant="secondary"
                        className="flex-1 border border-rose-300/25 bg-rose-500/10 text-rose-100 hover:bg-rose-500/20"
                        onClick={() => {
                          setArmedGuardedPreset(buildDomainAutonomyPreset(domain, 'degrade'));
                          setGuardPhrase('');
                        }}
                      >
                        Degradar
                      </Button>
                      <Button
                        type="button"
                        variant="secondary"
                        className="flex-1 border border-emerald-300/25 bg-emerald-500/10 text-emerald-100 hover:bg-emerald-500/20"
                        onClick={() => {
                          setArmedGuardedPreset(buildDomainAutonomyPreset(domain, 'restore'));
                          setGuardPhrase('');
                        }}
                      >
                        Restaurar
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {armedGuardedPreset ? (
            <div className="mt-4 rounded-[1rem] border border-rose-300/35 bg-rose-500/10 p-3 text-xs text-rose-100">
              <p className="font-semibold">Confirmacao manual obrigatoria</p>
              <p className="mt-1">
                Para enfileirar <span className="font-semibold">{armedGuardedPreset.label}</span>,
                digite <span className="font-semibold">{GUARD_CONFIRM_TEXT}</span>.
              </p>
              <div className="mt-2 flex flex-col gap-2 sm:flex-row">
                <input
                  type="text"
                  value={guardPhrase}
                  onChange={(event) => setGuardPhrase(event.target.value)}
                  placeholder={GUARD_CONFIRM_TEXT}
                  className="h-9 flex-1 rounded-lg border border-white/20 bg-black/40 px-3 text-sm text-white ring-0 outline-none placeholder:text-white/45 focus:border-rose-300/45"
                />
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant="secondary"
                    className="border border-rose-300/30 bg-rose-500/20 text-rose-100 hover:bg-rose-500/30"
                    onClick={queueGuardedPreset}
                    disabled={guardPhrase.trim().toUpperCase() !== GUARD_CONFIRM_TEXT}
                  >
                    Confirmar
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => {
                      setArmedGuardedPreset(null);
                      setGuardPhrase('');
                    }}
                  >
                    Cancelar
                  </Button>
                </div>
              </div>
            </div>
          ) : null}

          <div className="mt-4 rounded-[1rem] border border-white/10 bg-white/[0.03] p-3">
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
              <p className="text-xs font-semibold tracking-[0.2em] text-white/55 uppercase">
                Fila de comandos
              </p>
              <div className="flex flex-wrap items-center gap-2">
                {(['all', 'pending', 'dispatching', 'sent', 'failed'] as CommandFilter[]).map(
                  (value) => (
                    <Button
                      key={value}
                      type="button"
                      variant="secondary"
                      className={
                        commandFilter === value
                          ? 'h-7 border border-cyan-300/30 bg-cyan-500/15 px-2 text-xs text-cyan-100'
                          : 'h-7 px-2 text-xs'
                      }
                      onClick={() => setCommandFilter(value)}
                    >
                      {value}
                    </Button>
                  )
                )}
                <Button
                  type="button"
                  variant="secondary"
                  className="h-7 px-2 text-xs"
                  onClick={clearTerminalCommands}
                >
                  Limpar finalizados
                </Button>
              </div>
            </div>
            {filteredCommands.length > 0 ? (
              <div className="space-y-2">
                {filteredCommands
                  .slice()
                  .reverse()
                  .slice(0, 10)
                  .map((command) => (
                    <div
                      key={command.id}
                      className="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-xs text-white/75"
                    >
                      {(() => {
                        const timing = getCommandTimingHint(command);
                        return timing ? (
                          <p className={timing.overdue ? 'text-rose-300' : 'text-amber-200'}>
                            evidencia em {formatDurationShort(timing.timeoutMs)} | restante=
                            {formatDurationShort(timing.remainingMs)}
                          </p>
                        ) : null;
                      })()}
                      <p className="font-semibold text-white">{command.label}</p>
                      <p>
                        status={command.status} | criado={formatDate(command.createdAt)} |
                        atualizado=
                        {formatDate(command.updatedAt)}
                      </p>
                      {command.expectedActionName ? (
                        <p className="text-white/65">action={command.expectedActionName}</p>
                      ) : null}
                      <p className="text-white/60">domain={command.domain ?? '-'}</p>
                      <p className="text-white/60">
                        risk={command.riskTier ?? '-'} | auto_retry=
                        {String(Boolean(command.autoRetryOnNoEvidence))} | tentativas=
                        {String((command.retryCount ?? 0) + 1)}
                        {typeof command.maxAutoRetries === 'number'
                          ? ` (max=${command.maxAutoRetries + 1})`
                          : ''}
                      </p>
                      {command.driftGuardrailApplied ? (
                        <p className="text-amber-200">
                          drift_guardrail=ativo |{' '}
                          {command.driftGuardrailReason ?? 'modo conservador'}
                        </p>
                      ) : null}
                      {command.executionTrace ? (
                        <p
                          className={
                            command.executionTrace.success ? 'text-emerald-300' : 'text-rose-300'
                          }
                        >
                          execucao={command.executionTrace.success ? 'sucesso' : 'falha'} | trace=
                          {command.executionTrace.traceId} | policy=
                          {command.executionTrace.policyDecision ?? '-'} | risk=
                          {command.executionTrace.risk ?? '-'}
                        </p>
                      ) : command.status === 'sent' ? (
                        <p className="text-white/60">Aguardando resultado real da action...</p>
                      ) : null}
                      <div className="mt-2 flex gap-2">
                        {command.status === 'failed' ? (
                          <Button
                            type="button"
                            variant="secondary"
                            className="h-7 px-2 text-xs"
                            onClick={() => retryCommand(command.id)}
                          >
                            Reenfileirar
                          </Button>
                        ) : null}
                        {command.status === 'sent' || command.status === 'failed' ? (
                          <Button
                            type="button"
                            variant="secondary"
                            className="h-7 px-2 text-xs"
                            onClick={() => removeCommand(command.id)}
                          >
                            Remover
                          </Button>
                        ) : null}
                      </div>
                      {command.error ? <p className="text-rose-300">erro={command.error}</p> : null}
                    </div>
                  ))}
              </div>
            ) : (
              <p className="text-xs text-white/55">Sem comandos para o filtro selecionado.</p>
            )}
          </div>
        </section>

        <section className="rounded-[2rem] border border-white/10 bg-black/25 p-5 backdrop-blur-xl">
          <div className="mb-3 flex items-center gap-2 text-cyan-200">
            <ShieldCheck className="size-4" />
            <span className="text-xs font-semibold tracking-[0.2em] uppercase">
              Trust score por dominio
            </span>
          </div>
          {effectiveDomainTrustScores.length > 0 ? (
            <div className="space-y-4">
              <div className="rounded-[1rem] border border-white/10 bg-white/[0.03] p-3 text-xs text-white/60">
                fonte principal={backendDomainTrustScores.length > 0 ? 'backend' : 'local_queue'}
                {backendDomainTrustScores.length > 0 && domainTrustScores.length > 0
                  ? ' | fallback local ativo'
                  : ''}
                {' | calibracao da fila=trust efetivo'}
              </div>
              {backendDomainTrustScores.length > 0 && domainTrustScores.length > 0 ? (
                <div className="grid gap-3 md:grid-cols-3">
                  <div className="rounded-[1rem] border border-amber-300/20 bg-amber-500/10 p-3 text-sm text-amber-100">
                    <p className="font-semibold">Drift ativo</p>
                    <p className="text-xs text-amber-100/80">
                      {String(driftComparisons.length)} dominios com desvio relevante.
                    </p>
                  </div>
                  <div className="rounded-[1rem] border border-cyan-300/20 bg-cyan-500/10 p-3 text-sm text-cyan-100">
                    <p className="font-semibold">Somente backend</p>
                    <p className="text-xs text-cyan-100/80">
                      {String(backendOnlyComparisons.length)} dominios sem heuristica local.
                    </p>
                  </div>
                  <div className="rounded-[1rem] border border-white/10 bg-white/[0.03] p-3 text-sm text-white/80">
                    <p className="font-semibold">Somente local</p>
                    <p className="text-xs text-white/60">
                      {String(localOnlyComparisons.length)} dominios ainda sem snapshot backend.
                    </p>
                  </div>
                </div>
              ) : null}
              <div className="grid gap-3 md:grid-cols-2">
                {effectiveDomainTrustScores.map((score) => (
                  <div
                    key={`${score.source ?? 'local'}-${score.domain}`}
                    className="rounded-[1rem] border border-white/10 bg-white/[0.03] p-3 text-sm"
                  >
                    <p className="font-semibold text-white">{score.domain}</p>
                    <p className="text-white/70">
                      score={score.score.toFixed(2)} | samples={String(score.samples)} | source=
                      {score.source ?? 'local'}
                    </p>
                    <p className="text-white/60">
                      success={String(score.successCount)} | failure={String(score.failureCount)} |
                      no_evidence={String(score.noEvidenceCount)}
                    </p>
                    <p className="text-white/60">
                      recomendado: timeout={formatDurationShort(score.recommendation.timeoutMs)} |
                      retries={String(score.recommendation.maxAutoRetries)}
                    </p>
                    <p className="text-white/45">
                      atualizado ha {formatUpdatedAge(score.updatedAt)}
                    </p>
                  </div>
                ))}
              </div>
              {backendDomainTrustScores.length > 0 && domainTrustScores.length > 0 ? (
                <div className="space-y-3">
                  <div className="rounded-[1rem] border border-white/10 bg-black/20 p-3 text-xs text-white/60">
                    local queue heuristic: {String(domainTrustScores.length)} dominios calibrados.
                  </div>
                  {trustComparisons.length > 0 ? (
                    <div className="rounded-[1rem] border border-white/10 bg-black/20 p-3">
                      <p className="mb-2 text-xs font-semibold tracking-[0.2em] text-white/55 uppercase">
                        Drift monitor backend x local
                      </p>
                      <div className="space-y-2">
                        {trustComparisons.map((comparison) => (
                          <div
                            key={comparison.domain}
                            className={
                              comparison.state === 'drift'
                                ? 'rounded-xl border border-amber-300/25 bg-amber-500/10 px-3 py-2 text-xs text-amber-100'
                                : comparison.state === 'backend_only'
                                  ? 'rounded-xl border border-cyan-300/25 bg-cyan-500/10 px-3 py-2 text-xs text-cyan-100'
                                  : comparison.state === 'local_only'
                                    ? 'rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-white/70'
                                    : 'rounded-xl border border-emerald-300/20 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-100'
                            }
                          >
                            <p className="font-semibold">
                              {comparison.domain} | estado={comparison.state}
                            </p>
                            <p>
                              backend={comparison.backend?.score.toFixed(2) ?? '-'} | local=
                              {comparison.local?.score.toFixed(2) ?? '-'} | delta=
                              {comparison.scoreDelta.toFixed(2)}
                            </p>
                            <p>
                              timeout backend=
                              {comparison.backend
                                ? formatDurationShort(comparison.backend.recommendation.timeoutMs)
                                : '-'}{' '}
                              | timeout local=
                              {comparison.local
                                ? formatDurationShort(comparison.local.recommendation.timeoutMs)
                                : '-'}{' '}
                              | retry backend=
                              {comparison.backend?.recommendation.maxAutoRetries ?? '-'} | retry
                              local={comparison.local?.recommendation.maxAutoRetries ?? '-'}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </div>
          ) : (
            <p className="text-sm text-white/60">
              Sem score ainda. Consulte o backend ou execute comandos reais para calibrar os
              dominios.
            </p>
          )}
        </section>

        <div className="flex justify-end">
          <Button type="button" variant="secondary" onClick={() => window.location.reload()}>
            Atualizar
          </Button>
        </div>
      </div>
    </main>
  );
}
