'use client';

import { useEffect, useState } from 'react';
import { Bot, Clock3, PlayCircle, RefreshCcw, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  readStoredAutomationState,
  readStoredBrowserTask,
  readStoredWorkflowState,
} from '@/lib/orchestration-storage';
import type { AutomationState, BrowserTaskState, WorkflowState } from '@/lib/types/realtime';

function formatDate(value?: string) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(date);
}

export function BrowserAgentView() {
  const [browserTask, setBrowserTask] = useState<BrowserTaskState | null>(null);
  const [workflowState, setWorkflowState] = useState<WorkflowState | null>(null);
  const [automationState, setAutomationState] = useState<AutomationState | null>(null);

  useEffect(() => {
    const sync = () => {
      setBrowserTask(readStoredBrowserTask());
      setWorkflowState(readStoredWorkflowState());
      setAutomationState(readStoredAutomationState());
    };
    sync();
    window.addEventListener('storage', sync);
    const timer = window.setInterval(sync, 3000);
    return () => {
      window.removeEventListener('storage', sync);
      window.clearInterval(timer);
    };
  }, []);

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(34,197,94,0.12),_transparent_32%),radial-gradient(circle_at_top_right,_rgba(56,189,248,0.1),_transparent_30%),linear-gradient(180deg,#030711_0%,#071323_100%)] px-4 py-8 text-white">
      <div className="mx-auto max-w-5xl space-y-6">
        <header className="rounded-[2rem] border border-white/10 bg-black/30 px-6 py-5 backdrop-blur-xl">
          <div className="mb-2 flex items-center gap-2 text-cyan-200">
            <Bot className="size-5" />
            <span className="text-xs font-semibold tracking-[0.24em] uppercase">Jarvez Browser Agent</span>
          </div>
          <h1 className="text-2xl font-semibold">Autonomia Operacional</h1>
          <p className="mt-1 text-sm text-white/60">
            Estado atual do browser agent, workflow "ideia para codigo" e automacoes proativas.
          </p>
        </header>

        <section className="rounded-[2rem] border border-white/10 bg-black/25 p-5 backdrop-blur-xl">
          <div className="mb-3 flex items-center gap-2 text-emerald-200">
            <PlayCircle className="size-4" />
            <span className="text-xs font-semibold tracking-[0.2em] uppercase">Browser Task</span>
          </div>
          {browserTask ? (
            <div className="grid gap-2 text-sm text-white/80 md:grid-cols-2">
              <p>Status: <strong>{browserTask.status ?? '-'}</strong></p>
              <p>Read-only: <strong>{browserTask.read_only ? 'sim' : 'nao'}</strong></p>
              <p>Inicio: <strong>{formatDate(browserTask.started_at)}</strong></p>
              <p>Fim: <strong>{formatDate(browserTask.finished_at)}</strong></p>
              <p className="md:col-span-2">Request: <strong>{browserTask.request ?? '-'}</strong></p>
              <p className="md:col-span-2">
                Allowed domains: <strong>{(browserTask.allowed_domains ?? []).join(', ') || '-'}</strong>
              </p>
              <p className="md:col-span-2">Resumo: <strong>{browserTask.summary ?? '-'}</strong></p>
            </div>
          ) : (
            <p className="text-sm text-white/60">Nenhuma tarefa de browser registrada.</p>
          )}
        </section>

        <section className="rounded-[2rem] border border-white/10 bg-black/25 p-5 backdrop-blur-xl">
          <div className="mb-3 flex items-center gap-2 text-amber-200">
            <Shield className="size-4" />
            <span className="text-xs font-semibold tracking-[0.2em] uppercase">Workflow</span>
          </div>
          {workflowState ? (
            <div className="grid gap-2 text-sm text-white/80 md:grid-cols-2">
              <p>Status: <strong>{workflowState.status ?? '-'}</strong></p>
              <p>Tipo: <strong>{workflowState.workflow_type ?? '-'}</strong></p>
              <p>Projeto: <strong>{workflowState.project_name ?? '-'}</strong></p>
              <p>Passo atual: <strong>{workflowState.current_step ?? '-'}</strong></p>
              <p className="md:col-span-2">Resumo: <strong>{workflowState.summary ?? '-'}</strong></p>
            </div>
          ) : (
            <p className="text-sm text-white/60">Nenhum workflow registrado.</p>
          )}
        </section>

        <section className="rounded-[2rem] border border-white/10 bg-black/25 p-5 backdrop-blur-xl">
          <div className="mb-3 flex items-center gap-2 text-violet-200">
            <Clock3 className="size-4" />
            <span className="text-xs font-semibold tracking-[0.2em] uppercase">Automacao</span>
          </div>
          {automationState ? (
            <div className="grid gap-2 text-sm text-white/80 md:grid-cols-2">
              <p>Status: <strong>{automationState.status ?? '-'}</strong></p>
              <p>Tipo: <strong>{automationState.automation_type ?? '-'}</strong></p>
              <p>Ultima execucao: <strong>{formatDate(automationState.last_run_at)}</strong></p>
              <p>Proxima execucao: <strong>{formatDate(automationState.next_run_at)}</strong></p>
              <p className="md:col-span-2">Resumo: <strong>{automationState.summary ?? '-'}</strong></p>
            </div>
          ) : (
            <p className="text-sm text-white/60">Nenhuma automacao registrada.</p>
          )}
        </section>

        <div className="flex justify-end">
          <Button type="button" variant="secondary" onClick={() => window.location.reload()}>
            <RefreshCcw className="size-4" />
            <span>Atualizar</span>
          </Button>
        </div>
      </div>
    </main>
  );
}
