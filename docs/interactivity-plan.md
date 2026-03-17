# Jarvez2.0 - Plano de Interatividade

## Como usar
- Marque `[x]` quando concluido
- Use `[-]` para em andamento
- Use `[ ]` para pendente
- Atualize a linha `Notas:` com contexto curto, branch, PR ou decisao

---

## Visao geral
Este ciclo cobre a frente de interatividade do Jarvez como um plano proprio, separado da migracao MCP. O foco aqui e fazer o assistente parecer natural, rapido, claro e proativo sem mover o papel de control plane para fora do backend principal.

Hoje o Jarvez ja tem runtime de voz em `backend/runtime/`, transporte realtime com LiveKit em `backend/channels/`, snapshot de sessao publicado pelo backend, persistencia operacional em SQLite via `backend/actions_core/store.py` e memoria semantica entre sessoes via Mem0 em `backend/agent.py`. A UI em Next.js ja consome eventos, chips, toasts, visualizer e snapshot, mas ainda nao existe um state machine interativo claro de ponta a ponta para ouvindo -> pensando -> executando -> erro, nem uma camada estruturada de memoria conversacional persistida no SQLite.

Decisoes base deste plano:
- Ativacao inicial com botao dedicado + wake word desde o inicio, usando a mesma camada de estado e fallback explicito.
- Memoria persistente em modelo hibrido: SQLite para contexto estruturado/recente/preferencias/estado operacional; Mem0 para memoria semantica de longo prazo.

## Checklist Mestre

- [ ] V. Voz e naturalidade
  Notas: latencia percebida, confirmacao curta, erro falado, wake word e state machine de interatividade.

- [x] M. Memoria e contexto
  Notas: camada hibrida `SQLite + Mem0` implementada em `backend/memory/memory_manager.py`, com turnos, preferencias e resumo de sessao persistidos.

- [ ] P. Proatividade
  Notas: motor de sugestao ligado a heuristicas locais, memoria e ao substrato de automacoes de `F2.3`.

- [ ] UI. Visual e feedback
  Notas: estado do assistente visivel e sincronizado com o backend, sem poluir a sessao principal.

- [ ] G. Gestos e interacao fisica
  Notas: botao principal, wake word, cancelamento rapido, repeticao e historico recente por gesto.

---

## Frente V - Voz e naturalidade

Contexto tecnico: o runtime realtime ja existe em `backend/runtime/realtime_adapters.py` e `backend/agent.py`, com roteamento ainda concentrado em Google realtime. `backend/channels/router.py` e `livekit_adapter.py` ja transportam eventos/data packets, e a UI ja possui `audio-visualizer`, `StartAudioButton` e tratamento de erro de conexao, mas ainda falta um contrato explicito de interatividade com estados `idle/listening/transcribing/thinking/confirming/executing/background/speaking/error`. Hoje erros operacionais viram toasts e resultados de action em parte do fluxo, mas a camada de voz nao verbaliza recuperacao de forma padronizada.

- [x] V1. Criar state machine de interatividade de voz
  Notas: `backend/voice_interactivity.py` passou a definir o contrato de estado; backend publica `voice_interactivity` via eventos/snapshot e o frontend hidrata/mostra o estado real.

- [x] V2. Emitir confirmacao verbal curta antes de acoes com latencia perceptivel
  Notas: actions com latencia perceptivel agora emitem cue curta como `Abrindo.`, `Procurando.` ou `Deixa comigo.` antes da execucao.

- [x] V3. Reduzir latencia percebida com streaming e preamble curto
  Notas: frontend fala cues via browser TTS e publica `speaking`/`idle` no mesmo contrato de estado, sem esperar a resposta final do modelo.

- [x] V4. Padronizar tratamento de erro em voz
  Notas: falhas operacionais agora publicam estado `error` com mensagem falada curta e convite de retry; o teste novo cobre esse fluxo.

- [x] V5. Entregar ativacao dupla: botao dedicado + wake word
  Notas: `StartAudioButton` publica ativacao por botao e o frontend usa `SpeechRecognition`/`webkitSpeechRecognition` como wake word progressivo com fallback explicito para o botao.

- [x] V6. Ajustar tom de voz e prompt para naturalidade
  Notas: `backend/prompts.py` e `backend/runtime/realtime_adapters.py` foram ajustados para tom mais natural, ack curto e menos rigidez nas transicoes de voz; a voz agora tambem pode ser trocada por `.env` entre `google`, `openai`, `elevenlabs` e `kokoro`.

## Frente M - Memoria e contexto

Contexto tecnico: `backend/agent.py` ja carrega e persiste memoria publica/privada via Mem0 entre sessoes. `backend/actions_core/store.py` ja persiste `session_state`, `event_state`, `pending_confirmations`, `authenticated_sessions`, `channel_messages` e auditoria MCP em SQLite. Ainda nao existe uma camada dedicada de memoria conversacional estruturada que alimente voz, UI e decisao de proatividade com ownership claro entre SQLite e Mem0.

- [x] M1. Introduzir memoria conversacional estruturada em SQLite
  Notas: `backend/actions_core/store.py` agora cria `conversation_turns` e `session_summaries`, e `backend/memory/memory_manager.py` persiste turnos estruturados por sessao.

- [x] M2. Definir politica hibrida SQLite + Mem0
  Notas: `backend/memory/memory_manager.py` passou a centralizar a leitura; SQLite guarda contexto estruturado/recente e preferencias, Mem0 segue como memoria semantica de longo prazo.

- [x] M3. Alimentar o contexto de voz com memoria persistida
  Notas: `backend/agent.py` agora injeta no bootstrap os ultimos turnos relevantes, preferencias, resumo da sessao anterior e memorias Mem0 via `MemoryManager`.

- [x] M4. Persistir preferencias do usuario
  Notas: `user_preferences` foi adicionada ao SQLite e `MemoryManager` expoe `set_preference`, `get_preference` e `list_preferences`.

- [x] M5. Criar politica de resumo e expurgo
  Notas: turnos antigos agora viram `session_summaries` por sessao e saem de `conversation_turns`; a cobertura entrou em `backend/test_memory_manager.py`.

## Frente P - Proatividade

Contexto tecnico: ja existe substrato de automacao em `backend/automation/` com scheduler, triggers e executor, e ja existe proatividade leve no frontend em `frontend/hooks/useAwarenessProactive.ts`. O item `F2.3` de `docs/next-cycle-plan.md` ja assume que automacoes proativas serao fechadas no backend. Falta unificar isso com contexto conversacional, memoria persistida e controles de experiencia para que a proatividade deixe de ser so heuristica local ou rotina agendada.

- [ ] P1. Unificar heuristicas locais e automacoes backend em um motor de sugestao
  Notas: combinar hora do dia, contexto da sessao, memoria, estado do frontend e `F2.3`.

- [ ] P2. Fazer clarificacao antes de acoes ambiguas
  Notas: perguntar quando houver multiplos alvos plausiveis; nao inventar destino nem assumir device/app errado.

- [ ] P3. Sugerir e executar em paralelo quando risco for baixo
  Notas: padrao `posso fazer X; ja estou abrindo Y` para reduzir friccao sem bloquear a conversa.

- [ ] P4. Usar preferencias e rotina aprendida para antecipar sugestoes
  Notas: briefing, apps usuais, dispositivos favoritos, habitos horarios e contexto do momento.

- [ ] P5. Expor controles de proatividade
  Notas: intensidade, silencio temporario, motivo da sugestao e cooldown visivel na UI.

## Frente UI - Visual e feedback

Contexto tecnico: a UI ja hidrata snapshot em `useAgentActionEvents`, tem `session-view`, `audio-visualizer`, toasts, HUD chips, banner de reconnect e prompt de confirmacao. Tambem ja recebe muitos estados de backend como automation, workflows, browser tasks, codex e WhatsApp. O que falta e um feedback visual fiel ao estado real do assistente, em vez de animacao generica ou inferida, preservando a sessao principal limpa como pede o `AGENTS.md`.

- [x] UI1. Expor estado do assistente na sessao principal
  Notas: `session-view.tsx` agora consome `voice_interactivity` tipado e mostra estado compacto com microcopy real no HUD principal.

- [x] UI2. Sincronizar animacoes com o estado real do backend
  Notas: o orb principal passou a variar escala, opacidade e caos a partir de `voice_interactivity`, em vez de animacao generica desacoplada.

- [x] UI3. Mostrar acoes em background sem bloquear a conversa
  Notas: tarefas em `background` e estados longos de browser/workflow/automation/codex agora aparecem como pills compactas e toast resumido, sem abrir painel novo.

- [x] UI4. Tornar falhas impossiveis de passar em silencio
  Notas: `useAgentActionEvents.ts` passou a emitir toast deduplicado para `voice_interactivity.error`, somando feedback visual ao erro falado da Frente V.

- [x] UI5. Consolidar design system de interatividade
  Notas: estados principais agora compartilham palette, motion e microcopy consistentes no HUD e no orb, preservando a sessao limpa em mobile e desktop.

## Frente G - Gestos e interacao fisica

Contexto tecnico: hoje ja existe `StartAudioButton` no frontend, mas nao um modelo completo de gestos ou controles fisicos. O cancelamento de acoes existe em dominios especificos e no kill switch/policy, mas nao como experiencia unica de interacao. Esta frente depende do state machine de interatividade para que botao, wake word e gestos compartilhem o mesmo contrato.

- [ ] G1. Padronizar gesto de iniciar e parar escuta
  Notas: toque/hold no botao principal com fallback consistente para wake word em desktop e mobile.

- [ ] G2. Criar gesto rapido de cancelar acao em andamento
  Notas: botao de emergencia que chame cancelamento ou kill local sem exigir navegacao adicional.

- [ ] G3. Permitir repetir ultima resposta ou acao
  Notas: gesto simples para repetir audio ou refazer resposta; nao reexecutar acao destrutiva por padrao.

- [ ] G4. Expor historico recente por gesto leve
  Notas: swipe ou drawer com ultimas acoes, status e possivel retry.

---

## Dependencias entre frentes

- [ ] V antes de UI
  Notas: sem state machine de voz e execucao, a UI so anima no escuro e nao representa o backend real.

- [ ] M antes de P
  Notas: proatividade boa depende de memoria conversacional, preferencias e contexto persistido de verdade.

- [ ] V antes de G
  Notas: wake word, botao e cancelamento precisam compartilhar o mesmo contrato de estados e transicoes.

- [ ] UI em paralelo com o final de V
  Notas: assim que os eventos de interatividade estiverem estaveis, a UI pode refletir o backend sem esperar o ciclo inteiro.

- [ ] P ligado ao F2.3 do plano principal
  Notas: a camada interativa de proatividade depende do fechamento operacional das automacoes proativas ja planejadas em `docs/next-cycle-plan.md`.

## Ordem de execucao recomendada

- [ ] 1. Frente V
  Notas: maior ganho perceptivel imediato; reduz latencia sentida, falha silenciosa e robotizacao da conversa.

- [ ] 2. Frente UI
  Notas: torna o estado visivel e confiavel assim que V emitir sinais reais do backend.

- [ ] 3. Frente M
  Notas: cria a base para continuidade conversacional, preferencias persistidas e contexto entre sessoes.

- [ ] 4. Frente P
  Notas: depende de memoria e do substrato de automacoes ja existente para evitar sugestao solta ou irritante.

- [ ] 5. Frente G
  Notas: fecha a experiencia com controles fisicos depois que estados, feedback e cancelamento ja estao consolidados.

## Riscos abertos

- [ ] Latencia continuar alta mesmo com melhorias de voz
  Notas: mitigar com ack curto, streaming de audio, confirmacao inicial e background execution quando possivel.

- [ ] Wake word gerar falso positivo ou falso negativo
  Notas: mitigar com botao sempre disponivel, telemetria de ativacao e thresholds ajustaveis.

- [ ] Memoria persistente ficar invasiva ou confusa
  Notas: mitigar com politica clara de escopo, revisao, expurgo e separacao publico/privado.

- [ ] Proatividade irritar o usuario
  Notas: mitigar com cooldown, modo silencioso, justificativa da sugestao e controles de intensidade.

- [ ] UI ficar poluida
  Notas: mitigar com feedback compacto, estado resumido e uso de drawer/rota so quando a experiencia ficar longa demais.

- [ ] Divergencia entre Mem0 e SQLite
  Notas: mitigar com ownership claro: SQLite para contexto estruturado e operacional; Mem0 para memoria semantica.

## Aceite final

- [ ] Feedback inicial emitido em ate 300 ms apos fim de fala ou clique
  Notas: visual ou verbal curto, sem esperar a acao terminar.

- [ ] Inicio de resposta falada em ate 1200 ms p50 e 2000 ms p95
  Notas: medido em fluxos normais sem dependencia externa lenta.

- [ ] Falha silenciosa = 0 nos cenarios de aceite
  Notas: toda falha precisa feedback visual e/ou falado com motivo resumido.

- [ ] Estado do assistente visivel e correto em 100% dos estados principais
  Notas: `idle`, `listening`, `thinking`, `executing`, `background` e `error`.

- [ ] Memoria entre sessoes valida preferencias e ultimo contexto relevante
  Notas: apos reinicio, o Jarvez lembra preferencias e resumo util da sessao anterior.

- [ ] Proatividade respeita cooldown e modo silencioso
  Notas: nenhuma sugestao repetitiva fora da politica definida.

- [ ] Wake word e botao dedicado funcionam com fallback claro
  Notas: se wake word falhar, o botao ainda inicia e encerra a escuta.

- [ ] Cancelamento de emergencia interrompe qualquer acao em andamento
  Notas: acao observavel cancelada no backend e refletida na UI.

## Assuncoes registradas

- [ ] Interatividade segue como frente separada da migracao MCP
  Notas: este plano nao move ownership de integracoes MCP nem reabre as fases de extracao.

- [ ] Jarvez continua como control plane
  Notas: policy, snapshot, audit, session authority e runtime routing permanecem no backend principal.

- [ ] Mem0 nao sera substituido de imediato
  Notas: a memoria atual entre sessoes continua existindo e o SQLite sera expandido como camada estruturada complementar.

- [ ] F2.3 segue como base das automacoes proativas
  Notas: esta frente define a camada interativa em cima do substrato operacional ja previsto no plano principal.
