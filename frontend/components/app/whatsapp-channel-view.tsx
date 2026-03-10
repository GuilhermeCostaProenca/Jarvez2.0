'use client';

import { useEffect, useState } from 'react';
import { MessageCircle, RefreshCcw, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { readStoredWhatsAppChannelStatus } from '@/lib/orchestration-storage';

type WhatsAppChannelStatus = {
  mode?: string;
  legacy_enabled?: boolean;
  fallback_active?: boolean;
  history_source?: string;
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

export function WhatsAppChannelView() {
  const [status, setStatus] = useState<WhatsAppChannelStatus | null>(null);

  useEffect(() => {
    const sync = () => {
      const next = readStoredWhatsAppChannelStatus();
      setStatus(next as WhatsAppChannelStatus | null);
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
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(34,197,94,0.12),_transparent_30%),radial-gradient(circle_at_top_right,_rgba(16,185,129,0.1),_transparent_28%),linear-gradient(180deg,#04110b_0%,#061822_100%)] px-4 py-8 text-white">
      <div className="mx-auto max-w-4xl space-y-6">
        <header className="rounded-[2rem] border border-white/10 bg-black/30 px-6 py-5 backdrop-blur-xl">
          <div className="mb-2 flex items-center gap-2 text-emerald-200">
            <MessageCircle className="size-5" />
            <span className="text-xs font-semibold tracking-[0.24em] uppercase">WhatsApp Channel</span>
          </div>
          <h1 className="text-2xl font-semibold">Canal Remoto do Jarvez</h1>
          <p className="mt-1 text-sm text-white/60">
            Status do rollout MCP bidirecional com fallback em webhook legado.
          </p>
        </header>

        <section className="rounded-[2rem] border border-white/10 bg-black/25 p-5 backdrop-blur-xl">
          <div className="mb-3 flex items-center gap-2 text-cyan-200">
            <ShieldCheck className="size-4" />
            <span className="text-xs font-semibold tracking-[0.2em] uppercase">Estado Atual</span>
          </div>
          {status ? (
            <div className="grid gap-2 text-sm text-white/80 md:grid-cols-2">
              <p>Modo: <strong>{status.mode ?? '-'}</strong></p>
              <p>Legacy Cloud API: <strong>{status.legacy_enabled ? 'ativo' : 'inativo'}</strong></p>
              <p>Fallback ativo: <strong>{status.fallback_active ? 'sim' : 'nao'}</strong></p>
              <p>Fonte de historico: <strong>{status.history_source ?? '-'}</strong></p>
              <p>MCP habilitado: <strong>{status.mcp?.enabled ? 'sim' : 'nao'}</strong></p>
              <p>MCP conectado: <strong>{status.mcp?.connected ? 'sim' : 'nao'}</strong></p>
              <p>Historico MCP: <strong>{status.mcp?.history_available ? 'disponivel' : 'indisponivel'}</strong></p>
              <p>DB MCP: <strong>{status.mcp?.messages_db_path ?? '-'}</strong></p>
              <p>Msgs totais: <strong>{status.messages?.total ?? 0}</strong></p>
              <p>Inbound/Outbound: <strong>{status.messages?.inbound_total ?? 0}/{status.messages?.outbound_total ?? 0}</strong></p>
              <p>Ultimo inbound: <strong>{status.messages?.last_inbound_at ?? '-'}</strong></p>
              <p>Ultimo outbound: <strong>{status.messages?.last_outbound_at ?? '-'}</strong></p>
              <p className="md:col-span-2">Diagnostico: <strong>{status.mcp?.detail ?? '-'}</strong></p>
            </div>
          ) : (
            <p className="text-sm text-white/60">
              Ainda sem status local. Execute `whatsapp_channel_status` na sessao para atualizar.
            </p>
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
