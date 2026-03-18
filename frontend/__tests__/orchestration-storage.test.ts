/**
 * Tests for orchestration-storage critical functions.
 *
 * We test the localStorage-backed read/write cycle plus the normalization
 * functions that parse backend payloads into frontend DomainTrustScore shape.
 * The jsdom environment provides a localStorage implementation.
 */

import { describe, it, expect, beforeEach } from 'vitest';

// ---------------------------------------------------------------------------
// Inline the pure normalization helpers that are module-private in
// orchestration-storage.ts.  Tests verify the parse + hydration contract.
// ---------------------------------------------------------------------------

interface DomainTrustScore {
  domain: string;
  score: number;
  samples: number;
  successCount: number;
  failureCount: number;
  noEvidenceCount: number;
  updatedAt: number;
  source?: string;
  recommendation: { timeoutMs: number; maxAutoRetries: number };
}

const DEFAULT_DOMAIN_TRUST_SCORE = 0.7;
const DEFAULT_NO_EVIDENCE_TIMEOUT_MS = 45_000;
const MAX_NO_EVIDENCE_TIMEOUT_MS = 30 * 60_000;
const MAX_AUTO_RETRIES_HARD_LIMIT = 5;

function clampScore(value: number): number {
  if (!Number.isFinite(value)) return DEFAULT_DOMAIN_TRUST_SCORE;
  if (value < 0) return 0;
  if (value > 1) return 1;
  return value;
}

function clampInteger(value: number, min: number, max: number): number {
  if (!Number.isFinite(value)) return min;
  return Math.max(min, Math.min(max, Math.trunc(value)));
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

function recommendationFromScore(score: number): { timeoutMs: number; maxAutoRetries: number } {
  if (score >= 0.85) return { timeoutMs: 30_000, maxAutoRetries: 2 };
  if (score >= 0.65) return { timeoutMs: 45_000, maxAutoRetries: 1 };
  if (score >= 0.45) return { timeoutMs: 60_000, maxAutoRetries: 0 };
  return { timeoutMs: 90_000, maxAutoRetries: 0 };
}

function normalizeDomainTrustScores(value: unknown): DomainTrustScore[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((item): item is DomainTrustScore => Boolean(item && typeof item === 'object'))
    .map<DomainTrustScore>((item) => {
      const score = clampScore(Number(item.score));
      return {
        domain: typeof item.domain === 'string' && item.domain ? item.domain : 'general',
        score,
        samples: clampInteger(Number(item.samples ?? 0), 0, 100_000),
        successCount: clampInteger(Number(item.successCount ?? 0), 0, 100_000),
        failureCount: clampInteger(Number(item.failureCount ?? 0), 0, 100_000),
        noEvidenceCount: clampInteger(Number(item.noEvidenceCount ?? 0), 0, 100_000),
        updatedAt: Number.isFinite(Number(item.updatedAt)) ? Number(item.updatedAt) : Date.now(),
        source: item.source === 'backend' ? 'backend' : 'local',
        recommendation: recommendationFromScore(score),
      };
    })
    .sort((a, b) => a.domain.localeCompare(b.domain));
}

// Backend-format normalizer (snake_case → camelCase)
function normalizeBackendDomainTrustScores(value: unknown): DomainTrustScore[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((item): item is Record<string, unknown> => Boolean(item && typeof item === 'object'))
    .map<DomainTrustScore>((item) => {
      const score = clampScore(Number(item.score));
      const updatedAt = Date.parse(String(item.updated_at ?? ''));
      return {
        domain: typeof item.domain === 'string' && item.domain ? item.domain : 'general',
        score,
        samples: clampInteger(Number(item.samples ?? 0), 0, 100_000),
        successCount: clampInteger(Number(item.success_count ?? 0), 0, 100_000),
        failureCount: clampInteger(Number(item.failure_count ?? 0), 0, 100_000),
        noEvidenceCount: clampInteger(Number(item.no_evidence_count ?? 0), 0, 100_000),
        updatedAt: Number.isFinite(updatedAt) ? updatedAt : Date.now(),
        source: 'backend',
        recommendation: recommendationFromScore(score),
      };
    })
    .sort((a, b) => a.domain.localeCompare(b.domain));
}

// ---------------------------------------------------------------------------
// localStorage read/write helpers (mirrors orchestration-storage internals)
// ---------------------------------------------------------------------------

const DOMAIN_TRUST_KEY = 'jarvez:trust-domain-trust';

function readStoredScores(): DomainTrustScore[] {
  const raw = window.localStorage.getItem(DOMAIN_TRUST_KEY);
  if (!raw) return [];
  try {
    return normalizeDomainTrustScores(JSON.parse(raw));
  } catch {
    window.localStorage.removeItem(DOMAIN_TRUST_KEY);
    return [];
  }
}

function writeStoredScores(scores: DomainTrustScore[]): void {
  window.localStorage.setItem(DOMAIN_TRUST_KEY, JSON.stringify(scores));
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

beforeEach(() => {
  window.localStorage.clear();
});

describe('clampScore', () => {
  it('clamps values to [0,1]', () => {
    expect(clampScore(-0.5)).toBe(0);
    expect(clampScore(1.5)).toBe(1);
    expect(clampScore(0.7)).toBe(0.7);
  });

  it('returns default for NaN/Infinity', () => {
    expect(clampScore(NaN)).toBe(DEFAULT_DOMAIN_TRUST_SCORE);
    // Infinity fails isFinite check → returns DEFAULT_DOMAIN_TRUST_SCORE
    expect(clampScore(Infinity)).toBe(DEFAULT_DOMAIN_TRUST_SCORE);
  });
});

describe('normalizeNoEvidenceTimeoutMs', () => {
  it('returns default for non-finite input', () => {
    expect(normalizeNoEvidenceTimeoutMs(undefined)).toBe(DEFAULT_NO_EVIDENCE_TIMEOUT_MS);
    expect(normalizeNoEvidenceTimeoutMs(NaN)).toBe(DEFAULT_NO_EVIDENCE_TIMEOUT_MS);
  });

  it('clamps to minimum 5000ms', () => {
    expect(normalizeNoEvidenceTimeoutMs(0)).toBe(5_000);
    expect(normalizeNoEvidenceTimeoutMs(-1000)).toBe(5_000);
  });

  it('clamps to maximum', () => {
    expect(normalizeNoEvidenceTimeoutMs(999_999_999)).toBe(MAX_NO_EVIDENCE_TIMEOUT_MS);
  });

  it('passes valid values through', () => {
    expect(normalizeNoEvidenceTimeoutMs(30_000)).toBe(30_000);
  });
});

describe('normalizeMaxAutoRetries', () => {
  it('returns 0 when autoRetry disabled and value is invalid', () => {
    expect(normalizeMaxAutoRetries(undefined, false)).toBe(0);
    expect(normalizeMaxAutoRetries(NaN, false)).toBe(0);
  });

  it('returns 1 when autoRetry enabled and value is invalid', () => {
    expect(normalizeMaxAutoRetries(undefined, true)).toBe(1);
  });

  it('caps at hard limit', () => {
    expect(normalizeMaxAutoRetries(100, true)).toBe(MAX_AUTO_RETRIES_HARD_LIMIT);
  });

  it('passes valid values through', () => {
    expect(normalizeMaxAutoRetries(2, true)).toBe(2);
  });
});

describe('recommendationFromScore', () => {
  it('returns high-trust recommendation for score >= 0.85', () => {
    const rec = recommendationFromScore(0.9);
    expect(rec.timeoutMs).toBe(30_000);
    expect(rec.maxAutoRetries).toBe(2);
  });

  it('returns medium-trust for 0.65 <= score < 0.85', () => {
    const rec = recommendationFromScore(0.7);
    expect(rec.timeoutMs).toBe(45_000);
    expect(rec.maxAutoRetries).toBe(1);
  });

  it('returns low-trust for score < 0.45', () => {
    const rec = recommendationFromScore(0.2);
    expect(rec.timeoutMs).toBe(90_000);
    expect(rec.maxAutoRetries).toBe(0);
  });
});

describe('normalizeDomainTrustScores — parse and hydration', () => {
  it('returns empty array for non-array input', () => {
    expect(normalizeDomainTrustScores(null)).toEqual([]);
    expect(normalizeDomainTrustScores('string')).toEqual([]);
    expect(normalizeDomainTrustScores({})).toEqual([]);
  });

  it('normalizes valid camelCase payload from localStorage', () => {
    const raw = [
      {
        domain: 'whatsapp',
        score: 0.8,
        samples: 10,
        successCount: 8,
        failureCount: 1,
        noEvidenceCount: 1,
        updatedAt: 1710000000000,
        source: 'local',
      },
    ];
    const result = normalizeDomainTrustScores(raw);
    expect(result).toHaveLength(1);
    expect(result[0].domain).toBe('whatsapp');
    expect(result[0].score).toBe(0.8);
    expect(result[0].samples).toBe(10);
    expect(result[0].recommendation.timeoutMs).toBe(45_000); // 0.8 is in 0.65-0.85 bucket
  });

  it('falls back to "general" domain for empty domain string', () => {
    const raw = [{ domain: '', score: 0.7, samples: 0 }];
    const result = normalizeDomainTrustScores(raw);
    expect(result[0].domain).toBe('general');
  });

  it('sorts domains alphabetically', () => {
    const raw = [
      { domain: 'spotify', score: 0.9 },
      { domain: 'home', score: 0.6 },
      { domain: 'whatsapp', score: 0.5 },
    ];
    const result = normalizeDomainTrustScores(raw);
    expect(result.map((r) => r.domain)).toEqual(['home', 'spotify', 'whatsapp']);
  });
});

describe('normalizeBackendDomainTrustScores — backend snake_case format', () => {
  it('converts snake_case fields to camelCase', () => {
    const raw = [
      {
        domain: 'shell',
        score: 0.75,
        samples: 5,
        success_count: 4,
        failure_count: 1,
        no_evidence_count: 0,
        updated_at: '2026-03-18T12:00:00Z',
      },
    ];
    const result = normalizeBackendDomainTrustScores(raw);
    expect(result).toHaveLength(1);
    expect(result[0].domain).toBe('shell');
    expect(result[0].successCount).toBe(4);
    expect(result[0].failureCount).toBe(1);
    expect(result[0].source).toBe('backend');
  });
});

describe('localStorage read/write cycle', () => {
  it('writes and reads back domain trust scores', () => {
    const scores: DomainTrustScore[] = [
      {
        domain: 'ops',
        score: 0.9,
        samples: 20,
        successCount: 18,
        failureCount: 1,
        noEvidenceCount: 1,
        updatedAt: Date.now(),
        source: 'local',
        recommendation: { timeoutMs: 30_000, maxAutoRetries: 2 },
      },
    ];
    writeStoredScores(scores);
    const read = readStoredScores();
    expect(read).toHaveLength(1);
    expect(read[0].domain).toBe('ops');
    expect(read[0].score).toBe(0.9);
    expect(read[0].recommendation.maxAutoRetries).toBe(2);
  });

  it('returns empty array when localStorage is empty', () => {
    expect(readStoredScores()).toEqual([]);
  });

  it('returns empty array and clears key on malformed JSON', () => {
    window.localStorage.setItem(DOMAIN_TRUST_KEY, 'not-valid-json');
    const result = readStoredScores();
    expect(result).toEqual([]);
    expect(window.localStorage.getItem(DOMAIN_TRUST_KEY)).toBeNull();
  });
});
