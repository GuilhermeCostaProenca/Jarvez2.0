'use client';

import { useEffect, useState } from 'react';
import { Clock3, ExternalLink, RefreshCw, Search, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  readStoredResearchDashboard,
  readStoredResearchSchedules,
} from '@/lib/research-dashboard-storage';
import type { ResearchDashboard, ResearchSchedule } from '@/lib/types/realtime';

function formatTimestamp(value?: string) {
  if (!value) {
    return 'Agora';
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return 'Agora';
  }

  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(parsed);
}

export function ResearchDashboardView() {
  const [dashboard, setDashboard] = useState<ResearchDashboard | null>(null);
  const [schedules, setSchedules] = useState<ResearchSchedule[]>([]);

  useEffect(() => {
    const syncFromStorage = () => {
      setDashboard(readStoredResearchDashboard());
      setSchedules(readStoredResearchSchedules());
    };

    syncFromStorage();
    window.addEventListener('storage', syncFromStorage);
    const timer = window.setInterval(syncFromStorage, 5_000);

    return () => {
      window.removeEventListener('storage', syncFromStorage);
      window.clearInterval(timer);
    };
  }, []);

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.08),_transparent_30%),radial-gradient(circle_at_top_right,_rgba(251,191,36,0.08),_transparent_26%),linear-gradient(180deg,#05070c_0%,#0b1020_100%)] px-4 py-8 text-white">
      <div className="mx-auto max-w-6xl">
        <header className="mb-8 flex flex-wrap items-center justify-between gap-4 rounded-[2rem] border border-white/10 bg-black/30 px-6 py-5 backdrop-blur-xl">
          <div className="min-w-0">
            <div className="mb-2 flex items-center gap-2 text-cyan-200">
              <Search className="size-5" />
              <span className="text-xs font-semibold tracking-[0.24em] uppercase">
                Jarvez Research
              </span>
            </div>
            <h1 className="truncate text-2xl font-semibold">
              {dashboard ? dashboard.query : 'Dashboard de pesquisa'}
            </h1>
            <p className="mt-1 text-sm text-white/60">
              {dashboard
                ? `Atualizado em ${formatTimestamp(dashboard.generatedAt)}`
                : 'Nenhuma pesquisa foi gerada ainda nesta maquina.'}
            </p>
          </div>

          <Button type="button" variant="secondary" onClick={() => window.location.reload()}>
            <RefreshCw className="size-4" />
            <span>Atualizar</span>
          </Button>
        </header>

        <div className="grid gap-6 lg:grid-cols-[1.4fr_0.9fr]">
          <section className="space-y-6">
            {dashboard ? (
              <>
                <div className="rounded-[2rem] border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl">
                  <div className="mb-3 flex items-center gap-2 text-amber-300">
                    <Sparkles className="size-4" />
                    <span className="text-xs font-semibold tracking-[0.2em] uppercase">
                      Resumo consolidado
                    </span>
                  </div>
                  <p className="text-sm leading-7 text-white/78">{dashboard.summary}</p>
                </div>

                {dashboard.images.length > 0 && (
                  <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                    {dashboard.images.slice(0, 4).map((imageUrl) => (
                      <div
                        key={imageUrl}
                        className="overflow-hidden rounded-[1.5rem] border border-white/10 bg-white/[0.03]"
                      >
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={imageUrl}
                          alt=""
                          className="h-40 w-full object-cover"
                          loading="lazy"
                        />
                      </div>
                    ))}
                  </div>
                )}

                <div className="space-y-3">
                  {dashboard.results.map((result) => (
                    <article
                      key={result.url}
                      className="rounded-[2rem] border border-white/10 bg-black/25 p-5 backdrop-blur-xl"
                    >
                      <div className="flex flex-col gap-4 sm:flex-row">
                        {result.imageUrl ? (
                          <div className="overflow-hidden rounded-[1.25rem] border border-white/10 bg-white/5 sm:w-36">
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img
                              src={result.imageUrl}
                              alt=""
                              className="h-28 w-full object-cover sm:h-full"
                              loading="lazy"
                            />
                          </div>
                        ) : null}

                        <div className="min-w-0 flex-1">
                          <p className="text-[11px] font-semibold tracking-[0.22em] text-cyan-200/70 uppercase">
                            {result.domain}
                          </p>
                          <h2 className="mt-2 text-lg font-semibold text-white">{result.title}</h2>
                          {(result.snippet || result.pageDescription) && (
                            <p className="mt-2 text-sm leading-6 text-white/65">
                              {result.snippet || result.pageDescription}
                            </p>
                          )}
                          <div className="mt-4">
                            <Button
                              type="button"
                              variant="secondary"
                              onClick={() =>
                                window.open(result.url, '_blank', 'noopener,noreferrer')
                              }
                            >
                              <ExternalLink className="size-4" />
                              <span>Abrir fonte</span>
                            </Button>
                          </div>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              </>
            ) : (
              <div className="rounded-[2rem] border border-dashed border-white/15 bg-black/25 p-8 text-sm text-white/60">
                Quando o Jarvez executar uma `web_search_dashboard`, o compilado aparece aqui.
              </div>
            )}
          </section>

          <aside className="space-y-4">
            <div className="rounded-[2rem] border border-white/10 bg-black/25 p-5 backdrop-blur-xl">
              <div className="mb-3 flex items-center gap-2 text-amber-300">
                <Clock3 className="size-4" />
                <span className="text-xs font-semibold tracking-[0.2em] uppercase">
                  Briefings agendados
                </span>
              </div>

              {schedules.length > 0 ? (
                <div className="space-y-2">
                  {schedules.map((schedule) => (
                    <div
                      key={schedule.id}
                      className="rounded-[1.25rem] border border-white/10 bg-white/[0.03] px-4 py-3"
                    >
                      <p className="text-sm font-semibold text-white">{schedule.query}</p>
                      <p className="mt-1 text-xs text-white/55">
                        Diario as {schedule.timeOfDay}
                        {schedule.lastRunOn ? ` | Ultima execucao: ${schedule.lastRunOn}` : ''}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-white/55">
                  Nenhuma rotina salva ainda. Peca algo como &quot;todo dia as 08:00 pesquise
                  X&quot;.
                </p>
              )}
            </div>
          </aside>
        </div>
      </div>
    </main>
  );
}
