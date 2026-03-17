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
- [ ] Criar repo `jarvez-mcp-home-assistant`
  Notas:
- [ ] Migrar codigo de `backend/actions_domains/home_assistant.py`
  Notas:
- [ ] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas:
- [ ] Criar CHANGELOG.md com v0.1.0
  Notas:
- [ ] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-home-assistant com tag v0.1.0
  Notas:
- [ ] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas:
- [ ] Registrar em AGENTS.md como repositorio de referencia
  Notas:

##### Dominio: thinq
Contexto tecnico: `backend/actions_domains/thinq.py` esta isolado, mas continua dependente de credenciais e helpers ThinQ na facade; nao houve MCP publico confirmado para este dominio.
- [ ] Criar repo `jarvez-mcp-thinq`
  Notas:
- [ ] Migrar codigo de `backend/actions_domains/thinq.py`
  Notas:
- [ ] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas:
- [ ] Criar CHANGELOG.md com v0.1.0
  Notas:
- [ ] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-thinq com tag v0.1.0
  Notas:
- [ ] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas:
- [ ] Registrar em AGENTS.md como repositorio de referencia
  Notas:

#### Fase B — Integracoes com estado local e callbacks

##### Dominio: whatsapp
Contexto tecnico: a extracao precisa considerar `backend/actions_domains/whatsapp.py`, `backend/actions_domains/whatsapp_channel.py` e `backend/integrations/whatsapp_mcp_client.py`, preservando fallback `whatsapp_legacy_v1` e o journal persistido em `channel_messages` como glue do Jarvez.
- [ ] Criar repo `jarvez-mcp-whatsapp`
  Notas:
- [ ] Migrar codigo de `backend/actions_domains/whatsapp.py`
  Notas:
- [ ] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas:
- [ ] Criar CHANGELOG.md com v0.1.0
  Notas:
- [ ] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-whatsapp com tag v0.1.0
  Notas:
- [ ] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas:
- [ ] Registrar em AGENTS.md como repositorio de referencia
  Notas:

##### Dominio: onenote
Contexto tecnico: `backend/actions_domains/onenote.py` ja esta isolado, mas os helpers de OAuth, token persistence e chamadas Graph ainda estao na facade de `backend/actions.py`.
- [ ] Criar repo `jarvez-mcp-onenote`
  Notas:
- [ ] Migrar codigo de `backend/actions_domains/onenote.py`
  Notas:
- [ ] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas:
- [ ] Criar CHANGELOG.md com v0.1.0
  Notas:
- [ ] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-onenote com tag v0.1.0
  Notas:
- [ ] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas:
- [ ] Registrar em AGENTS.md como repositorio de referencia
  Notas:

##### Dominio: ac
Contexto tecnico: `backend/actions_domains/ac.py` depende do dominio ThinQ e das preferencias/automacoes locais de chegada; so entra depois de `jarvez-mcp-thinq` estar definido.
- [ ] Criar repo `jarvez-mcp-ac`
  Notas:
- [ ] Migrar codigo de `backend/actions_domains/ac.py`
  Notas:
- [ ] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas:
- [ ] Criar CHANGELOG.md com v0.1.0
  Notas:
- [ ] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-ac com tag v0.1.0
  Notas:
- [ ] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas:
- [ ] Registrar em AGENTS.md como repositorio de referencia
  Notas:

#### Fase C — Superficie de engenharia local

##### Dominio: github
Contexto tecnico: `github_*` hoje esta misturado em `backend/actions_domains/projects.py`; antes de publicar `jarvez-mcp-github`, e preciso separar busca/metadata GitHub do catalogo e da selecao de projeto local.
- [ ] Criar repo `jarvez-mcp-github`
  Notas:
- [ ] Migrar codigo de `backend/actions_domains/projects.py`
  Notas:
- [ ] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas:
- [ ] Criar CHANGELOG.md com v0.1.0
  Notas:
- [ ] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-github com tag v0.1.0
  Notas:
- [ ] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas:
- [ ] Registrar em AGENTS.md como repositorio de referencia
  Notas:

##### Dominio: projects
Contexto tecnico: `backend/actions_domains/projects.py` depende de `ProjectCatalog`, de projeto ativo em sessao, de indexacao local e do glue de `git_clone_repository`; a extracao precisa manter o Jarvez como fonte de verdade do catalogo e do projeto selecionado.
- [ ] Criar repo `jarvez-mcp-projects`
  Notas:
- [ ] Migrar codigo de `backend/actions_domains/projects.py`
  Notas:
- [ ] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas:
- [ ] Criar CHANGELOG.md com v0.1.0
  Notas:
- [ ] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-projects com tag v0.1.0
  Notas:
- [ ] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas:
- [ ] Registrar em AGENTS.md como repositorio de referencia
  Notas:

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
- [ ] Criar repo `jarvez-mcp-codex`
  Notas:
- [ ] Migrar codigo de `backend/actions_domains/codex.py`
  Notas:
- [ ] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas:
- [ ] Criar CHANGELOG.md com v0.1.0
  Notas:
- [ ] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-codex com tag v0.1.0
  Notas:
- [ ] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas:
- [ ] Registrar em AGENTS.md como repositorio de referencia
  Notas:

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
- [ ] Criar repo `jarvez-mcp-rpg`
  Notas:
- [ ] Migrar codigo de `backend/actions_domains/rpg.py`
  Notas:
- [ ] Escrever README com instrucoes de conexao (Claude Code + Jarvez)
  Notas:
- [ ] Criar CHANGELOG.md com v0.1.0
  Notas:
- [ ] Subir para github.com/GuilhermeCostaProenca/jarvez-mcp-rpg com tag v0.1.0
  Notas:
- [ ] Adicionar comentario DEPRECATED nos handlers em `actions.py`
  Notas:
- [ ] Registrar em AGENTS.md como repositorio de referencia
  Notas:

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

#### Fase E — Limpeza final
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
  Notas:
- [ ] `actions.py` nao tem mais handlers de dominio, so glue code
  Notas:
- [ ] Jarvez conecta nos MCP servers externos via `claude mcp add`
  Notas:
- [ ] AGENTS.md atualizado com todos os novos repos
  Notas:
