# Next Cycle Plan - Hardening do Core + Autonomia Real

## Visao Geral

Objetivo do ciclo:
- reduzir risco estrutural do core sem reescrever runtime;
- mover estado critico para backend persistente (SQLite);
- unificar decisao de modelo para voz e orquestracao;
- abrir trilha de autonomia real (browser agent + canal remoto WhatsApp + workflow ideia->codigo).

Principio de rollout:
- mudancas pequenas e isoladas;
- compatibilidade com fluxo atual;
- validacao continua com testes particionados.

## Frente 1 - Hardening do Core

### F1.1 Caracterizacao e rede de seguranca

Status:
- [x] suites particionadas criadas:
  - `backend/test_action_core.py`
  - `backend/test_session_state.py`
  - `backend/test_policy_ops.py`
  - `backend/test_projects_code.py`
  - `backend/test_integrations_whatsapp.py` (stub)
  - `backend/test_integrations_notes_media.py` (stub)
  - `backend/test_rpg.py`
- [x] `test_actions` mantido como fonte de verdade.
- [x] suites principais rodando verde para core/policy/session/projects.

Criterio de aceite:
- `py_compile` sem erro;
- suites particionadas verdes.

### F1.2 Extracao do nucleo de actions

Status:
- [x] pacote `backend/actions_core/` criado:
  - `types.py`, `registry.py`, `state.py`, `store.py`, `events.py`, `dispatch.py`.
- [x] `backend/actions.py` virou fachada compat com imports de `actions_core`.
- [x] `codex_cli.build_exec_command(...)` aceita `sandbox_mode` e `ephemeral`.

Criterio de aceite:
- `dispatch_action` continua retornando envelope atual;
- registry e tipos preservados.

### F1.3 Quebra por dominio (incremental)

Status:
- [~] iniciado com novos modulos dedicados sem romper `actions.py`:
  - `backend/browser_agent/`
  - `backend/workflows/`
  - `backend/actions_domains/whatsapp_channel.py`
  - `backend/integrations/whatsapp_mcp_client.py`
- [ ] migracao completa dos dominios historicos ainda pendente.

Proxima ordem recomendada:
1. `session.py`
2. `research.py`
3. `whatsapp.py`
4. `spotify.py`
5. `onenote.py`
6. `home_assistant.py`
7. `thinq.py` + `ac.py`
8. `projects.py`
9. `code_actions.py`
10. `codex.py`
11. `orchestration.py`
12. `policy.py` + `ops.py`
13. `rpg.py`

### F1.4 Persistencia em SQLite + snapshot

Status:
- [x] SQLite unico em `backend/data/jarvez_state.db` via `actions_core/store.py`.
- [x] tabelas criadas:
  - `session_state`
  - `event_state`
  - `pending_confirmations`
  - `authenticated_sessions`
- [x] dual-write/read-through aplicado para:
  - autenticacao
  - confirmacoes pendentes
  - memory scope
  - persona mode
  - capability mode
  - active project
  - active character
  - active codex task + history
- [x] `session_snapshot` implementado (`backend/session_snapshot.py`) e publicado:
  - no start da sessao (`agent.py`)
  - apos `dispatch_action`.

Criterio de aceite:
- restart preserva estado principal;
- frontend hidrata por snapshot sem depender so de localStorage.

### F1.5 Unificacao runtime voz + roteador

Status:
- [x] camada `backend/runtime/model_gateway.py` com `RuntimeDecision`.
- [x] adapter realtime em `backend/runtime/realtime_adapters.py`.
- [x] `agent.py` usa gateway para decisao de provider realtime.
- [x] decisao de rota persistida em `event_state:model_route`.

Criterio de aceite:
- sessao LiveKit continua subindo;
- rota aparece no frontend/orchestration.

## Frente 2 - Autonomia Real

### F2.0 Substrato de canais

Status:
- [x] `backend/channels/{types,router,audit,livekit_adapter}.py`.
- [x] `backend/channels/whatsapp_adapter.py` com envelope inbound normalizado.

Criterio de aceite:
- canais tipados sem quebrar fluxo LiveKit.

### F2.1 Browser Agent (Playwright MCP)

Status:
- [x] `backend/browser_agent/{state,policies,mcp_client,runner}.py`.
- [x] actions publicas:
  - `browser_agent_run`
  - `browser_agent_status`
  - `browser_agent_cancel`
- [x] eventos:
  - `browser_task_started`
  - `browser_task_failed`
- [x] estado persistido em `event_state:browser_tasks`.
- [x] UI dedicada:
  - `frontend/app/browser-agent/page.tsx`
  - `frontend/components/app/browser-agent-view.tsx`

Observacao:
- execucao MCP esta em modo de fila/healthcheck seguro;
- loop completo de automacao browser ainda sera evoluido na proxima iteracao.

### F2.2 WhatsApp bidirecional (MCP + rollback legado)

Status:
- [x] cliente de status MCP:
  - `backend/integrations/whatsapp_mcp_client.py`
- [x] action publica:
  - `whatsapp_channel_status`
- [x] webhook legado ganhou bridge opcional para MCP:
  - `frontend/app/api/whatsapp/webhook/route.ts`
  - variavel: `WHATSAPP_MCP_BRIDGE_URL`
- [x] UI dedicada:
  - `frontend/app/integrations/whatsapp/page.tsx`
  - `frontend/components/app/whatsapp-channel-view.tsx`
- [ ] ingestao/bidirecional completo por QR ainda pendente.

### F2.3 Loop proativo

Status:
- [~] base pronta com `automation_status` e `automation_run_now`.
- [x] persistencia de `automation_state`.
- [ ] scheduler/triggers dedicados (`backend/automation/*`) ainda pendente.

### F2.4 Fluxo "tenho uma ideia" -> codigo

Status:
- [x] actions publicas:
  - `workflow_run`
  - `workflow_status`
  - `workflow_cancel`
- [x] engine inicial:
  - `backend/workflows/{types,engine,state}.py`
- [x] estado persistido em `event_state:workflow_state`.
- [ ] execucao automatica com `codex exec --sandbox workspace-write` apos checkpoint ainda pendente.

## Dependencias Entre Frentes

- F1.1 -> pre requisito global.
- F1.4 -> pre requisito para estado de browser/workflow/whatsapp sobreviver a restart.
- F1.5 + F2.0 -> base comum de decisao/modelo e canal.
- F2.1/F2.2/F2.4 dependem de persistencia e eventos estaveis.

## Ordem de Execucao Recomendada (proximas iteracoes)

1. concluir split por dominio em `actions_domains` (session/research/whatsapp).
2. completar runtime do browser MCP (execucao de tarefas reais com guardrails).
3. completar canal WhatsApp MCP bidirecional com pairing e dedupe.
4. adicionar `backend/automation/*` com scheduler de briefing e trigger de chegada.
5. fechar workflow ideia->codigo com gates de aprovacao e validacao automatica.

## Riscos e Mitigacoes

- Risco: regressao no `actions.py`.
  - Mitigacao: manter fachada compativel + testes particionados.
- Risco: lock/concorrencia SQLite em Windows/OneDrive.
  - Mitigacao: writer unico Python + WAL + `busy_timeout`.
- Risco: divergencia UI/backend.
  - Mitigacao: `session_snapshot` + fallback localStorage.
- Risco: canais remotos sem isolamento.
  - Mitigacao: envelope tipado por canal + status explicito `legacy_v1`.

## Complexidade por item

- Alta:
  - split completo de `actions.py`
  - WhatsApp MCP bidirecional completo
  - browser agent com execucao full
  - workflow ideia->codigo com aplicacao automatica
  - automation scheduler/triggers
- Media:
  - gateway de modelo/runtime
  - persistencia de eventos e snapshots
  - UI dedicada de autonomia/trust
- Baixa:
  - status actions auxiliares
  - wrappers de testes
  - bridge opcional webhook->MCP
