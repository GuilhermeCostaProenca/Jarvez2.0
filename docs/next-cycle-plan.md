# Jarvez2.0 — Plano Unificado

## Como usar
- Marque `[x]` quando concluido
- Use `[-]` para em andamento
- Use `[ ]` para pendente
- Atualize a linha `Notas:` com contexto curto, branch, PR ou decisao

---

## Parte 1 — Ciclo anterior (hardening do core)

## Checklist Mestre

- [x] F1.1. Caracterizacao e rede de seguranca antes de mover codigo
  Notas: `test_actions.py` foi particionado em suites menores e entraram testes dedicados para eventos, snapshot, router e store. A base de seguranca melhorou, mas o ambiente atual ainda nao tem `pytest` instalado para rodar tudo daqui.

- [x] F1.2. Extrair o nucleo estavel do sistema de actions
  Notas: `backend/actions_core/` ja existe com `types.py`, `registry.py`, `state.py`, `store.py`, `events.py` e `dispatch.py`. `backend/actions.py` segue como facade compativel.

- [x] F1.3. Quebra por dominio em ordem segura
  Notas: handlers ja migrados para `backend/actions_domains/` em `session.py`, `research.py`, `whatsapp.py`, `spotify.py`, `onenote.py`, `home_assistant.py`, `thinq.py`, `ac.py`, `projects.py`, `code_actions.py`, `codex.py`, `orchestration.py`, `policy.py`, `ops.py`, `rpg.py` e `workflows.py`.

- [x] F1.4. Persistencia simples em SQLite com dual-write e leitura gradual
  Notas: `store.py` e dual-write/read-prefer-SQLite estao ativos. `session_snapshot` ja e publicado no start, pos-action e reconnect, e o frontend ja hidrata via backend.

- [x] F1.5. Unificar voice runtime e multi-model router sob uma camada de decisao
  Notas: `backend/runtime/model_gateway.py` e `backend/runtime/realtime_adapters.py` ja entraram. Voz e orchestration/subagents passam pela camada de decisao; Google segue como adapter realtime atual.

- [x] F2.0. Substrato minimo de gateway/canais antes das integracoes novas
  Notas: `backend/channels/types.py`, `router.py`, `audit.py` e `livekit_adapter.py` ja estao integrados. LiveKit usa o adapter sem mudar a UX principal.

- [x] F2.1. Browser agent com Playwright MCP
  Notas: `browser_agent_run/status/cancel` ja emitem `started/progress/completed/failed`, ha allowlist obrigatoria, evidencia estruturada, parse no frontend e gate explicito para write-mode.

- [x] F2.2. WhatsApp bidirecional completo usando `whatsapp-mcp`, com rollback legado
  Notas: a referencia foi vendorizada em `references/whatsapp-mcp`, existe cliente/backend de integracao, journal persistido e fallback para Cloud API legado. Validar pareamento QR e fluxo completo ainda continua importante em ambiente real.

- [ ] F2.3. Loop de contexto proativo de verdade
  Notas: o substrato de automacao existe e ha partes de scheduler/trigger no backend, mas este item ainda precisa fechamento operacional, regras finais, status visivel e validacao ponta a ponta.

- [x] F2.4. Fluxo "tenho uma ideia" -> planejamento -> implementacao automatica
  Notas: `backend/workflows/` e `backend/actions_domains/workflows.py` ja existem, com `workflow_run/status/cancel/approve/resume`, persistencia e approval gates.

## Subitens por frente

### F1.1

- [x] Dividir `backend/test_actions.py` em suites menores sem mudar assertions
  Notas: entraram suites como `backend/test_actions_domains_split.py`, `backend/test_actions_core_events.py`, `backend/test_orchestration_router.py` e correlatas.

- [ ] Adicionar Vitest no frontend para `useAgentActionEvents` e storages criticos
  Notas: ainda nao fechado. O parser de eventos foi endurecido no codigo, mas a camada de teste frontend dedicada ainda precisa ser formalizada.

### F1.2

- [x] Extrair tipos e registry
  Notas: concluido em `backend/actions_core/types.py` e `backend/actions_core/registry.py`.

- [x] Extrair events e state
  Notas: concluido em `backend/actions_core/events.py` e `backend/actions_core/state.py`.

- [x] Extrair dispatch e manter `actions.py` como facade
  Notas: concluido com compatibilidade preservada para os fluxos atuais.

### F1.3

- [x] Migrar dominios de sessao, pesquisa e integracoes
  Notas: concluido.

- [x] Migrar dominios de projetos, code actions, codex e orchestration
  Notas: concluido.

- [x] Migrar policy, ops, rpg e workflows
  Notas: concluido.

### F1.4

- [x] Introduzir tabelas e store SQLite
  Notas: concluido no backend; snapshot e estados operacionais persistem.

- [x] Publicar `session_snapshot`
  Notas: concluido com envio no inicio, pos-action e reconnect.

- [x] Trocar frontend para hidratar do backend e usar `localStorage` como fallback
  Notas: concluido para snapshot e estados principais.

### F1.5

- [x] Criar `RuntimeDecision`/gateway
  Notas: concluido.

- [x] Fazer orchestration respeitar `provider_order` derivado do gateway
  Notas: concluido em `backend/orchestration/router.py` e `backend/providers/provider_router.py`.

- [x] Levar voz para a mesma camada de decisao
  Notas: concluido no escopo do ciclo, mantendo Google como adapter realtime.

### F2.0

- [x] Padronizar envelopes de canal e auditoria
  Notas: concluido.

- [x] Colocar LiveKit em cima do adapter novo
  Notas: concluido.

### F2.1

- [x] Criar client MCP, runner, state e policies do browser agent
  Notas: concluido.

- [x] Expor apenas `browser_agent_run/status/cancel` ao modelo
  Notas: concluido.

- [x] Persistir tarefa e emitir progresso estruturado
  Notas: concluido.

### F2.2

- [x] Vendorizar `references/whatsapp-mcp`
  Notas: concluido, removendo binarios e bancos locais do versionamento.

- [x] Criar cliente/backend de integracao e journal persistido
  Notas: concluido.

- [x] Manter compatibilidade com `whatsapp_legacy_v1`
  Notas: concluido com fallback.

- [ ] Validar fluxo real completo com QR, texto, audio e restart
  Notas: ainda depende de rodada manual em ambiente com conta conectada.

### F2.3

- [ ] Fechar regras de scheduler e triggers
  Notas: falta definicao final e validacao operacional.

- [ ] Expor `automation_status` e `automation_run_now`
  Notas: revisar o que ja existe no backend e fechar o contrato realtime/UI.

- [ ] Renderizar automacoes no Trust Center sem poluir a sessao principal
  Notas: pendente.

- [ ] Validar cooldown, evidence e protecoes de policy
  Notas: pendente.

### F2.4

- [x] Criar engine de workflow com estado persistido e gates
  Notas: concluido.

- [x] Expor `workflow_run/status/cancel/approve/resume`
  Notas: concluido.

- [x] Integrar com `projects`, `codex`, `code_actions` e `orchestration`
  Notas: concluido no nivel de backend/eventos.

- [ ] Fechar bateria manual dos 3 cenarios de aceite
  Notas: ainda falta validacao operacional completa com projeto ambiguo e rollback de falha.

## Dependencias

- [x] F1.1 antes do restante
  Notas: concluido.

- [x] F1.2 antes do split por dominio
  Notas: concluido.

- [x] F1.4 como base para WhatsApp, automacoes e workflows
  Notas: concluido.

- [x] F1.5 e F2.0 rodando juntos
  Notas: concluido.

- [x] F2.1 depois de F2.0
  Notas: concluido.

- [x] F2.2 dependente do vendor da referencia
  Notas: concluido.

- [ ] F2.3 dependente de F1.4 e ajustes finais de scheduler
  Notas: base pronta, fechamento pendente.

- [x] F2.4 dependente de F1.4, F1.5 e split de dominios
  Notas: concluido.

## Riscos Abertos

- [ ] Automacoes proativas dispararem cedo demais ou em duplicidade
  Notas: precisa fechamento de cooldown, janela e observabilidade.

- [ ] Fluxos operacionais reais ainda sem rodada manual completa
  Notas: principalmente WhatsApp QR/audio/restart e workflow com rollback.

- [ ] `references/skills` segue modificado localmente
  Notas: estado local pre-existente; nao faz parte deste plano, mas convem limpar separadamente.

## Aceite Final do Ciclo

- [ ] Backend com testes executaveis no ambiente atual
  Notas: `compileall` passou, mas `pytest` nao esta instalado neste Python.

- [ ] Frontend com testes direcionados do parser de eventos
  Notas: cobertura dedicada ainda pendente.

- [ ] Automacoes proativas fechadas e visiveis na UI correta
  Notas: pendente.

- [ ] Validacao manual completa de WhatsApp e workflow
  Notas: pendente.

---

## Parte 2 — Migracao MCP

### Visao geral
`backend/actions_domains/` ja separa 17 modulos de dominio, mas `backend/actions.py` ainda concentra o registry das `ActionSpec`, o dispatch com policy/evidence, auth/confirmation, session snapshot, publicacao de eventos e boa parte dos helpers de token/cache/OAuth.
Fora dos dominios modularizados ainda vivem `backend/browser_agent/` com `browser_agent_run/status/cancel`, `backend/automation/` com `automation_status` e `automation_run_now`, a suite de `evals`, CRUD de perfis de voz, `forget_memory`, `coding_mode_*`, `git_commit_and_push_project` e a cola geral da facade.
A migracao MCP desta rodada cobre tudo que pode sair para repos proprios sem tirar do Jarvez o papel de control plane e fonte de verdade do estado: auth, policy, audit, realtime routing, snapshots e hidratacao da UI continuam locais.
A facade ainda faz de verdade a gestao de singletons (`ProjectCatalog`, `CodeWorkerClient`, `GitHubCatalogClient`, `RPGKnowledgeIndex`, `CodeKnowledgeIndex`), persistencia SQLite, validacao/redaction de payload, event/session state e o registro final das actions expostas ao runtime.

### MCPs publicos disponiveis (nao implementar do zero)
- `spotify` -> `marcelmarais/spotify-mcp-server` -> ja esta vendorizado em `references/spotify-mcp-server` e cobre playback, devices e playlists na mesma superficie do dominio atual.
- `whatsapp` -> `lharries/whatsapp-mcp` -> ja esta vendorizado em `references/whatsapp-mcp` e combina com o fallback legado e com o journal local do Jarvez.
- `home_assistant` -> `oleander/home-assistant-mcp-server` -> substitui chamadas REST diretas do Home Assistant por um MCP pronto.
- `onenote` -> `Softeria/ms-365-mcp-server` -> alinha a extracao com Microsoft Graph e as operacoes de notebook/secao/pagina hoje feitas no dominio OneNote.
- `github` -> `github/github-mcp-server` -> cobre descoberta e metadata de repositorios, deixando catalogo e selecao de projeto como glue local.
- `code/filesystem/git` -> `modelcontextprotocol/servers` (`server-filesystem`, `server-git`) -> base publica para a fase de `projects` e `code_actions` sem reimplementar acesso a arquivos e Git.
- `browser` -> `microsoft/playwright-mcp` / `@playwright/mcp` -> ja e a base operacional do browser agent atual; nesta rodada o que resta no Jarvez e glue, policy e persistencia.
- `thinq`, `ac` e `rpg` -> nao houve confirmacao de MCP publico pronto na varredura; esses dominios devem prever repos `jarvez-mcp-*`.

### Fases de extracao

#### Fase A — Separar arquivos mistos e integracoes API puras

##### Dominio: spotify
Contexto tecnico: `backend/actions_domains/spotify.py` ja esta isolado, mas ainda depende de helpers de token/cache e aliases de device que hoje vivem na facade de `backend/actions.py`.
- [x] Criar repo `jarvez-mcp-spotify`
  Notas: repo criado em `../jarvez-mcp-spotify` seguindo a estrutura standalone de `../jarvez-mcp-rpg`, com `server.py`, `core/` e `tools/`.
- [x] Migrar codigo de `backend/actions_domains/spotify.py`
  Notas: handlers `spotify_status/get_devices/transfer_playback/play/pause/next_track/previous_track/set_volume/create_surprise_playlist` foram portados para `../jarvez-mcp-spotify/tools/spotify.py`, e os helpers de token/cache/device alias sairam para `../jarvez-mcp-spotify/core/spotify_client.py`.
- [x] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas: `../jarvez-mcp-spotify/README.md` documenta instalacao, `claude mcp add --transport stdio`, variaveis de ambiente e o papel do repo na extracao do Jarvez.
- [x] Criar CHANGELOG.md com v0.1.0
  Notas: `../jarvez-mcp-spotify/CHANGELOG.md` criado com a entrada `v0.1.0 - 2026-03-17`.
- [x] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-spotify com tag v0.1.0
  Notas: repo publicado em `https://github.com/GuilhermeCostaProenca/jarvez-mcp-spotify`, branch `main` enviada e tag `v0.1.0` criada em `2026-03-17`.
- [x] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas: `backend/actions.py` agora sinaliza os wrappers e o registro `spotify_*` como compatibilidade temporaria durante a migracao para `../jarvez-mcp-spotify`.
- [x] Registrar em AGENTS.md como repositorio de referencia
  Notas: `AGENTS.md` ganhou a entrada `jarvez-mcp-spotify` na tabela de repositorios de referencia.

##### Dominio: home-assistant
Contexto tecnico: `backend/actions_domains/home_assistant.py` esta misturado com `open_desktop_resource`, `run_local_command` e `git_clone_repository`; nesta fase migram so `call_service`, `turn_light_on`, `turn_light_off` e `set_light_brightness`.
- [x] Criar repo `jarvez-mcp-home-assistant`
  Notas: repo criado em `../jarvez-mcp-home-assistant` seguindo a estrutura standalone de `../jarvez-mcp-rpg` e `../jarvez-mcp-spotify`, com `server.py`, `core/` e `tools/`.
- [x] Migrar codigo de `backend/actions_domains/home_assistant.py`
  Notas: foram portados apenas `call_service`, `turn_light_on`, `turn_light_off` e `set_light_brightness` para `../jarvez-mcp-home-assistant/tools/home_assistant.py`; `open_desktop_resource`, `run_local_command` e `git_clone_repository` ficaram no Jarvez para a futura extracao `desktop`.
- [x] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas: `../jarvez-mcp-home-assistant/README.md` documenta instalacao, `claude mcp add --transport stdio`, variaveis de ambiente e o recorte exato do dominio.
- [x] Criar CHANGELOG.md com v0.1.0
  Notas: `../jarvez-mcp-home-assistant/CHANGELOG.md` criado com a entrada `v0.1.0 - 2026-03-17`.
- [x] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-home-assistant com tag v0.1.0
  Notas: repo publicado em `https://github.com/GuilhermeCostaProenca/jarvez-mcp-home-assistant`, branch `main` enviada e tag `v0.1.0` criada em `2026-03-17`.
- [x] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas: `backend/actions.py` agora marca `turn_light_on`, `turn_light_off`, `set_light_brightness` e `call_service` como compatibilidade temporaria enquanto o Jarvez ainda nao aponta para `jarvez-mcp-home-assistant`.
- [x] Registrar em AGENTS.md como repositorio de referencia
  Notas: `AGENTS.md` ganhou a entrada `jarvez-mcp-home-assistant` na tabela de repositorios de referencia.

##### Dominio: thinq
Contexto tecnico: `backend/actions_domains/thinq.py` esta isolado, mas continua dependente de credenciais e helpers ThinQ na facade; nao houve MCP publico confirmado para este dominio.
- [x] Criar repo `jarvez-mcp-thinq`
  Notas: repo criado em `../jarvez-mcp-thinq` seguindo a estrutura standalone de `../jarvez-mcp-rpg`, `../jarvez-mcp-spotify` e `../jarvez-mcp-home-assistant`, com `server.py`, `core/` e `tools/`.
- [x] Migrar codigo de `backend/actions_domains/thinq.py`
  Notas: handlers `thinq_status/list_devices/get_device_profile/get_device_state/control_device` foram portados para `../jarvez-mcp-thinq/tools/thinq.py`; o repo novo tambem recebeu o nucleo de auth, headers e descoberta de device em `../jarvez-mcp-thinq/core/thinq_client.py`.
- [x] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas: `../jarvez-mcp-thinq/README.md` documenta instalacao, `claude mcp add --transport stdio`, variaveis de ambiente e a fronteira atual entre `thinq_*` e `ac_*`.
- [x] Criar CHANGELOG.md com v0.1.0
  Notas: `../jarvez-mcp-thinq/CHANGELOG.md` criado com a entrada `v0.1.0 - 2026-03-17`.
- [x] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-thinq com tag v0.1.0
  Notas: repo publicado em `https://github.com/GuilhermeCostaProenca/jarvez-mcp-thinq`, branch `main` enviada e tag `v0.1.0` criada em `2026-03-17`.
- [x] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas: `backend/actions.py` agora marca `thinq_status`, `thinq_list_devices`, `thinq_get_device_profile`, `thinq_get_device_state` e `thinq_control_device` como compatibilidade temporaria; os helpers locais continuam por enquanto porque `ac_*` ainda depende deles.
- [x] Registrar em AGENTS.md como repositorio de referencia
  Notas: `AGENTS.md` ganhou a entrada `jarvez-mcp-thinq` na tabela de repositorios de referencia.

#### Fase B — Integracoes com estado local e callbacks

##### Dominio: whatsapp
Contexto tecnico: a extracao precisa considerar `backend/actions_domains/whatsapp.py`, `backend/actions_domains/whatsapp_channel.py` e `backend/integrations/whatsapp_mcp_client.py`, preservando fallback `whatsapp_legacy_v1` e o journal persistido em `channel_messages` como glue do Jarvez.
- [x] Criar repo `jarvez-mcp-whatsapp`
  Notas: repo criado em `../jarvez-mcp-whatsapp` seguindo a estrutura standalone de `../jarvez-mcp-onenote` e `../jarvez-mcp-thinq`, com `server.py`, `core/`, `tools/` e `data/`.
- [x] Migrar codigo de `backend/actions_domains/whatsapp.py`
  Notas: o recorte `whatsapp_channel_status/list_chats/whatsapp_send_text/send_message` foi portado para `../jarvez-mcp-whatsapp/tools/whatsapp.py`, e os helpers de conectividade com o bridge HTTP e leitura do SQLite local sairam para `../jarvez-mcp-whatsapp/core/whatsapp_client.py`; journal persistido, fallback `whatsapp_legacy_v1` e channel state ficaram no Jarvez.
- [x] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas: `../jarvez-mcp-whatsapp/README.md` documenta instalacao, variaveis de ambiente, execucao standalone, `claude mcp add --transport stdio` e a fronteira entre o repo novo e o control plane do Jarvez.
- [x] Criar CHANGELOG.md com v0.1.0
  Notas: `../jarvez-mcp-whatsapp/CHANGELOG.md` criado com a entrada `v0.1.0 - 2026-03-17`.
- [x] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-whatsapp com tag v0.1.0
  Notas: repo publicado em `https://github.com/GuilhermeCostaProenca/jarvez-mcp-whatsapp`, branch `main` enviada, tag `v0.1.0` criada em `2026-03-17` e HEAD local em `84ecf74dccfc3d462c1cfd81ae2673d2828786bd`.
- [x] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas: `backend/actions.py` agora marca `whatsapp_channel_status` e `whatsapp_send_text` como compatibilidade temporaria enquanto o Jarvez preserva localmente journal, fallback e channel state.
- [x] Registrar em AGENTS.md como repositorio de referencia
  Notas: `AGENTS.md` ganhou a entrada `jarvez-mcp-whatsapp` na tabela de repositorios de referencia.

##### Dominio: onenote
Contexto tecnico: `backend/actions_domains/onenote.py` ja esta isolado, mas os helpers de OAuth, token persistence e chamadas Graph ainda estao na facade de `backend/actions.py`.
- [x] Criar repo `jarvez-mcp-onenote`
  Notas: repo criado em `../jarvez-mcp-onenote` seguindo a estrutura standalone de `../jarvez-mcp-spotify`, `../jarvez-mcp-home-assistant`, `../jarvez-mcp-thinq` e `../jarvez-mcp-rpg`, com `server.py`, `core/`, `tools/` e `data/`.
- [x] Migrar codigo de `backend/actions_domains/onenote.py`
  Notas: a superficie `onenote_status/list_notebooks/list_sections/list_pages/search_pages/get_page_content/create_character_page/append_to_page` foi portada para `../jarvez-mcp-onenote/tools/onenote.py`, e os helpers de OAuth, token persistence, preview HTML e chamadas Graph sairam para `../jarvez-mcp-onenote/core/onenote_client.py`.
- [x] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas: `../jarvez-mcp-onenote/README.md` documenta instalacao, variaveis de ambiente, execucao standalone, `claude mcp add --transport stdio` e a integracao futura com o Jarvez.
- [x] Criar CHANGELOG.md com v0.1.0
  Notas: `../jarvez-mcp-onenote/CHANGELOG.md` criado com a entrada `v0.1.0 - 2026-03-17`.
- [x] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-onenote com tag v0.1.0
  Notas: repo publicado em `https://github.com/GuilhermeCostaProenca/jarvez-mcp-onenote`, branch `main` enviada, tag `v0.1.0` criada em `2026-03-17` e HEAD local em `bbf89e728b6e961c1f4100a850840869f0fbadb1`.
- [x] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas: `backend/actions.py` agora marca a superficie `onenote_*` como compatibilidade temporaria ate o Jarvez apontar para `jarvez-mcp-onenote`.
- [x] Registrar em AGENTS.md como repositorio de referencia
  Notas: `AGENTS.md` ganhou a entrada `jarvez-mcp-onenote` na tabela de repositorios de referencia.

##### Dominio: ac
Contexto tecnico: `backend/actions_domains/ac.py` depende do dominio ThinQ e das preferencias/automacoes locais de chegada; so entra depois de `jarvez-mcp-thinq` estar definido.
- [x] Criar repo `jarvez-mcp-ac`
  Notas: repo criado em `../jarvez-mcp-ac` seguindo a estrutura standalone de `../jarvez-mcp-thinq` e `../jarvez-mcp-spotify`, com `server.py`, `core/` e `tools/`.
- [x] Migrar codigo de `backend/actions_domains/ac.py`
  Notas: o recorte `ac_get_status/ac_turn_on/ac_turn_off/ac_set_mode/ac_set_temperature` foi portado para `../jarvez-mcp-ac/tools/ac.py`, com helpers ThinQ alinhados em `../jarvez-mcp-ac/core/ac_client.py`; `ac_configure_arrival_prefs`, `ac_prepare_arrival`, policy e automacoes continuam locais no Jarvez.
- [x] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas: `../jarvez-mcp-ac/README.md` documenta instalacao, variaveis de ambiente, execucao standalone, `claude mcp add --transport stdio`, dependencia funcional de `jarvez-mcp-thinq` e a fronteira com o Jarvez.
- [x] Criar CHANGELOG.md com v0.1.0
  Notas: `../jarvez-mcp-ac/CHANGELOG.md` criado com a entrada `v0.1.0 - 2026-03-17`.
- [x] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-ac com tag v0.1.0
  Notas: repo publicado em `https://github.com/GuilhermeCostaProenca/jarvez-mcp-ac`, branch `main` enviada, tag `v0.1.0` criada em `2026-03-17` e HEAD local em `156ec7b50795f97f9976a7a9249ebb3517aacdb0`.
- [x] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas: `backend/actions.py` agora marca `ac_get_status`, `ac_turn_on`, `ac_turn_off`, `ac_set_mode` e `ac_set_temperature` como compatibilidade temporaria enquanto o Jarvez preserva localmente preferencias de chegada e automacoes.
- [x] Registrar em AGENTS.md como repositorio de referencia
  Notas: `AGENTS.md` ganhou a entrada `jarvez-mcp-ac` na tabela de repositorios de referencia.

#### Fase C — Superficie de engenharia local

##### Dominio: github
Contexto tecnico: `github_*` hoje esta misturado em `backend/actions_domains/projects.py`; antes de publicar `jarvez-mcp-github`, e preciso separar busca/metadata GitHub do catalogo e da selecao de projeto local.
- [x] Criar repo `jarvez-mcp-github`
  Notas: repo criado em `../jarvez-mcp-github` seguindo a estrutura standalone de `../jarvez-mcp-spotify` e `../jarvez-mcp-thinq`, com `server.py`, `core/` e `tools/`.
- [x] Migrar codigo de `backend/actions_domains/projects.py`
  Notas: foram portados apenas `github_list_repos` e `github_find_repo` para `../jarvez-mcp-github/tools/github.py`; `github_clone_and_register`, catalogo local, projeto ativo e selecao continuam no Jarvez.
- [x] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas: `../jarvez-mcp-github/README.md` documenta instalacao, `claude mcp add --transport stdio`, variaveis de ambiente e a fronteira exata entre metadata GitHub e glue local do Jarvez.
- [x] Criar CHANGELOG.md com v0.1.0
  Notas: `../jarvez-mcp-github/CHANGELOG.md` criado com a entrada `v0.1.0 - 2026-03-17`.
- [x] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-github com tag v0.1.0
  Notas: repo publicado em `https://github.com/GuilhermeCostaProenca/jarvez-mcp-github`, branch `main` enviada, tag `v0.1.0` criada e HEAD local em `a42d65097c3035de7ccfa46e39a20c7f8d8f1102`.
- [x] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas: `backend/actions.py` e `backend/actions_domains/projects.py` agora marcam `github_list_repos` e `github_find_repo` como compatibilidade temporaria; `github_clone_and_register` segue local porque mistura clone, catalogo e selecao.
- [x] Registrar em AGENTS.md como repositorio de referencia
  Notas: `AGENTS.md` ganhou a entrada `jarvez-mcp-github` na tabela de repositorios de referencia.

##### Dominio: projects
Contexto tecnico: `backend/actions_domains/projects.py` depende de `ProjectCatalog`, de projeto ativo em sessao, de indexacao local e do glue de `git_clone_repository`; a extracao precisa manter o Jarvez como fonte de verdade do catalogo e do projeto selecionado.
- [x] Criar repo `jarvez-mcp-projects`
  Notas: repo criado em `../jarvez-mcp-projects` seguindo a estrutura standalone de `../jarvez-mcp-github` e `../jarvez-mcp-spotify`, com `server.py`, `core/` e `tools/`.
- [x] Migrar codigo de `backend/actions_domains/projects.py`
  Notas: o recorte extraido cobre metadata pura em `../jarvez-mcp-projects/tools/projects.py` com `project_list`, `project_open`, `project_create` e `project_update`; `ProjectCatalog`, projeto ativo em sessao, indexacao local, `project_scan`, `project_refresh_index`, `project_search` e clone local continuam no Jarvez.
- [x] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas: `../jarvez-mcp-projects/README.md` documenta instalacao, `claude mcp add --transport stdio`, variaveis de ambiente e a fronteira exata entre metadata de projeto e glue local do Jarvez.
- [x] Criar CHANGELOG.md com v0.1.0
  Notas: `../jarvez-mcp-projects/CHANGELOG.md` criado com a entrada `v0.1.0 - 2026-03-17`.
- [x] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-projects com tag v0.1.0
  Notas: repo publicado em `https://github.com/GuilhermeCostaProenca/jarvez-mcp-projects`, branch `main` enviada, tag `v0.1.0` criada e HEAD local em `ecf3f812d39fc37971983b0b46c9cd2201ea31f2`.
- [x] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas: `backend/actions.py` e `backend/actions_domains/projects.py` agora marcam `project_list` e `project_update` como compatibilidade temporaria; selecao de projeto, projeto ativo e indexacao seguem locais.
- [x] Registrar em AGENTS.md como repositorio de referencia
  Notas: `AGENTS.md` ganhou a entrada `jarvez-mcp-projects` na tabela de repositorios de referencia.

##### Dominio: code-actions
Contexto tecnico: `backend/actions_domains/code_actions.py` depende de `backend/code_worker.py`, `backend/code_knowledge.py` e do estado de projeto ativo mantido pela facade e pelo catalogo local.
- [ ] Criar repo `jarvez-mcp-code-actions`
  Notas:
- [ ] Migrar codigo de `backend/actions_domains/code_actions.py`
  Notas:
- [ ] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas:
- [ ] Criar CHANGELOG.md com v0.1.0
  Notas:
- [ ] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-code-actions com tag v0.1.0
  Notas:
- [ ] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas:
- [ ] Registrar em AGENTS.md como repositorio de referencia
  Notas:

##### Dominio: codex
Contexto tecnico: `backend/actions_domains/codex.py` depende do estado de task/historico/progresso que ainda mora em `actions.py`, alem de emissao de eventos e controle de processos em memoria.
- [x] Criar repo `jarvez-mcp-codex`
  Notas: repo criado em `../jarvez-mcp-codex` seguindo a estrutura standalone de `../jarvez-mcp-spotify` e `../jarvez-mcp-thinq`, com `server.py`, `core/` e `tools/`.
- [x] Migrar codigo de `backend/actions_domains/codex.py`
  Notas: o recorte extraido cobre `codex_exec_task`, `codex_exec_review`, `codex_exec_status`, `codex_cancel_task` e `codex_list_tasks` em `../jarvez-mcp-codex/tools/codex.py`; historico em sessao, eventos realtime e controle de processo por participante continuam no Jarvez.
- [x] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas: `../jarvez-mcp-codex/README.md` documenta instalacao, `claude mcp add --transport stdio`, variaveis de ambiente e a fronteira exata entre task surface e glue local do Jarvez.
- [x] Criar CHANGELOG.md com v0.1.0
  Notas: `../jarvez-mcp-codex/CHANGELOG.md` criado com a entrada `v0.1.0 - 2026-03-17`.
- [x] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-codex com tag v0.1.0
  Notas: repo publicado em `https://github.com/GuilhermeCostaProenca/jarvez-mcp-codex`, branch `main` enviada, tag `v0.1.0` criada e HEAD local em `74e5030bf772869a2cfdd0ed204ce55fff7bd2fc`.
- [x] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas: `backend/actions.py` e `backend/actions_domains/codex.py` agora marcam `codex_exec_task`, `codex_exec_review`, `codex_exec_status` e `codex_cancel_task` como compatibilidade temporaria; historico, eventos e controle por participante seguem locais.
- [x] Registrar em AGENTS.md como repositorio de referencia
  Notas: `AGENTS.md` ganhou a entrada `jarvez-mcp-codex` na tabela de repositorios de referencia.

##### Dominio: desktop
Contexto tecnico: `open_desktop_resource` e `run_local_command` nascem dos helpers nao-HA hoje misturados em `backend/actions_domains/home_assistant.py`; esta extracao deve separar desktop/local shell do dominio de casa.
- [ ] Criar repo `jarvez-mcp-desktop`
  Notas:
- [ ] Migrar codigo de `backend/actions_domains/home_assistant.py`
  Notas:
- [ ] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas:
- [ ] Criar CHANGELOG.md com v0.1.0
  Notas:
- [ ] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-desktop com tag v0.1.0
  Notas:
- [ ] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas:
- [ ] Registrar em AGENTS.md como repositorio de referencia
  Notas:

#### Fase D — Conhecimento e workflows de app

##### Dominio: research
Contexto tecnico: `backend/actions_domains/research.py` pode virar MCP, mas o dashboard, agendamento e reabertura em rota dedicada continuam como glue do Jarvez ate a UX estabilizar.
- [ ] Criar repo `jarvez-mcp-research`
  Notas:
- [ ] Migrar codigo de `backend/actions_domains/research.py`
  Notas:
- [ ] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas:
- [ ] Criar CHANGELOG.md com v0.1.0
  Notas:
- [ ] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-research com tag v0.1.0
  Notas:
- [ ] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas:
- [ ] Registrar em AGENTS.md como repositorio de referencia
  Notas:

##### Dominio: rpg
Contexto tecnico: `backend/actions_domains/rpg.py` depende de `backend/rpg_knowledge.py`, `references/gerador-ficha-tormenta20`, `references/artonMap`, PDFs/SQLite locais, arquivos de sessao e backlinks com OneNote; nao houve MCP publico confirmado para este stack.
- [x] Criar repo `jarvez-mcp-rpg`
  Notas: repo criado em `../jarvez-mcp-rpg` como MCP standalone do dominio RPG, com `server.py`, `core/`, `tools/`, `rpg_engine/` e assets vendorizados necessarios.
- [x] Migrar codigo de `backend/actions_domains/rpg.py`
  Notas: a superficie `rpg_*` foi extraida para `../jarvez-mcp-rpg`, preservando knowledge index, sessoes, fichas e integracao com os assets locais do dominio.
- [x] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas: `../jarvez-mcp-rpg/README.md` documenta instalacao, `claude mcp add --transport stdio`, variaveis de ambiente e a estrategia de integracao futura com o Jarvez.
- [x] Criar CHANGELOG.md com v0.1.0
  Notas: `../jarvez-mcp-rpg/CHANGELOG.md` existe e acompanha a publicacao inicial `v0.1.0`.
- [x] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-rpg com tag v0.1.0
  Notas: repo publicado em `https://github.com/GuilhermeCostaProenca/jarvez-mcp-rpg`, branch `main` ativa, tag `v0.1.0` existente e HEAD local em `462dfb668fe60bdf2accb07cea0ef7d4b454f9e7`.
- [x] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas: `backend/actions.py` ja marca a superficie `rpg_*` como migrada para `github.com/GuilhermeCostaProenca/jarvez-mcp-rpg`, mantendo compatibilidade temporaria no monolito.
- [x] Registrar em AGENTS.md como repositorio de referencia
  Notas: `AGENTS.md` ja lista `jarvez-mcp-rpg` na tabela de repositorios de referencia.

##### Dominio: workflows
Contexto tecnico: a extracao inclui `backend/actions_domains/workflows.py` e `backend/workflows/`, mas approval gates, session snapshot e integracao com projeto/codex continuam no backend do Jarvez.
- [ ] Criar repo `jarvez-mcp-workflows`
  Notas:
- [ ] Migrar codigo de `backend/actions_domains/workflows.py`
  Notas:
- [ ] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas:
- [ ] Criar CHANGELOG.md com v0.1.0
  Notas:
- [ ] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-workflows com tag v0.1.0
  Notas:
- [ ] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas:
- [ ] Registrar em AGENTS.md como repositorio de referencia
  Notas:

#### Fase E — Integracao MCP no Jarvez
- [x] E1. Criar o substrato `backend/mcp/` com `registry.py`, `manager.py` e `client.py`
  Notas: concluido com `backend/mcp/{types,registry,client,manager}.py`, bootstrap interno em `backend/backend_mcp.py` e teste dedicado em `backend/test_mcp_substrate.py`.
- [x] E2. Definir manifesto/config dos MCPs habilitados pelo Jarvez
  Notas: concluido com manifesto em `backend/mcp/registry.py`; o backend principal ja registra `spotify`, `onenote`, `home_assistant`, `thinq`, `rpg` e `whatsapp`, todos com `name`, `command`, `args`, `cwd`, `enabled`, `timeout_seconds` e `legacy_fallback_enabled`.
- [x] E3. Implementar boot lifecycle dos MCP servers via subprocess/stdin
  Notas: concluido em `backend/mcp/manager.py` + `backend/mcp/client.py`, subindo `../jarvez-mcp-spotify/server.py` via `sys.executable`, reutilizando cliente ativo e expondo `stop_server`/`shutdown_all`.
- [x] E4. Implementar handshake inicial com descoberta de tools
  Notas: concluido com `ClientSession.initialize()` + `list_tools`; o piloto `spotify` descobriu `spotify_status`, `spotify_get_devices`, `spotify_transfer_playback`, `spotify_play`, `spotify_pause`, `spotify_next_track`, `spotify_previous_track`, `spotify_set_volume` e `spotify_create_surprise_playlist`.
- [x] E5. Implementar `call_tool` com timeout, retries e tratamento uniforme de erro
  Notas: concluido com `call_tool()` em `backend/mcp/client.py`; validado no piloto com `spotify_status`, retornando MCP `status=ok` e payload real `spotify_auth_required` quando nao autenticado.
- [x] E6. Implementar heranca e injecao controlada de env por servidor MCP
  Notas: concluido com `env_allowlist` e `env_overrides` em `backend/mcp/types.py` + `backend/mcp/registry.py`; o piloto `spotify` sobe com env explicitamente filtrado em `backend/mcp/client.py` e redaction de segredos nos logs/status.
- [x] E7. Expor `healthcheck` e `status` dos MCPs ativos
  Notas: concluido em `backend/mcp/manager.py` e `backend/backend_mcp.py`; o backend agora expoe `get_mcp_server_status()`/`get_mcp_status_snapshot()` com processo ativo, ultima descoberta, ultimo sucesso, ultima falha, ultimo erro e tempo de resposta.
- [x] E8. Persistir logs, auditoria e `evidence` das chamadas MCP
  Notas: concluido com a tabela SQLite `mcp_call_audit` em `backend/actions_core/store.py` e registro automatico no manager; chamadas do piloto `spotify` persistem servidor, tool, args redigidos, duracao, resumo do retorno e tipo de erro.
- [x] E9. Implementar fallback explicito para handlers legacy
  Notas: concluido com `call_tool_with_fallback()` em `backend/mcp/manager.py` + wrapper em `backend/backend_mcp.py`; o fallback respeita `legacy_fallback_enabled`, registra o motivo (`tool_error` no teste/manual) e nao altera os handlers legacy existentes.
- [x] E10. Migrar `actions.py` gradualmente para roteamento via MCP
  Notas: concluido para a superficie `spotify_*` e para o recorte inicial read-only de `onenote_*`; `backend/actions.py` agora tenta o MCP `spotify` primeiro em toda a superficie `spotify_*` e tenta o MCP `onenote` primeiro em `onenote_status`, `onenote_list_notebooks` e `onenote_list_sections`, preservando fallback legacy controlado sem remocao de handlers.
- [x] E11. Validar um dominio piloto em integracao real
  Notas: concluido com o piloto `jarvez-mcp-spotify` e com a primeira extensao segura para `jarvez-mcp-onenote`; alem de `dispatch_action("spotify_status")` e do restante do recorte Spotify, o backend principal validou `dispatch_action("onenote_status")` via MCP real, com `evidence.provider="mcp"`, `mcp_server="onenote"` e `fallback_used=false` no cenario manual atual, enquanto o fallback legacy de `onenote_list_notebooks` ficou coberto em teste dedicado.
- [-] E12. Expandir a validacao real para `jarvez-mcp-home-assistant`, `jarvez-mcp-thinq`, `jarvez-mcp-rpg` e recortes dependentes de `ac_*`/`whatsapp_*`
  Notas: iniciado por `jarvez-mcp-home-assistant`, expandido para `jarvez-mcp-thinq`, `jarvez-mcp-rpg`, o recorte inicial de `ac_*` em cima do server MCP `thinq` e agora para um recorte inicial de `whatsapp_*`; `backend/actions.py` tenta o MCP `home_assistant` primeiro em `call_service`, `turn_light_on`, `turn_light_off` e `set_light_brightness`, tenta o MCP `thinq` primeiro em `thinq_status` e `thinq_list_devices`, tenta o MCP `rpg` primeiro em `rpg_get_knowledge_stats` e `rpg_search_knowledge`, tenta o MCP `thinq` tambem em `ac_get_status`, `ac_turn_on` e `ac_turn_off`, e agora usa o MCP `whatsapp` como probe em `whatsapp_channel_status` via `list_chats` e para envio simples em `whatsapp_send_text` via `send_message`, sempre com fallback legacy preservado. Validacoes reais feitas com `dispatch_action("turn_light_on")`, `dispatch_action("thinq_status")`, `dispatch_action("rpg_get_knowledge_stats")`, `dispatch_action("rpg_search_knowledge")`, `dispatch_action("ac_get_status")` e `dispatch_action("whatsapp_channel_status")`; no recorte WhatsApp o backend retornou `provider="mcp"`, `fallback_used=false`, `mcp_server="whatsapp"` e manteve journal, channel state e contadores locais no Jarvez.

#### Fase F — Limpeza final
- [ ] Remover handlers marcados DEPRECATED do `actions.py`
  Notas:
- [ ] Validar que `actions.py` facade esta vazio ou so com glue code
  Notas:
- [ ] Atualizar `docs/jarvez-baseline.md` com nova contagem de actions locais
  Notas:
- [ ] Smoke test completo do Jarvez apos remocao
  Notas:

### Dominios que ficam locais nesta rodada
- `session`, `policy`, `orchestration`, `ops`, `automation`, `browser_agent`, `runtime`, `channels`, `actions_core`
  Notas: control plane do Jarvez; concentram auth, dispatch, policy, audit, realtime routing, snapshots e source-of-truth do frontend.

---

## Riscos abertos
- Extrair `projects`, `code_actions` e `codex` cedo demais pode quebrar o Jarvez como fonte de verdade do projeto ativo, do historico de tasks e do code worker -> mitigar separando primeiro a API externa do estado local e mantendo catalogo/snapshot no backend principal.
- `backend/actions_domains/home_assistant.py` e `backend/actions_domains/projects.py` ainda misturam dominios diferentes no mesmo arquivo -> mitigar com split interno antes de marcar handlers como `DEPRECATED`.
- `whatsapp` e `onenote` ainda dependem de fallback legado, journal local e helpers de token/OAuth na facade -> mitigar extraindo o MCP sem remover o glue de persistencia e reconexao do Jarvez.
- `rpg` cruza SQLite local, arquivos, PDFs, references vendorizadas e sincronizacao opcional com OneNote -> mitigar tratando `jarvez-mcp-rpg` como repo proprio com assets documentados, sem prometer compatibilidade com MCP publico inexistente.
- `ops` ainda chama runners via modulo `actions`, e automacao/arrival usa glue local de policy e snapshot -> mitigar mantendo `ops` e `automation` locais nesta rodada.

---

## Aceite final
- [ ] Todos os dominios extraiveis tem repo publico no GitHub
  Notas: publicados ate agora com tag `v0.1.0`: `jarvez-mcp-rpg`, `jarvez-mcp-spotify`, `jarvez-mcp-home-assistant`, `jarvez-mcp-thinq`, `jarvez-mcp-onenote`, `jarvez-mcp-whatsapp`, `jarvez-mcp-ac`, `jarvez-mcp-github`, `jarvez-mcp-projects` e `jarvez-mcp-codex`.
- [ ] Jarvez consome MCPs reais pelo client interno e nao apenas por repos publicados
  Notas: integrar e validar no backend principal pelo menos `jarvez-mcp-rpg`, `jarvez-mcp-spotify`, `jarvez-mcp-home-assistant`, `jarvez-mcp-thinq`, `jarvez-mcp-onenote` e `jarvez-mcp-whatsapp`.
- [ ] `actions.py` nao tem mais handlers de dominio, so glue code
  Notas:
- [ ] Jarvez conecta nos MCP servers externos via `claude mcp add`
  Notas: alem do fluxo manual no Claude, o backend principal precisa conseguir subir, descobrir tools e chamar MCPs reais via `backend/mcp/`.
- [ ] AGENTS.md atualizado com todos os novos repos
  Notas: `AGENTS.md` ja inclui `jarvez-mcp-rpg`, `jarvez-mcp-spotify`, `jarvez-mcp-home-assistant`, `jarvez-mcp-thinq`, `jarvez-mcp-onenote`, `jarvez-mcp-whatsapp`, `jarvez-mcp-ac`, `jarvez-mcp-github`, `jarvez-mcp-projects` e `jarvez-mcp-codex`; seguem pendentes os proximos dominios extraidos.

## Nota de sincronizacao
- A ordem restante continua fazendo sentido. A Fase B fica fechada para os dominios priorizados (`whatsapp`, `onenote`, `ac`) sem mover journal, preferências, policy ou automações locais para fora do Jarvez.
- A Fase C comeca por `github` no recorte puro de busca/metadata/clone URL; catalogo local, projeto ativo, selecao e clone fisico continuam no Jarvez.
- Ainda na Fase C, `projects` sai apenas no recorte de metadata (`project_list`, `project_open`, `project_create`, `project_update`); `ProjectCatalog`, indexacao e projeto ativo em sessao continuam como glue local.
- Ainda na Fase C, `codex` sai apenas no recorte de tasks (`codex_exec_task`, `codex_exec_review`, `codex_exec_status`, `codex_cancel_task`, `codex_list_tasks`); historico de sessao, eventos realtime e controle por participante continuam no Jarvez.
- Na Fase E, o piloto recomendado de integracao real e `jarvez-mcp-spotify`, porque oferece o melhor equilibrio entre baixo acoplamento no Jarvez principal e cobertura real de manifesto, env, discovery, `call_tool` e fallback legacy.
