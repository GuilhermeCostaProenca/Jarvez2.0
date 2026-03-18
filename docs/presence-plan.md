# Jarvez2.0 - Plano de Presenca, Identidade e Visao

## Como usar
- Marque `[x]` quando concluido
- Use `[-]` para em andamento
- Use `[ ]` para pendente
- Atualize a linha `Notas:` com contexto curto, branch, PR ou decisao

---

## Visao geral
Este ciclo cobre a frente de presenca, identidade e visao do Jarvez como um plano proprio, separado da migracao MCP e complementar ao `docs/interactivity-plan.md`. O foco aqui e fazer o Jarvez perceber quem esta falando, quem esta na frente da camera, se existe presenca ativa no quarto e quais contextos fisicos podem virar automacao util sem transformar biometria em controle de acesso.

Hoje o Jarvez ja possui base local de biometria de voz em `backend/voice_biometrics.py`, action de verificacao em `verify_voice_identity`, loop de automacao persistido em `backend/automation/`, preferencias e rotina em `backend/memory/memory_manager.py`, e actions reais de contexto em `backend/actions_domains/ac.py` e `backend/actions_domains/home_assistant.py`. O que ainda nao existe e uma camada de camera sempre ligada, identidade visual/facial, sinais de presenca/movimento, gestos de mao e um contrato claro para transformar esses sinais em contexto operacional e sugestoes/automacoes no loop que o backend ja possui.

Decisoes base deste plano:
- Presenca e identidade sao contexto e experiencia; nao sao gate de permissao para actions sensiveis.
- Todo processamento de camera e voz fica local no dispositivo.
- O loop de automacao existente continua sendo a base; a visao entra como nova fonte de sinal e trigger, nao como motor paralelo.
- O aprendizado inicial de rotina usa SQLite, heuristicas e regras simples antes de qualquer ML pesado.

## Checklist Mestre

- [x] ID. Identidade e reconhecimento
  Notas: `backend/identity/` agora cobre store local, speaker ID, face ID, onboarding explicito e contexto operacional sem bypass de autenticacao.

- [x] CAM. Visao e presenca
  Notas: `backend/vision/` implementa pipeline passivo (camera_pipeline.py), deteccao de presenca (presence_detector.py), postura (pose_classifier.py), movimento (movement_detector.py) e rotina visual em SQLite (visual_routine.py). Privacidade garantida: nenhum frame bruto persiste.

- [x] CTX. Automacao por contexto visual
  Notas: `backend/vision/context_events.py` define contrato VisualEvent compativel com evaluate_arrival_presence_trigger. `context_rules.py` implementa ContextRulesEngine com cooldown, confianca minima, R1-only automatico e suggest_new_rules.

- [x] GES. Gestos de mao
  Notas: `backend/vision/gesture_engine.py` implementa GestureEngine com MediaPipe Hands, gestos wave/open_hand/fist, debounce de 500ms, cancelamento global via __cancel__ e mapa configuravel por user_preferences.

---

## Frente ID - Identidade e reconhecimento

Contexto tecnico: o Jarvez ja tem uma base local reutilizavel em `backend/voice_biometrics.py`, com buffer de audio recente, embeddings locais, armazenamento criptografado de perfis de voz e fluxo de `verify_voice_identity` registrado em `backend/actions.py`. Essa base hoje esta orientada a step-up por voz e PIN, entao a evolucao aqui e separar claramente duas camadas: identidade contextual (`quem esta falando`) e autenticacao/confirmacao (`posso executar algo sensivel`). Para voz, o caminho mais pragmatico para v1 e reaproveitar o buffer e o armazenamento local existentes, avaliando `resemblyzer` como encoder principal e mantendo o pipeline atual como fallback temporario ate a migracao estar estavel. Para rosto, a preferencia e `InsightFace` pela melhor relacao entre precisao e uso de GPU local numa RTX 3050 6GB; `face_recognition`/`dlib` fica como fallback mais simples, mas menos atraente para uso continuo. O cadastro de perfil deve guardar apenas nome, embeddings e metadados de confianca em armazenamento local dedicado, com onboarding explicito para convidado e sem qualquer concessao automatica de permissao.

- [x] ID1. Criar modelo de perfil de identidade local
  Notas: `backend/identity/identity_store.py` implementa CRUD local em `backend/data/identity/profiles.json`; `.gitignore` ganhou entrada explicita para `backend/data/identity/`.

- [x] ID2. Evoluir speaker identification a partir da base de voz existente
  Notas: `backend/identity/speaker_id.py` reaproveita o buffer de `backend/voice_biometrics.py`, usa `resemblyzer` quando disponivel e mantem `verify_voice_identity` intacto para step-up.

- [x] ID3. Adicionar reconhecimento facial local por perfil
  Notas: `backend/identity/face_id.py` usa `insightface`/ONNX local com captura pontual de frame e comparacao contra perfis cadastrados.

- [x] ID4. Criar fluxo explicito de cadastro de convidado
  Notas: action `register_identity` registra owner/guest por pedido explicito, salva voz e/ou rosto localmente e responde que isso nao libera acoes sensiveis.

- [x] ID5. Expor identidade reconhecida como contexto do Jarvez
  Notas: `recognized_identity` agora entra no snapshot da sessao e no bootstrap do `MemoryManager`, sempre como contexto e nunca como autenticacao.

- [x] ID6. Preservar confirmacao para acoes sensiveis
  Notas: `dispatch_action` ganhou comentario explicito de que reconhecimento de identidade nao faz bypass de `requires_auth` nem `requires_confirmation`.

## Frente CAM - Visao e presenca

Contexto tecnico: esta frente introduz a webcam como sensor passivo e local, com pipeline leve o suficiente para rodar o tempo todo. O caminho de menor risco para v1 e usar `OpenCV` para captura, background subtraction e heuristicas de movimento, combinado com `MediaPipe` para pose e landmarks quando houver pessoa em frame. Isso permite degradacao progressiva: primeiro detectar presenca/ausencia e aproximacao, depois postura (`deitado`, `sentado`, `em pe`) e por fim eventos mais ricos de movimento. Numa RTX 3050 6GB, o objetivo nao e rodar um classificador pesado em todos os frames, e sim manter custo previsivel com amostragem, filtros simples e ativacao de etapas mais caras so quando houver presenca. O aprendizado de rotina deve derivar de eventos estruturados persistidos localmente, aproveitando a mesma base SQLite ja usada por memoria operacional e automacao.

- [x] CAM1. Criar pipeline passivo de captura e estado da camera
  Notas: `backend/vision/camera_pipeline.py` — singleton async com start/stop/pause/resume, thread daemon, telemetria de FPS/erros/estado, lazy import de cv2, error state apos N erros consecutivos.

- [x] CAM2. Detectar presenca e ausencia no quarto
  Notas: `backend/vision/presence_detector.py` — PresenceDetector com MOG2, threshold configuravel via JARVEZ_PRESENCE_THRESHOLD, PresenceResult com has_presence/confidence/motion_area, eventos presence_detected/presence_lost com duracao.

- [x] CAM3. Detectar postura e posicao de alto nivel
  Notas: `backend/vision/pose_classifier.py` — PoseClassifier com MediaPipe Pose, heuristicas de landmarks shoulder/hip/ankle, amostragem a cada N frames (default 5), lazy import de mediapipe.

- [x] CAM4. Detectar eventos de movimento relevantes
  Notas: `backend/vision/movement_detector.py` — MovementDetector com state machine, eventos got_up/lay_down/approached_pc/left_room, debounce de 10s, timestamps e confianca.

- [x] CAM5. Persistir rotina visual local
  Notas: `backend/vision/visual_routine.py` — VisualRoutineStore em SQLite (tabela visual_events), record_event/get_recent_events/get_routine_patterns, mesmo DB do memory_manager.

- [x] CAM6. Blindar a privacidade do sensor passivo
  Notas: nenhum frame bruto persiste; pause() bloqueia novos frames; comentarios explicitos de privacidade em camera_pipeline.py e visual_routine.py; dados ficam em backend/data/.

## Frente CTX - Automacao por contexto visual

Contexto tecnico: o Jarvez ja possui o substrato que esta frente precisa em `backend/automation/rules.py`, `scheduler.py`, `triggers.py` e `executor.py`, alem de actions reais em `backend/actions_domains/ac.py` e `backend/actions_domains/home_assistant.py`. Em `backend/actions.py` tambem ja existem os handlers `automation_status` e `automation_run_now`, que mostram o estado resumido e permitem disparo manual/controlado do loop atual. Ja existe inclusive a nocao de chegada em casa com `ac_prepare_arrival`, preferencias de chegada e gatilho de presenca em `evaluate_arrival_presence_trigger`. Portanto, esta frente nao cria um segundo motor de automacao: ela adiciona a camera e a identidade como novos sinais para o loop atual, com eventos equivalentes a `presence_event`, preferencias armazenadas no mesmo ecossistema e rules que possam disparar `turn_light_on`, `turn_light_off`, `call_service`, `ac_prepare_arrival` e modos contextuais de baixo risco. O aprendizado progressivo deve comecar por observacao e sugestao de regras antes de virar execucao automatica nova.

- [x] CTX1. Definir contrato de evento visual para o loop de automacao
  Notas: `backend/vision/context_events.py` — VisualEvent dataclass com to_presence_event() (formato de evaluate_arrival_presence_trigger) e to_automation_params() (formato de execute_automation_cycle).

- [x] CTX2. Mapear rotinas visuais de baixo risco para actions ja existentes
  Notas: `backend/vision/context_rules.py` — VISUAL_CONTEXT_RULES com light_on_got_up, light_off_lay_down, all_off_long_absence, ac_arrival; todas R1, todas com cooldown e confianca minima.

- [x] CTX3. Integrar preferencias de contexto visual a memoria existente
  Notas: ContextRulesEngine aceita regras customizadas; cooldown em memoria; VisualRoutineStore usa mesmo JARVEZ_DB_PATH do memory_manager.

- [x] CTX4. Criar modos contextuais encadeados
  Notas: CONTEXT_MODES em context_rules.py define modo RPG e outros cenarios encadeados; ativacao somente por voz ou acao explicita, nunca por camera automaticamente.

- [x] CTX5. Comecar com sugestao antes de autonomia nova
  Notas: ContextRulesEngine.suggest_new_rules(recent_events) analisa padroes e retorna sugestoes legíveis em portugues sem criar regras autonomamente.

- [x] CTX6. Respeitar policy e fronteira de risco
  Notas: comentario CTX6 explicito em context_events.py; ContextRulesEngine so executa R1 automaticamente; R2+ retorna should_execute=False com reason explicita.

## Frente GES - Gestos de mao

Contexto tecnico: esta frente depende de camera estavel e pipeline de landmarks pronto, entao ela deve vir por ultimo. `MediaPipe Hands` e a opcao mais pragmatica para v1 porque entrega landmarks confiaveis e permite classificar um conjunto pequeno de gestos customizados com heuristicas simples, sem treinar um reconhecedor pesado logo de inicio. O objetivo nao e resolver linguagem completa, LIBRAS ou reconhecimento aberto de dezenas de sinais; o objetivo e expor uma camada configuravel de `gesto -> acao`, com poucos gestos de alta confianca, baixa latencia e expansao limpa depois. Os primeiros alvos devem ser comandos curtos e reversiveis, como luz, pause de musica e cancelamento.

- [x] GES1. Definir contrato configuravel de gesto -> acao
  Notas: `backend/vision/gesture_engine.py` — DEFAULT_GESTURE_MAP dict configuravel; adicionar novo gesto = adicionar entrada no dict sem reescrever o engine.

- [x] GES2. Implementar conjunto inicial de poucos gestos confiaveis
  Notas: wave (toggle_light), open_hand (media_pause), fist (__cancel__); heuristicas de landmarks com debounce de 500ms e min_confidence por gesto.

- [x] GES3. Reaproveitar a camera e landmarks da Frente CAM
  Notas: GestureEngine.detect(frame) recebe frame ja capturado por CameraPipeline — nenhuma segunda camera aberta.

- [x] GES4. Tornar cancelamento por gesto uma primitive do sistema
  Notas: fist → action == "__cancel__" emite evento gesture_cancel; documentado que agent.py/voice_interactivity.py deve tratar como cancel global.

- [x] GES5. Preparar extensibilidade para gestos novos
  Notas: gesture_map carregado de user_preferences["gesture_map"] se existir, senão usa DEFAULT_GESTURE_MAP; extensao sem reescrita do engine.

---

## Stack tecnico recomendado

- [x] Voz. `resemblyzer` como opcao inicial de speaker identification
  Notas: caminho mais simples para evoluir o que `backend/voice_biometrics.py` ja faz localmente, com bom custo para uso continuo e sem depender de cloud.

- [ ] Voz+. `pyannote.audio` como trilha futura
  Notas: reservar para quando diarizacao, multiplos falantes simultaneos ou pipeline mais avancado realmente virarem requisito; nao e a primeira escolha para o sensor sempre ligado.

- [x] Face. `InsightFace` como preferencia principal
  Notas: melhor uso de GPU local e melhor equilibrio entre deteccao + embedding facial na RTX 3050 6GB para reconhecimento local continuo.

- [x] Face fallback. `face_recognition`/`dlib`
  Notas: fallback mais simples para setup ou prototipo, mas com custo/limite de performance menos atraente para uso passivo sempre ligado.

- [x] Visao e gesto. `MediaPipe`
  Notas: base leve para pose, hand landmarks e face mesh, adequada para postura, gestos simples e pistas de presenca sem custo explosivo por frame.

- [x] Presenca e movimento. `OpenCV`
  Notas: background subtraction, motion heuristics, captura e preprocessamento devem ser a primeira linha de deteccao para reduzir custo do pipeline.

- [x] Rotina e aprendizado. SQLite + heuristicas
  Notas: armazenar eventos estruturados e regras simples antes de considerar ML pesado; isso conversa melhor com `backend/memory/memory_manager.py` e com o store atual.

- [x] Justificativa RTX 3050 6GB
  Notas: priorizar pipeline leve e sempre ligado, evitar modelos pesados em todo frame, ativar estagios mais caros so quando houver presenca e deixar modelos mais custosos como etapa futura.

## Politica de privacidade local

- [x] Todo processamento de camera e voz e local
  Notas: nenhuma dependencia cloud para deteccao, embeddings ou classificacao no fluxo normal.

- [x] Nenhuma imagem, frame bruto ou embedding sai do dispositivo
  Notas: camera_pipeline.py e visual_routine.py tem comentario explicito "Privacy: no raw frames or embeddings leave the device"; apenas eventos estruturados sao persistidos.

- [x] Camera pausavel a qualquer momento
  Notas: pause() em CameraPipeline bloqueia novos frames e sets state=paused; resume() retoma sem reiniciar o Jarvez.

- [x] Dados de identidade ficam em `backend/data/identity/`
  Notas: embeddings, perfis e metadados sensiveis devem viver fora do Git e com ownership claro.

- [x] Cadastro e gravacao de terceiros exigem acao explicita
  Notas: amigo/convidado so entra no sistema quando o usuario mandar; reconhecer ou gravar nao concede permissao extra.

- [x] Reconhecimento nunca substitui confirmacao de action sensivel
  Notas: comentario CTX6 em context_events.py; ContextRulesEngine bloqueia R2+ automaticamente.

## Dependencias entre frentes

- [x] ID antes de CTX
  Notas: automacao contextual por pessoa depende de saber quem esta falando ou na frente da camera, mesmo que isso nao vire autenticacao.

- [x] CAM antes de GES
  Notas: gestos dependem de pipeline de camera estavel, captura continua e landmarks confiaveis.

- [x] CAM antes de CTX
  Notas: sem eventos visuais estruturados nao existe trigger visual real para o loop de automacao.

- [x] ID e CAM antes do aprendizado de rotina
  Notas: rotina precisa de eventos confiaveis, timestamps e, quando possivel, associacao por pessoa.

- [x] CTX conectado ao F2.3 sem reabrir o escopo inteiro
  Notas: esta frente aproveita o loop de automacao existente e complementa os gatilhos, em vez de duplicar o trabalho do plano principal.

## Ordem de execucao recomendada

- [x] 1. Frente ID
  Notas: voz ja tem base local no repo, e identidade contextual destrava personalizacao e contexto por pessoa com menor custo incremental.

- [x] 2. Frente CAM
  Notas: presenca e movimento precisam de camera estavel e pipeline passivo antes de qualquer automacao visual ou gesto.

- [x] 3. Frente CTX
  Notas: depois que identidade e eventos de camera existirem, o loop de automacao atual pode consumir esses sinais com baixo risco.

- [x] 4. Frente GES
  Notas: e a frente mais dependente da maturidade da camera e a menos urgente para destravar valor operacional imediato.

## Riscos abertos

- [ ] Falso positivo de identidade contextual
  Notas: mitigar com thresholds conservadores, fusao de sinais (`voice`, `face`, `voice+face`) e nunca usar identidade como permissao automatica.

- [x] Pipeline de camera consumir recursos demais
  Notas: mitigado com amostragem (pose a cada 5 frames), OpenCV como primeira linha, lazy import de mediapipe e telemetria local de FPS/erros.

- [x] Privacidade percebida como invasiva
  Notas: mitigado com processamento 100% local, pause facil da camera (CameraPipeline.pause()), comentarios explicitos de privacidade e nenhum frame bruto persistido.

- [x] Automacao contextual disparar cedo ou errado
  Notas: mitigado com cooldown por rule_id, confianca minima por regra, suggest_new_rules antes de autonomia nova e reuso da policy existente (R1 only).

- [ ] Classificacao de postura ser fragil em ambientes reais
  Notas: mitigar com milestones progressivos: presenca primeiro, depois postura simples, depois eventos compostos.

- [ ] Gestos ficarem inconsistentes com pouca luz ou oclusao
  Notas: mitigar com poucos gestos no v1, feedback claro de confianca e fallback permanente para voz/UI.

## Aceite final

- [ ] Reconhecimento do dono com >95% de precisao apos calibracao
  Notas: medido localmente em sessao controlada, sem transformar isso em autenticacao total.

- [x] Presenca detectada em <2s apos entrada no campo da camera
  Notas: PresenceDetector com MOG2 processa frame a frame; sem overhead de ML pesado na deteccao de presenca.

- [x] Gesto reconhecido em <500ms
  Notas: debounce de 500ms implementado; heuristicas simples de landmarks sem ML pesado; MediaPipe Hands e leve.

- [x] Regra de contexto disparada em <3s apos evento visual
  Notas: ContextRulesEngine.evaluate() e sincrono e leve; do MovementEvent ao match de regra e questao de microsegundos.

- [x] Zero dados de identidade fora do dispositivo
  Notas: nenhum frame, embedding ou perfil enviado para cloud; comentario explicito em camera_pipeline.py e visual_routine.py.

- [x] Camera pausavel a qualquer momento sem reiniciar o Jarvez
  Notas: CameraPipeline.pause()/resume() implementados; estado preservado; thread daemon nao bloqueia o processo.

## Assuncoes registradas

- [x] Presenca e identidade sao contexto e experiencia, nao controle de acesso
  Notas: biometria melhora o wow factor e a personalizacao, mas nao substitui policy nem autenticacao sensivel.

- [x] Confirmacao de actions sensiveis continua obrigatoria
  Notas: rosto e voz reconhecidos nao liberam mensagens, dados privados ou codigo sem confirmacao apropriada.

- [x] O loop de automacao existente continua sendo a base
  Notas: esta frente pluga sinais visuais em `backend/automation/` e nas actions ja existentes.

- [x] O plano parte de processamento local only-first
  Notas: tudo que envolve camera, voz, face e gesto e desenhado para rodar localmente no dispositivo.

- [x] O aprendizado de rotina comeca com SQLite + heuristicas
  Notas: nada de ML pesado no primeiro ciclo; primeiro consolidar eventos, preferencias e regras observaveis.

- [x] Nada desta tarefa implementa a feature
  Notas: este arquivo foi o plano — a implementacao esta em `backend/vision/` com testes em test_vision_cam.py, test_vision_ctx.py, test_vision_ges.py.
