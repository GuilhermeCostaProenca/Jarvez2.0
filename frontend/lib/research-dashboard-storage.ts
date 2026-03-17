import type { ResearchDashboard, ResearchSchedule } from '@/lib/types/realtime';

export const WEB_RESEARCH_SCHEDULES_KEY = 'jarvez:web-research-schedules';
export const WEB_RESEARCH_DASHBOARD_KEY = 'jarvez:web-research-dashboard';

export function readStoredResearchSchedules(): ResearchSchedule[] {
  if (typeof window === 'undefined') {
    return [];
  }

  const raw = window.localStorage.getItem(WEB_RESEARCH_SCHEDULES_KEY);
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw) as ResearchSchedule[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    window.localStorage.removeItem(WEB_RESEARCH_SCHEDULES_KEY);
    return [];
  }
}

export function writeStoredResearchSchedules(value: ResearchSchedule[]) {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(WEB_RESEARCH_SCHEDULES_KEY, JSON.stringify(value));
}

export function readStoredResearchDashboard(): ResearchDashboard | null {
  if (typeof window === 'undefined') {
    return null;
  }

  const raw = window.localStorage.getItem(WEB_RESEARCH_DASHBOARD_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as ResearchDashboard;
  } catch {
    window.localStorage.removeItem(WEB_RESEARCH_DASHBOARD_KEY);
    return null;
  }
}

export function writeStoredResearchDashboard(value: ResearchDashboard) {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(WEB_RESEARCH_DASHBOARD_KEY, JSON.stringify(value));
}
