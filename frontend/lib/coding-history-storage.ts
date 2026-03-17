import type { CodingHistoryEntry, CodexTaskHistoryEntry } from '@/lib/types/realtime';

export const CODING_HISTORY_KEY = 'jarvez:coding-history';
export const CODEX_TASK_HISTORY_KEY = 'jarvez:codex-task-history';

export function readStoredCodingHistory(): CodingHistoryEntry[] {
  if (typeof window === 'undefined') {
    return [];
  }

  const raw = window.localStorage.getItem(CODING_HISTORY_KEY);
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw) as CodingHistoryEntry[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    window.localStorage.removeItem(CODING_HISTORY_KEY);
    return [];
  }
}

export function writeStoredCodingHistory(value: CodingHistoryEntry[]) {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(CODING_HISTORY_KEY, JSON.stringify(value));
}

export function readStoredCodexTaskHistory(): CodexTaskHistoryEntry[] {
  if (typeof window === 'undefined') {
    return [];
  }

  const raw = window.localStorage.getItem(CODEX_TASK_HISTORY_KEY);
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw) as CodexTaskHistoryEntry[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    window.localStorage.removeItem(CODEX_TASK_HISTORY_KEY);
    return [];
  }
}

export function writeStoredCodexTaskHistory(value: CodexTaskHistoryEntry[]) {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(CODEX_TASK_HISTORY_KEY, JSON.stringify(value));
}
