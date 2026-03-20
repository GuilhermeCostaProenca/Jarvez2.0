'use client';

import React, { useMemo, useState } from 'react';
import {
  Activity,
  FolderCode,
  PanelRightClose,
  PanelRightOpen,
  Play,
  Route,
  ShieldCheck,
  Sparkles,
  TerminalSquare,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { getSecurityAccessChip } from '@/lib/auth-state-ui';
import { cn } from '@/lib/shadcn/utils';
import type { CodexTaskEvent, CodexTaskHistoryEntry, CodexTaskState, SecuritySessionState } from '@/lib/types/realtime';

interface CodingWorkspaceProps {
  securitySession: SecuritySessionState;
  activeCodexTask: CodexTaskState | null;
  codexTaskEvents: CodexTaskEvent[];
  codexTaskHistory: CodexTaskHistoryEntry[];
  contextLabel: string;
  silentMode: boolean;
  integrationsMenuOpen: boolean;
  onToggleSilentMode: () => void;
  onToggleIntegrations: () => void;
  onSendPrompt: (prompt: string) => unknown | Promise<unknown>;
}

function statusLabel(status?: string) {
  if (status === 'running') return 'Executando';
  if (status === 'completed') return 'Concluida';
  if (status === 'failed') return 'Falhou';
  if (status === 'cancelled') return 'Cancelada';
  return 'Aguardando';
}

function formatTaskTime(value?: string) {
  if (!value) return 'agora';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export function CodingWorkspace({
  securitySession,
  activeCodexTask,
  codexTaskEvents,
  codexTaskHistory,
  contextLabel,
  silentMode,
  integrationsMenuOpen,
  onToggleSilentMode,
  onToggleIntegrations,
  onSendPrompt,
}: CodingWorkspaceProps) {
  const [prompt, setPrompt] = useState('');
  const [isSendingPrompt, setIsSendingPrompt] = useState(false);
  const accessChip = getSecurityAccessChip(securitySession);

  const workspaceHeadline = useMemo(() => {
    if (activeCodexTask?.status === 'running') {
      return 'Codex trabalhando no projeto';
    }
    if (activeCodexTask?.status === 'failed') {
      return 'A tarefa precisa de revisao';
    }
    return 'O que vamos programar a seguir?';
  }, [activeCodexTask?.status]);

  const workspaceSubheadline = useMemo(() => {
    if (activeCodexTask?.summary) {
      return activeCodexTask.summary;
    }
    if (securitySession.activeProjectName) {
      return `Projeto ativo: ${securitySession.activeProjectName}`;
    }
    return 'Selecione um projeto e deixe o Jarvez acionar o Codex em modo seguro.';
  }, [activeCodexTask?.summary, securitySession.activeProjectName]);

  const handleSubmitPrompt = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextPrompt = prompt.trim();
    if (!nextPrompt || isSendingPrompt) {
      return;
    }

    setIsSendingPrompt(true);
    try {
      await onSendPrompt(nextPrompt);
      setPrompt('');
    } finally {
      setIsSendingPrompt(false);
    }
  };

  const handleQuickPrompt = async (nextPrompt: string) => {
    if (isSendingPrompt) {
      return;
    }

    setIsSendingPrompt(true);
    try {
      await onSendPrompt(nextPrompt);
    } finally {
      setIsSendingPrompt(false);
    }
  };

  return (
    <div className="relative z-20 flex h-full min-h-0 flex-col overflow-hidden bg-[radial-gradient(circle_at_top,rgba(36,58,78,0.28),transparent_38%),linear-gradient(180deg,#090909_0%,#040404_100%)] text-white">
      <div className="border-b border-white/8 px-4 py-4 md:px-8">
        <div className="mx-auto flex w-full max-w-7xl flex-wrap items-center gap-3">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl border border-cyan-300/20 bg-cyan-500/10 p-2 text-cyan-100">
              <TerminalSquare className="size-5" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-100/80">
                Jarvez Codex Mode
              </p>
              <p className="text-sm text-white/60">{contextLabel}</p>
            </div>
          </div>

          <div className="flex flex-1 flex-wrap items-center gap-2 md:justify-center">
            <span className="rounded-full border border-cyan-300/25 bg-cyan-500/10 px-3 py-1 text-xs text-cyan-100">
              Codigo
            </span>
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/75">
              {securitySession.activeProjectName ?? 'Nenhum projeto ativo'}
            </span>
            <span
              className={cn(
                'rounded-full border px-3 py-1 text-xs',
                activeCodexTask?.status === 'running'
                  ? 'border-cyan-300/20 bg-cyan-500/10 text-cyan-100'
                  : activeCodexTask?.status === 'completed'
                    ? 'border-emerald-300/20 bg-emerald-500/10 text-emerald-100'
                    : activeCodexTask?.status === 'failed'
                      ? 'border-rose-300/20 bg-rose-500/10 text-rose-100'
                      : 'border-white/10 bg-white/5 text-white/60'
              )}
            >
              {statusLabel(activeCodexTask?.status)}
            </span>
          </div>

          <div className="ml-auto flex flex-wrap items-center gap-2">
            <span
              className={cn('rounded-full border px-3 py-1 text-xs', accessChip.className)}
            >
              {accessChip.label}
            </span>
            <Button type="button" size="sm" variant="secondary" onClick={onToggleSilentMode}>
              {silentMode ? 'Ativar proativo' : 'Modo silencioso'}
            </Button>
            <Button type="button" size="sm" variant="secondary" onClick={onToggleIntegrations}>
              {integrationsMenuOpen ? (
                <PanelRightClose className="size-4" />
              ) : (
                <PanelRightOpen className="size-4" />
              )}
              <span>Integracoes</span>
            </Button>
            <Button
              type="button"
              size="sm"
              variant="secondary"
              onClick={() => window.open('/orchestration', '_blank', 'noopener,noreferrer')}
            >
              <Route className="size-4" />
              <span>Orquestracao</span>
            </Button>
            <Button
              type="button"
              size="sm"
              variant="secondary"
              onClick={() => window.open('/trust-center', '_blank', 'noopener,noreferrer')}
            >
              <ShieldCheck className="size-4" />
              <span>Trust Center</span>
            </Button>
          </div>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-5 md:px-8 md:py-8">
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
          <div className="rounded-[2rem] border border-white/8 bg-white/[0.03] p-5 shadow-2xl backdrop-blur-xl md:p-7">
            <div className="mx-auto max-w-4xl text-center">
              <p className="text-[13px] font-semibold uppercase tracking-[0.28em] text-white/35">
                Workspace de Programacao
              </p>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white md:text-5xl">
                {workspaceHeadline}
              </h1>
              <p className="mx-auto mt-3 max-w-3xl text-sm text-white/60 md:text-base">
                {workspaceSubheadline}
              </p>
            </div>

            <form
              onSubmit={handleSubmitPrompt}
              className="mx-auto mt-6 max-w-4xl rounded-[1.75rem] border border-white/10 bg-black/35 p-3"
            >
              <div className="flex flex-col gap-3 md:flex-row md:items-end">
                <div className="flex-1">
                  <label className="mb-2 block text-left text-[11px] font-semibold uppercase tracking-[0.22em] text-white/40">
                    Prompt tecnico
                  </label>
                  <textarea
                    value={prompt}
                    onChange={(event) => setPrompt(event.target.value)}
                    placeholder="Ex.: analisa a autenticacao do projeto ativo e monte um plano sem editar arquivos."
                    className="min-h-28 w-full resize-none rounded-3xl border border-white/8 bg-white/[0.04] px-4 py-4 text-sm text-white outline-none placeholder:text-white/25 focus:border-cyan-300/25"
                  />
                </div>
                <Button
                  type="submit"
                  size="lg"
                  className="h-14 rounded-2xl px-6"
                  disabled={isSendingPrompt || !prompt.trim()}
                >
                  <Play className="size-4" />
                  {isSendingPrompt ? 'Executando...' : 'Executar'}
                </Button>
              </div>
            </form>

            <div className="mx-auto mt-4 flex max-w-4xl flex-wrap justify-center gap-2">
              <Button
                type="button"
                size="sm"
                variant="secondary"
                disabled={isSendingPrompt}
                onClick={() =>
                  void handleQuickPrompt('Analise o projeto ativo em modo de leitura e resuma a arquitetura.')
                }
              >
                Analisar projeto
              </Button>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                disabled={isSendingPrompt}
                onClick={() =>
                  void handleQuickPrompt('Revise as mudancas atuais do projeto ativo sem editar arquivos.')
                }
              >
                Revisar mudancas
              </Button>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                disabled={isSendingPrompt}
                onClick={() =>
                  void handleQuickPrompt('Explique a arquitetura do projeto ativo e destaque os arquivos principais.')
                }
              >
                Explicar arquitetura
              </Button>
            </div>
          </div>

          <div className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.85fr)]">
            <section className="rounded-[1.75rem] border border-white/8 bg-white/[0.03] p-5 backdrop-blur-xl">
              <div className="flex items-center gap-3">
                <div className="rounded-2xl border border-cyan-300/15 bg-cyan-500/10 p-2 text-cyan-100">
                  <Activity className="size-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">Timeline da Tarefa</p>
                  <p className="text-xs text-white/45">
                    O processo aparece aqui em tempo real, sem depender do chat
                  </p>
                </div>
              </div>

              <div className="mt-4 space-y-3">
                {codexTaskEvents.map((event, index) => (
                  <div
                    key={`${event.task_id ?? 'task'}-${event.timestamp ?? index}-${event.phase ?? 'phase'}`}
                    className="rounded-3xl border border-white/8 bg-black/20 p-4"
                  >
                    <div className="flex items-center gap-2">
                      <span className="rounded-full border border-cyan-300/20 bg-cyan-500/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-cyan-100">
                        {event.phase ?? 'passo'}
                      </span>
                      {event.raw_event_type ? (
                        <span className="font-mono text-[11px] text-white/45">{event.raw_event_type}</span>
                      ) : null}
                      <span className="ml-auto text-[10px] text-white/35">
                        {formatTaskTime(event.timestamp)}
                      </span>
                    </div>
                    <p className="mt-3 text-sm text-white/80">{event.message ?? 'Sem detalhes.'}</p>
                  </div>
                ))}

                {codexTaskEvents.length === 0 ? (
                  <div className="rounded-3xl border border-dashed border-white/8 bg-black/15 p-4">
                    <p className="text-sm text-white/55">
                      Assim que o Jarvez disparar o Codex, cada fase da execucao aparece aqui.
                    </p>
                  </div>
                ) : null}
              </div>
            </section>

            <div className="grid gap-6">
              <section className="rounded-[1.75rem] border border-white/8 bg-white/[0.03] p-5 backdrop-blur-xl">
                <div className="flex items-center gap-3">
                  <div className="rounded-2xl border border-white/8 bg-white/[0.04] p-2 text-white/80">
                    <FolderCode className="size-5" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-white">Contexto da Execucao</p>
                    <p className="text-xs text-white/45">
                      Projeto alvo, comando e resumo da tarefa atual
                    </p>
                  </div>
                </div>

                <div className="mt-4 space-y-4">
                  <div className="rounded-3xl border border-white/8 bg-black/20 p-4">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-white/45">
                      Projeto
                    </p>
                    <p className="mt-3 text-sm text-white/80">
                      {activeCodexTask?.project_name ?? securitySession.activeProjectName ?? 'Nenhum projeto ativo'}
                    </p>
                    {activeCodexTask?.working_directory || securitySession.activeProjectRootPath ? (
                      <p className="mt-2 break-all font-mono text-[11px] text-white/45">
                        {activeCodexTask?.working_directory ?? securitySession.activeProjectRootPath}
                      </p>
                    ) : null}
                  </div>

                  <div className="rounded-3xl border border-white/8 bg-black/20 p-4">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-white/45">
                      Comando do Codex
                    </p>
                    <p className="mt-3 break-all font-mono text-[11px] text-white/70">
                      {activeCodexTask?.command_preview ??
                        'codex exec --json --skip-git-repo-check --sandbox read-only --ephemeral -C <repo> "<prompt>"'}
                    </p>
                  </div>

                  <div className="rounded-3xl border border-white/8 bg-black/20 p-4">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-white/45">
                      Resumo final
                    </p>
                    <p className="mt-3 text-sm leading-6 text-white/80">
                      {activeCodexTask?.summary ?? 'Nenhuma tarefa concluida ainda.'}
                    </p>
                    {activeCodexTask?.error ? (
                      <p className="mt-3 rounded-2xl border border-rose-300/10 bg-rose-500/[0.04] px-3 py-2 text-xs text-rose-100/80">
                        {activeCodexTask.error}
                      </p>
                    ) : null}
                  </div>
                </div>
              </section>

              <section className="rounded-[1.75rem] border border-white/8 bg-white/[0.03] p-5 backdrop-blur-xl">
                <div className="flex items-center gap-3">
                  <div className="rounded-2xl border border-emerald-300/15 bg-emerald-500/10 p-2 text-emerald-100">
                    <Sparkles className="size-5" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-white">Historico de Tarefas</p>
                    <p className="text-xs text-white/45">Ultimas execucoes do Codex nesta maquina</p>
                  </div>
                </div>

                <div className="mt-4 space-y-3">
                  {codexTaskHistory.map((entry) => (
                    <div
                      key={entry.task_id ?? `${entry.project_name}-${entry.started_at}`}
                      className="rounded-3xl border border-white/8 bg-black/20 p-4"
                    >
                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            'rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide',
                            entry.status === 'completed'
                              ? 'border-emerald-300/20 bg-emerald-500/10 text-emerald-100'
                              : entry.status === 'failed'
                                ? 'border-rose-300/20 bg-rose-500/10 text-rose-100'
                                : entry.status === 'cancelled'
                                  ? 'border-amber-300/20 bg-amber-500/10 text-amber-100'
                                  : 'border-cyan-300/20 bg-cyan-500/10 text-cyan-100'
                          )}
                        >
                          {statusLabel(entry.status)}
                        </span>
                        <span className="text-xs text-white/55">{entry.project_name ?? 'Projeto'}</span>
                        <span className="ml-auto text-[10px] text-white/35">
                          {formatTaskTime(entry.finished_at ?? entry.started_at)}
                        </span>
                      </div>
                      <p className="mt-3 text-sm text-white/80">
                        {entry.request ?? entry.summary ?? 'Tarefa sem resumo'}
                      </p>
                      {entry.summary && entry.summary !== entry.request ? (
                        <p className="mt-2 text-xs text-white/45">{entry.summary}</p>
                      ) : null}
                    </div>
                  ))}

                  {codexTaskHistory.length === 0 ? (
                    <div className="rounded-3xl border border-dashed border-white/8 bg-black/15 p-4">
                      <p className="text-sm text-white/55">
                        Nenhuma tarefa registrada ainda. Assim que o Codex rodar, o historico aparece aqui.
                      </p>
                    </div>
                  ) : null}
                </div>
              </section>

              <section className="rounded-[1.75rem] border border-white/8 bg-white/[0.03] p-5 backdrop-blur-xl">
                <div className="flex items-center gap-3">
                  <div className="rounded-2xl border border-emerald-300/15 bg-emerald-500/10 p-2 text-emerald-100">
                    <ShieldCheck className="size-5" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-white">Guardrails Ativos</p>
                    <p className="text-xs text-white/45">Politica da V1 para o Codex CLI</p>
                  </div>
                </div>

                <div className="mt-4 space-y-3">
                  <div className="rounded-3xl border border-white/8 bg-black/20 p-4 text-sm text-white/70">
                    O Jarvez roda o Codex com sandbox read-only e sem mutacao automatica nesta fase.
                  </div>
                  <div className="rounded-3xl border border-white/8 bg-black/20 p-4 text-sm text-white/70">
                    Toda tarefa precisa de um projeto resolvido antes da execucao.
                  </div>
                  <div className="rounded-3xl border border-white/8 bg-black/20 p-4 text-sm text-white/70">
                    A narracao acompanha as fases principais da tarefa, nao cada linha bruta do terminal.
                  </div>
                </div>
              </section>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
