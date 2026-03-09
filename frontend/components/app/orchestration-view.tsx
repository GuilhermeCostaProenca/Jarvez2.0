'use client';

import { useEffect, useState } from 'react';
import { Activity, Bot, Route, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { readStoredModelRoute, readStoredSubagents } from '@/lib/orchestration-storage';
import type { ModelRouteDecision, SubagentState } from '@/lib/types/realtime';

function formatDate(value?: string) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(date);
}

export function OrchestrationView() {
  const [route, setRoute] = useState<ModelRouteDecision | null>(null);
  const [subagents, setSubagents] = useState<SubagentState[]>([]);

  useEffect(() => {
    const sync = () => {
      setRoute(readStoredModelRoute());
      setSubagents(readStoredSubagents());
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
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(56,189,248,0.12),_transparent_35%),radial-gradient(circle_at_top_right,_rgba(34,197,94,0.1),_transparent_28%),linear-gradient(180deg,#030711_0%,#0b1327_100%)] px-4 py-8 text-white">
      <div className="mx-auto max-w-5xl space-y-6">
        <header className="rounded-[2rem] border border-white/10 bg-black/30 px-6 py-5 backdrop-blur-xl">
          <div className="mb-2 flex items-center gap-2 text-cyan-200">
            <Route className="size-5" />
            <span className="text-xs font-semibold tracking-[0.24em] uppercase">Jarvez Orchestration</span>
          </div>
          <h1 className="text-2xl font-semibold">Roteamento e Subagentes</h1>
          <p className="mt-1 text-sm text-white/60">
            Visao dedicada de roteamento multi-model e execucoes em subagentes.
          </p>
        </header>

        <section className="rounded-[2rem] border border-white/10 bg-black/25 p-5 backdrop-blur-xl">
          <div className="mb-3 flex items-center gap-2 text-amber-300">
            <Sparkles className="size-4" />
            <span className="text-xs font-semibold tracking-[0.2em] uppercase">Ultima rota</span>
          </div>
          {route ? (
            <div className="grid gap-3 text-sm text-white/80 md:grid-cols-2">
              <p>Task type: <strong>{route.task_type ?? '-'}</strong></p>
              <p>Risco: <strong>{route.risk ?? '-'}</strong></p>
              <p>Primario: <strong>{route.primary_provider ?? '-'}</strong></p>
              <p>Usado: <strong>{route.used_provider ?? '-'}</strong></p>
              <p>Fallback: <strong>{route.fallback_used ? 'sim' : 'nao'}</strong></p>
              <p>Gerado em: <strong>{formatDate(route.generated_at)}</strong></p>
              <p className="md:col-span-2">Motivo: <strong>{route.reason ?? '-'}</strong></p>
            </div>
          ) : (
            <p className="text-sm text-white/60">Nenhuma decisao de rota registrada ainda.</p>
          )}
        </section>

        <section className="rounded-[2rem] border border-white/10 bg-black/25 p-5 backdrop-blur-xl">
          <div className="mb-3 flex items-center gap-2 text-cyan-200">
            <Bot className="size-4" />
            <span className="text-xs font-semibold tracking-[0.2em] uppercase">Subagentes</span>
          </div>
          {subagents.length > 0 ? (
            <div className="space-y-3">
              {subagents.map((item) => (
                <article key={item.subagent_id} className="rounded-[1.25rem] border border-white/10 bg-white/[0.03] px-4 py-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-sm font-semibold">{item.subagent_id}</p>
                    <p className="text-xs text-white/60">{item.status}</p>
                  </div>
                  <p className="mt-1 text-xs text-white/65">
                    Provider: {item.route_provider ?? '-'} | Atualizado: {formatDate(item.updated_at)}
                  </p>
                  {item.result_summary ? (
                    <p className="mt-2 text-sm text-white/75">{item.result_summary}</p>
                  ) : null}
                </article>
              ))}
            </div>
          ) : (
            <p className="text-sm text-white/60">Nenhum subagente registrado nesta sessao.</p>
          )}
        </section>

        <div className="flex justify-end">
          <Button type="button" variant="secondary" onClick={() => window.location.reload()}>
            <Activity className="size-4" />
            <span>Atualizar</span>
          </Button>
        </div>
      </div>
    </main>
  );
}
