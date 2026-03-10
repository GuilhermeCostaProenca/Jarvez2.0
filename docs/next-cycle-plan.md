# Next Cycle Plan: Hardening do Core + Autonomia Real

## Resumo

Objetivo do ciclo: reduzir o risco estrutural do core sem reescrever o runtime, colocar o backend como fonte de verdade do estado de sessÃ£o, unificar a decisÃ£o de modelo entre voz e orquestraÃ§Ã£o, e entÃ£o abrir duas superfÃ­cies de autonomia real que hoje faltam: browser agent e canal remoto bidirecional via WhatsApp.

Baseline confirmada no cÃ³digo real: [backend/actions.py](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\backend\actions.py) tem 12.347 linhas e concentra registry, dispatch, helpers de integraÃ§Ã£o, estado de sessÃ£o e parte de ops; [backend/agent.py](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\backend\agent.py) instancia Google Realtime diretamente; [frontend/hooks/useAgentActionEvents.ts](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\frontend\hooks\useAgentActionEvents.ts) e [frontend/lib/orchestration-storage.ts](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\frontend\lib\orchestration-storage.ts) hidratam quase todo o estado operacional via `localStorage`; [frontend/app/api/whatsapp/webhook/route.ts](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\frontend\app\api\whatsapp\webhook\route.ts) sÃ³ normaliza webhook para JSON local e o backend envia via Cloud API. O backend compila, testes unitÃ¡rios menores passam, e `test_actions.py` jÃ¡ cobre bastante coisa, mas estÃ¡ monolÃ­tico e lento para servir de rede de seguranÃ§a de refactor.

## MudanÃ§as de Interface e Tipos

- Novo pacote `backend/actions_core/`: `types.py`, `registry.py`, `state.py`, `store.py`, `events.py`, `dispatch.py`.
- Novo pacote `backend/actions_domains/`: `session.py`, `research.py`, `whatsapp.py`, `spotify.py`, `onenote.py`, `home_assistant.py`, `thinq.py`, `ac.py`, `projects.py`, `code_actions.py`, `codex.py`, `orchestration.py`, `policy.py`, `ops.py`, `rpg.py`.
- Novo SQLite backend Ãºnico: `backend/data/jarvez_state.db`.
- Novo evento em `lk.agent.events`: `session_snapshot`.
- Novos eventos planejados: `browser_task_started`, `browser_task_progress`, `browser_task_completed`, `browser_task_failed`, `workflow_started`, `workflow_progress`, `workflow_completed`, `workflow_failed`.
- Novas actions pÃºblicas planejadas: `browser_agent_run`, `browser_agent_status`, `browser_agent_cancel`, `workflow_run`, `workflow_status`, `workflow_cancel`, `automation_status`, `automation_run_now`.
- `codex_cli.build_exec_command(...)` passa a aceitar `sandbox_mode` e `ephemeral` como parÃ¢metros; default continua `read-only`.
- `frontend/lib/types/realtime.ts` ganha `SessionSnapshot`, `BrowserTaskState`, `WorkflowState`, `AutomationState`.
- `frontend/hooks/useAgentActionEvents.ts` passa a hidratar do backend por `session_snapshot`; `localStorage` vira cache/fallback, nÃ£o fonte de verdade.

## Frente 1: Hardening do Core

### F1.1. CaracterizaÃ§Ã£o e rede de seguranÃ§a antes de mover cÃ³digo
- Arquivos: `backend/test_actions.py`, `backend/test_memory_scope.py`, `backend/test_codex_cli.py`, `backend/test_project_catalog.py`, `frontend/package.json`, `frontend/hooks/useAgentActionEvents.ts`.
- ExecuÃ§Ã£o: primeiro dividir `test_actions.py` em suÃ­tes menores por domÃ­nio sem mudar assertions; depois adicionar Vitest no frontend sÃ³ para `useAgentActionEvents` e storages crÃ­ticos.
- Ordem: `test_action_core.py` â†’ `test_session_state.py` â†’ `test_policy_ops.py` â†’ `test_projects_code.py` â†’ `test_integrations_whatsapp.py` â†’ `test_integrations_notes_media.py` â†’ `test_rpg.py` â†’ `useAgentActionEvents.test.ts` â†’ `orchestration-storage.test.ts`.
- Pode quebrar: falsa sensaÃ§Ã£o de cobertura, refactor sem caracterizaÃ§Ã£o dos payloads, regressÃ£o silenciosa no parser do frontend.
- Validar: backend `py_compile`; rodar suÃ­tes particionadas; no frontend validar parse de `function_tools_executed`, `autonomy_notice`, `codex_task_*` e futuro `session_snapshot`.
- Complexidade: MÃ©dia.

### F1.2. Extrair o nÃºcleo estÃ¡vel do sistema de actions
- Arquivos: criar `backend/actions_core/{types,registry,events,dispatch,state}.py`; editar [backend/actions.py](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\backend\actions.py), [backend/agent.py](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\backend\agent.py).
- Escopo: mover `ActionResult`, `ActionContext`, `ActionSpec`, `PendingConfirmation`, `AuthenticatedSession`, helpers de publicaÃ§Ã£o de eventos, `register_action`, `get_action`, `get_exposed_actions`, `_ensure_result_envelope`, `dispatch_action`, getters/setters de estado de sessÃ£o.
- Ordem: extrair tipos/registry primeiro; depois events/state; por Ãºltimo dispatch; `backend/actions.py` vira faÃ§ade compatÃ­vel.
- Pode quebrar: import circular, perda de `ACTION_REGISTRY`, envelope de evidence/policy, publicaÃ§Ã£o em `lk.agent.events`.
- Validar: `dispatch_action` continua devolvendo o mesmo JSON; smoke manual de confirmaÃ§Ã£o, auth e subagent ainda aparece na UI.
- Complexidade: Alta.

### F1.3. Quebra por domÃ­nio em ordem segura
Status atual de extração: `session.py`, `research.py`, `whatsapp.py`, `spotify.py`, `onenote.py`, `home_assistant.py`, `thinq.py`, `ac.py`, `projects.py`, `code_actions.py`, `codex.py`, `orchestration.py`, `policy.py`, `ops.py` e `rpg.py` já estão com handlers migrados e `actions.py` atuando como façade compatível.

1. `session.py`: auth, confirmaÃ§Ã£o, memory scope, persona, voice profile e payloads de sessÃ£o; depende sÃ³ de `actions_core`; validar `authenticate_identity`, `confirm_action`, `verify_voice_identity`, `set_memory_scope`, `set_persona_mode`.
2. `research.py`: `_web_search_dashboard` e `_save_web_briefing_schedule`; baixo acoplamento; validar dashboard e schedule.
3. `whatsapp.py`: normalize/send/read/TTS atuais; validar sem tocar ainda no webhook legacy.
4. `spotify.py`: tokens, aliases, status/playback/playlist; validar apenas com mocks HTTP.
5. `onenote.py`: auth cache, list/search/page append/create; validar sÃ³ com mocks HTTP.
6. `home_assistant.py`: `call_service`, lights, desktop open, local command, git clone/push; este passo sÃ³ entra depois de `test_projects_code.py` pronto.
7. `thinq.py` e `ac.py`: ThinQ genÃ©rico e AC arrival prefs; manter separados porque AC jÃ¡ Ã© produto prÃ³prio.
8. `projects.py`: catÃ¡logo, seleÃ§Ã£o, refresh, GitHub catalog/clone-register.
9. `code_actions.py`: worker status/read/search/git diff/status/explain/propose/apply/run command.
10. `codex.py`: task state, streaming events, history e cancelamento.
11. `orchestration.py`: providers health, skills, route preview, orchestrate, subagents.
12. `policy.py` e `ops.py`: risk matrix, trust drift, killswitch, canary, incident, playbooks, control loop.
13. `rpg.py`: por Ãºltimo, porque mistura PDF, OneNote, arquivos locais e active character.
- Pode quebrar: helpers compartilhados â€œvazandoâ€ entre mÃ³dulos; payloads de `active_project`, `security_status`, `policy`, `codex_history`; imports cÃ­clicos entre `rpg.py` e `onenote.py`, `ops.py` e `policy.py`, `code_actions.py` e `projects.py`.
- Validar: cada mÃ³dulo sÃ³ entra depois de sua suÃ­te dedicada passar e de um smoke manual curto do domÃ­nio.
- Complexidade: Alta.

### F1.4. PersistÃªncia simples em SQLite com dual-write e leitura gradual
Status atual: `store.py` + dual-write/read-prefer-SQLite já ativos em `actions.py`; `session_snapshot` já hidrata o frontend e agora é publicado no start, pós-action e reconnect (`participant_connected`) no `agent.py`.
- Arquivos: criar `backend/actions_core/store.py` e `backend/session_snapshot.py`; editar [backend/actions.py](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\backend\actions.py), [backend/agent.py](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\backend\agent.py), [frontend/hooks/useAgentActionEvents.ts](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\frontend\hooks\useAgentActionEvents.ts), [frontend/lib/types/realtime.ts](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\frontend\lib\types\realtime.ts), `frontend/lib/{research-dashboard-storage,coding-history-storage,orchestration-storage}.ts`.
- Tabelas: `session_state(participant_identity, room, namespace, payload_json, updated_at)`, `pending_confirmations(token, participant_identity, room, action_name, params_json, expires_at)`, `authenticated_sessions(participant_identity, room, auth_method, expires_at, last_activity_at)`, `event_state(participant_identity, room, namespace, payload_json, updated_at)`.
- Namespaces persistidos neste ciclo: `memory_scope`, `persona_mode`, `capability_mode`, `active_project`, `active_character`, `active_codex_task`, `codex_history`, `research_schedules`, `model_route`, `subagent_states`, `policy_events`, `execution_traces`, `eval_baseline_summary`, `eval_metrics`, `eval_metrics_summary`, `slo_report`, `providers_health`, `feature_flags`, `canary_state`, `incident_snapshot`, `playbook_report`, `auto_remediation`, `canary_promotion`, `control_tick`.
- EstratÃ©gia: primeiro dual-write; depois read-prefer-SQLite com fallback para memÃ³ria/localStorage; por fim `agent.py` publica `session_snapshot` ao iniciar a sessÃ£o e ao reconectar.
- Pode quebrar: mismatch entre snapshot e cache local, TTL de auth/confirmation, lock de SQLite em Windows/OneDrive, restauraÃ§Ã£o parcial do estado.
- Validar: reiniciar backend e confirmar restauraÃ§Ã£o de persona/projeto/coding mode/codex history/research schedules; confirmar que `localStorage` vazio nÃ£o quebra UI; usar WAL e `busy_timeout` igual aos Ã­ndices jÃ¡ existentes.
- Complexidade: Alta.

### F1.5. Unificar voice runtime e multi-model router sob uma camada de decisÃ£o
Status atual: voice e orquestracao/subagent ja passam pelo model_gateway; route_orchestration aplica provider_order derivado do RuntimeDecision e persiste model_route normalmente.
- Arquivos: criar `backend/runtime/model_gateway.py` e `backend/runtime/realtime_adapters.py`; editar [backend/agent.py](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\backend\agent.py), [backend/providers/provider_router.py](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\backend\providers\provider_router.py), [backend/orchestration/router.py](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\backend\orchestration\router.py), providers.
- DecisÃ£o fechada: neste ciclo o gateway escolhe entre adapters por capability; `voice_realtime` continua selecionando Google por ser o Ãºnico adapter LiveKit-realtime existente, mas a escolha passa pela mesma camada que jÃ¡ decide `chat/code/review/research/automation`.
- SaÃ­da do gateway: `RuntimeDecision` com `intent`, `task_type`, `risk`, `required_capabilities`, `primary_provider`, `fallback_provider`, `reason`.
- Pode quebrar: startup da sessÃ£o LiveKit, seleÃ§Ã£o de tools, telemetria de provider usado, fallback de orchestration.
- Validar: teste unitÃ¡rio de roteamento; smoke â€œconectar e receber primeira respostaâ€; `model_route` persistido e renderizado na UI.
- Complexidade: Alta.

## Frente 2: Autonomia Real

### F2.0. Substrato mÃ­nimo de gateway/canais antes das integraÃ§Ãµes novas
Status atual: channels/types+router+livekit_adapter+audit ativos e integrados; publish de lk.agent.events e telemetry inbound do LiveKit passam pelo adapter sem mudanca de UX.
- Arquivos: criar `backend/channels/{types,router,audit,livekit_adapter}.py`; editar [backend/agent.py](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\backend\agent.py), `backend/actions_core/events.py`, `backend/session_snapshot.py`.
- Envelope padrÃ£o: `InboundEnvelope`, `OutboundEnvelope`, `ChannelIdentity`, `ExecutionAuditRecord`.
- Regra: LiveKit passa primeiro por esse adapter sem alterar UX; browser agent e WhatsApp entram depois usando o mesmo envelope.
- Pode quebrar: duplicaÃ§Ã£o de mensagens/eventos e perda de contexto por room/participant.
- Validar: LiveKit continua funcional sem WhatsApp/browser ligados.
- Complexidade: MÃ©dia.

### F2.1. Browser agent com Playwright MCP, sem expor dezenas de tools brutas ao modelo
Status atual: browser_agent_run/status/cancel já emite started/progress/completed|failed; runner executa browser_navigate + browser_snapshot via MCP HTTP (`/mcp`) com allowlist obrigatório, valida domínio final após navegação, captura evidência estruturada e frontend já parseia browser_task_* e workflow_* direto de lk.agent.events; write-mode foi liberado com gate explícito via confirm_action (`write_confirmed`).
- Arquivos: criar `backend/browser_agent/{mcp_client,runner,state,policies}.py`, `backend/actions_domains/browser.py`, `frontend/app/browser-agent/page.tsx`, `frontend/components/app/browser-agent-view.tsx`; editar `frontend/lib/types/realtime.ts`, `frontend/hooks/useAgentActionEvents.ts`, [backend/prompts.py](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\backend\prompts.py).
- IntegraÃ§Ã£o escolhida: sidecar MCP persistente via `npx @playwright/mcp@latest --port ...`; o backend fala com um client prÃ³prio e expÃµe ao modelo apenas `browser_agent_run/status/cancel`.
- Defaults: `read_only` e `allowed_domains` obrigatÃ³rios por execuÃ§Ã£o; aÃ§Ãµes de clique/tipo/upload fora de leitura exigem `require_confirmation`; tarefas ficam persistidas em SQLite e emitem progresso estruturado.
- Pode quebrar: loops longos, navegaÃ§Ã£o fora do domÃ­nio, vazamento de sessÃ£o/logins, upload indevido.
- Validar: 3 smoke tests isolados: leitura de pÃ¡gina com resumo, captura de snapshot/screenshot, preenchimento confirmado em site de teste allowlisted.
- Complexidade: Alta.

### F2.2. WhatsApp bidirecional completo usando `whatsapp-mcp`, mantendo rollback para o legado
Status atual: SQLite ganhou tabela channel_messages; inbox legacy sincroniza para store no backend; leitura via bridge MCP (SQLite de mensagens) já entra no mesmo journal quando configurada; envio de texto agora tenta MCP primeiro e cai para Cloud API legado automaticamente; outbound whatsapp_send_text/audio_tts continua gerando journal persistido; whatsapp_channel_status expõe totais/últimos timestamps + saúde MCP (conectividade e disponibilidade de histórico), mantendo fallback legacy_v1.
- Arquivos: criar `backend/integrations/whatsapp_mcp_client.py`, `backend/channels/whatsapp_adapter.py`, `backend/actions_domains/whatsapp_channel.py`, `frontend/app/integrations/whatsapp/page.tsx`, `frontend/components/app/whatsapp-channel-view.tsx`; editar [frontend/app/api/whatsapp/webhook/route.ts](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\frontend\app\api\whatsapp\webhook\route.ts), [backend/actions.py](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\backend\actions.py), prompts e tipos.
- MigraÃ§Ã£o: primeiro vendorizar a referÃªncia faltante em `references/whatsapp-mcp`; depois rodar o bridge pessoal via QR; depois espelhar mensagens no backend em tabela `channel_messages`; depois ativar resposta bidirecional pelo adapter; sÃ³ no fim trocar o default inbound do webhook JSON para o adapter MCP.
- Compatibilidade: manter `whatsapp_get_recent_messages`, `whatsapp_send_text` e `whatsapp_send_audio_tts` funcionando durante todo o ciclo; o webhook Cloud vira fallback `whatsapp_legacy_v1`.
- Pode quebrar: mensagens duplicadas, reply loop com o prÃ³prio Jarvez, mÃ­dias nÃ£o indexadas, estado perdido apÃ³s restart.
- Validar: QR pair, receber texto, responder texto, responder Ã¡udio, restart com histÃ³rico intacto, bloqueio para contato nÃ£o pareado.
- Complexidade: Alta.

### F2.3. Loop de contexto proativo de verdade
- Arquivos: criar `backend/automation/{rules,scheduler,triggers,executor}.py`; editar `backend/actions_domains/research.py`, `backend/actions_domains/ac.py`, `backend/actions_domains/ops.py`, [backend/agent.py](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\backend\agent.py), `backend/session_snapshot.py`.
- Inputs do primeiro ciclo: `save_web_briefing_schedule` jÃ¡ existente; `ac_configure_arrival_prefs` jÃ¡ existente; presenÃ§a via Home Assistant como padrÃ£o quando `JARVEZ_PRESENCE_ENTITY_ID` estiver configurado; se nÃ£o estiver, arrival automation fica desativada.
- Comportamento: scheduler backend dispara briefing diÃ¡rio; trigger de presenÃ§a aciona `ac_prepare_arrival` primeiro em `dry_run`, depois em live somente se polÃ­tica permitir; todas as execuÃ§Ãµes geram evidence e trace.
- Observabilidade: adicionar `automation_status` e `automation_run_now`; renderizar estado no Trust Center, sem inflar a tela principal.
- Pode quebrar: automaÃ§Ã£o invasiva, horÃ¡rios duplicados, arrival falso-positivo.
- Validar: simulaÃ§Ã£o de agenda diÃ¡ria, simulaÃ§Ã£o de chegada via evento HA, verificaÃ§Ã£o de cooldown e evidence.
- Complexidade: Alta.

### F2.4. Fluxo â€œtenho uma ideiaâ€ â†’ planejamento â†’ implementaÃ§Ã£o automÃ¡tica no projeto certo
- Status atual: `backend/workflows/{types,engine,state}.py` + `backend/workflows/definitions/idea_to_code.py` + `backend/actions_domains/workflows.py` ativos; `actions.py` ja registra `workflow_run/status/cancel/approve/resume` e roteia para engine persistida com gates.
- Arquivos: criar `backend/workflows/{types,engine,state}.py`, `backend/workflows/definitions/idea_to_code.py`, `backend/actions_domains/workflows.py`; editar [backend/codex_cli.py](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\backend\codex_cli.py), `backend/actions_domains/{projects,codex,code_actions,orchestration}.py`, [backend/prompts.py](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\backend\prompts.py), `frontend/lib/types/realtime.ts`, `frontend/hooks/useAgentActionEvents.ts`.
- Workflow fechado: `project_catalog.resolve` â†’ `build_task_plan` â†’ `codex_exec_review` em `read-only` â†’ proposta estruturada de mudanÃ§a â†’ checkpoint de confirmaÃ§Ã£o â†’ `codex exec --sandbox workspace-write` para aplicar ou, se o diff vier estruturado, `code_apply_patch` como fallback controlado â†’ `code_run_command` para validaÃ§Ã£o â†’ opcional `git_commit_and_push_project` em checkpoint separado.
- InspiraÃ§Ã£o adotada de `references/lobster`: steps tipados, estado persistido, approval gates duros e retomada; nÃ£o adotar YAML runner ainda, sÃ³ engine Python mÃ­nima para um workflow.
- Pode quebrar: escolha errada de projeto, escrita sem validaÃ§Ã£o, commit prematuro, fluxo sem retomada.
- Validar: 3 cenÃ¡rios manuais: ideia com um Ãºnico projeto claro, ideia com ambiguidade de projeto, ideia que gera falha de validaÃ§Ã£o e entra em rollback sem commit.
- Complexidade: Alta.

## DependÃªncias Entre as Frentes

- F1.1 Ã© prÃ©-requisito de todo o resto.
- F1.2 precisa entrar antes da quebra por domÃ­nio e antes de qualquer integraÃ§Ã£o nova.
- F1.4 Ã© prÃ©-requisito de F2.2, F2.3 e F2.4, porque WhatsApp, automaÃ§Ãµes e workflows precisam sobreviver a restart.
- F1.5 e F2.0 andam juntos: o model gateway unifica decisÃ£o de modelo; o channel/gateway substrate unifica entrada/saÃ­da.
- F2.1 pode comeÃ§ar depois de F2.0, mesmo antes do WhatsApp.
- F2.2 depende de F2.0 e do vendor da referÃªncia `whatsapp-mcp`.
- F2.3 depende de F1.4 e usa `save_web_briefing_schedule` e `ac_configure_arrival_prefs` jÃ¡ persistidos.
- F2.4 depende de F1.4, F1.5 e do split de `projects/codex/code_actions`.

## Ordem Recomendada de ExecuÃ§Ã£o

1. F1.1 testes e caracterizaÃ§Ã£o.
2. F1.2 nÃºcleo estÃ¡vel de actions.
3. F1.3 quebra por domÃ­nio atÃ© `projects/code_actions/codex/orchestration`.
4. F1.4 SQLite + `session_snapshot`.
5. F1.5 model gateway da voz.
6. F2.0 substrate de canais.
7. F2.1 browser agent.
8. F2.2 WhatsApp bidirecional.
9. F2.3 loop proativo.
10. F2.4 workflow â€œideia â†’ cÃ³digoâ€.

## Riscos e MitigaÃ§Ãµes

- `backend/actions.py` parar no meio do refactor: mitigar com faÃ§ade compatÃ­vel e migraÃ§Ã£o por blocos completos, nunca por helpers soltos.
- SQLite em Windows/OneDrive: mitigar com um Ãºnico writer Python, WAL, `busy_timeout`, sem gravador Node concorrente neste ciclo.
- DivergÃªncia backend/UI ao remover `localStorage` como fonte de verdade: mitigar com `session_snapshot` e fallback de leitura local atÃ© o fim do rollout.
- Browser agent se tornar tool-spam: mitigar expondo sÃ³ aÃ§Ãµes de alto nÃ­vel ao modelo e deixando o loop MCP interno ao backend.
- WhatsApp quebrar o que jÃ¡ funciona: mitigar com `whatsapp_legacy_v1` atÃ© haver paridade real.
- â€œIdeia â†’ cÃ³digoâ€ escrever demais cedo demais: mitigar com dois checkpoints distintos, um para aplicar e outro para commit/push.

## Testes e CenÃ¡rios de Aceite

- Core: auth, confirmation, envelope, policy deny/require_confirmation, workspace boundary, codex task lifecycle, subagent lifecycle, control loop tick.
- PersistÃªncia: restart do backend preserva persona, projeto ativo, coding mode, codex history, schedules e traces; token expirado nÃ£o revive aÃ§Ã£o indevida.
- Frontend: `useAgentActionEvents` hidrata corretamente `session_snapshot`, continua aceitando eventos antigos e nÃ£o depende de `localStorage` para render inicial.
- Browser: leitura allowlisted, navegaÃ§Ã£o com prova, tentativa fora do allowlist bloqueada, interaÃ§Ã£o write-mode exige confirmaÃ§Ã£o.
- WhatsApp: QR pair, inbound texto, outbound texto, outbound Ã¡udio, restart com histÃ³rico, contato nÃ£o pareado bloqueado.
- Proativo: briefing diÃ¡rio dispara uma vez por janela; arrival dry-run produz evidence; live-run sÃ³ passa quando policy/trust permitem.
- Workflow: resolve projeto correto, pausa para aprovaÃ§Ã£o, valida antes de finalizar, nÃ£o faz commit sem checkpoint separado.

## Assumptions e Defaults Escolhidos

- Este plano substitui o conteÃºdo de `docs/next-cycle-plan.md`; ao sair do Plan Mode, a implementaÃ§Ã£o deve materializar exatamente este spec nesse arquivo.
- `references/whatsapp-mcp` estÃ¡ ausente no checkout atual; usar o upstream atÃ© vendorizar a pasta antes da implementaÃ§Ã£o: <https://github.com/lharries/whatsapp-mcp>.
- ReferÃªncias consultadas para o spec: [Playwright MCP local](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\references\playwright-mcp\README.md), <https://github.com/microsoft/playwright-mcp>, [Lobster local](c:\Users\guilh\OneDrive\Ãrea de Trabalho\Jarvez2.0\references\lobster\README.md>.
- O backend Python serÃ¡ o Ãºnico escritor do SQLite neste ciclo; `localStorage` fica sÃ³ como cache/fallback para nÃ£o introduzir lock cross-runtime em Windows.
- Google continua como Ãºnico adapter realtime de voz no ciclo; a unificaÃ§Ã£o pedida Ã© de camada de decisÃ£o, nÃ£o de paridade imediata entre providers de Ã¡udio.
- Browser agent nasce em modo `read_only` por padrÃ£o; qualquer interaÃ§Ã£o que altere estado externo sobe para confirmaÃ§Ã£o explÃ­cita.
- Workflow â€œideia â†’ cÃ³digoâ€ usa `codex exec` em `read-only` para planejar e `workspace-write` somente apÃ³s checkpoint explÃ­cito; commit/push Ã© sempre um segundo checkpoint.











