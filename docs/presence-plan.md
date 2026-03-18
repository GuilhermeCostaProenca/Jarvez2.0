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

- [ ] ID. Identidade e reconhecimento
  Notas: speaker identification, reconhecimento facial, cadastro de perfil local e contexto por pessoa sem virar autenticacao.

- [ ] CAM. Visao e presenca
  Notas: webcam passiva, deteccao de presenca, postura, movimento e eventos fisicos com pipeline local sempre ligado.

- [ ] CTX. Automacao por contexto visual
  Notas: sinais visuais alimentando `backend/automation/`, `ac_prepare_arrival`, Home Assistant e modos contextuais sem duplicar F2.3.

- [ ] GES. Gestos de mao
  Notas: poucos gestos customizados, configuraveis e expansivos, com cancelamento e controles rapidos no v1.

---

## Frente ID - Identidade e reconhecimento

Contexto tecnico: o Jarvez ja tem uma base local reutilizavel em `backend/voice_biometrics.py`, com buffer de audio recente, embeddings locais, armazenamento criptografado de perfis de voz e fluxo de `verify_voice_identity` registrado em `backend/actions.py`. Essa base hoje esta orientada a step-up por voz e PIN, entao a evolucao aqui e separar claramente duas camadas: identidade contextual (`quem esta falando`) e autenticacao/confirmacao (`posso executar algo sensivel`). Para voz, o caminho mais pragmatico para v1 e reaproveitar o buffer e o armazenamento local existentes, avaliando `resemblyzer` como encoder principal e mantendo o pipeline atual como fallback temporario ate a migracao estar estavel. Para rosto, a preferencia e `InsightFace` pela melhor relacao entre precisao e uso de GPU local numa RTX 3050 6GB; `face_recognition`/`dlib` fica como fallback mais simples, mas menos atraente para uso continuo. O cadastro de perfil deve guardar apenas nome, embeddings e metadados de confianca em armazenamento local dedicado, com onboarding explicito para convidado e sem qualquer concessao automatica de permissao.

- [ ] ID1. Criar modelo de perfil de identidade local
  Notas: definir armazenamento em `backend/data/identity/` para dono, convidados explicitamente cadastrados, embeddings de voz/rosto, nivel de confianca e timestamps sem sair do dispositivo.

- [ ] ID2. Evoluir speaker identification a partir da base de voz existente
  Notas: reaproveitar `backend/voice_biometrics.py`, `VoiceProfileStore` e `verify_voice_identity` para separar reconhecimento contextual de step-up de seguranca.

- [ ] ID3. Adicionar reconhecimento facial local por perfil
  Notas: webcam gera embeddings faciais locais, com `InsightFace` como preferencia e `face_recognition` como fallback, sempre com calibacao inicial por perfil.

- [ ] ID4. Criar fluxo explicito de cadastro de convidado
  Notas: so cadastrar terceiros quando o usuario disser explicitamente quem e a pessoa; gravar amigo nao libera nenhuma acao nem muda policy.

- [ ] ID5. Expor identidade reconhecida como contexto do Jarvez
  Notas: publicar nome reconhecido, confianca e fonte (`voice`, `face`, `voice+face`) como contexto e memoria operacional, sem marcar sessao como autenticada por causa disso.

- [ ] ID6. Preservar confirmacao para acoes sensiveis
  Notas: mensagens, dados privados, codigo e outras actions sensiveis continuam exigindo confirmacao/autenticacao independente da identidade reconhecida.

## Frente CAM - Visao e presenca

Contexto tecnico: esta frente introduz a webcam como sensor passivo e local, com pipeline leve o suficiente para rodar o tempo todo. O caminho de menor risco para v1 e usar `OpenCV` para captura, background subtraction e heuristicas de movimento, combinado com `MediaPipe` para pose e landmarks quando houver pessoa em frame. Isso permite degradacao progressiva: primeiro detectar presenca/ausencia e aproximacao, depois postura (`deitado`, `sentado`, `em pe`) e por fim eventos mais ricos de movimento. Numa RTX 3050 6GB, o objetivo nao e rodar um classificador pesado em todos os frames, e sim manter custo previsivel com amostragem, filtros simples e ativacao de etapas mais caras so quando houver presenca. O aprendizado de rotina deve derivar de eventos estruturados persistidos localmente, aproveitando a mesma base SQLite ja usada por memoria operacional e automacao.

- [ ] CAM1. Criar pipeline passivo de captura e estado da camera
  Notas: webcam ligada o tempo todo, com pausar/retomar sem reiniciar o Jarvez e observabilidade minima de FPS, erro e estado atual.

- [ ] CAM2. Detectar presenca e ausencia no quarto
  Notas: usar heuristicas leves para responder rapido se existe alguem no ambiente e registrar eventos de entrada, saida e permanencia.

- [ ] CAM3. Detectar postura e posicao de alto nivel
  Notas: classificar `deitado`, `sentado`, `em pe`, `fora de frame` com `MediaPipe Pose` e heuristicas simples antes de considerar modelos mais caros.

- [ ] CAM4. Detectar eventos de movimento relevantes
  Notas: levantar da cama, aproximar do PC, afastar do setup e sair do comodo devem virar eventos estruturados com timestamps e confianca.

- [ ] CAM5. Persistir rotina visual local
  Notas: registrar horarios, duracoes e sequencias recorrentes em SQLite para alimentar sugestoes futuras sem ML pesado no v1.

- [ ] CAM6. Blindar a privacidade do sensor passivo
  Notas: nenhum frame bruto, imagem ou embedding sai do dispositivo; camera pausavel e politica clara para terceiros.

## Frente CTX - Automacao por contexto visual

Contexto tecnico: o Jarvez ja possui o substrato que esta frente precisa em `backend/automation/rules.py`, `scheduler.py`, `triggers.py` e `executor.py`, alem de actions reais em `backend/actions_domains/ac.py` e `backend/actions_domains/home_assistant.py`. Em `backend/actions.py` tambem ja existem os handlers `automation_status` e `automation_run_now`, que mostram o estado resumido e permitem disparo manual/controlado do loop atual. Ja existe inclusive a nocao de chegada em casa com `ac_prepare_arrival`, preferencias de chegada e gatilho de presenca em `evaluate_arrival_presence_trigger`. Portanto, esta frente nao cria um segundo motor de automacao: ela adiciona a camera e a identidade como novos sinais para o loop atual, com eventos equivalentes a `presence_event`, preferencias armazenadas no mesmo ecossistema e rules que possam disparar `turn_light_on`, `turn_light_off`, `call_service`, `ac_prepare_arrival` e modos contextuais de baixo risco. O aprendizado progressivo deve comecar por observacao e sugestao de regras antes de virar execucao automatica nova.

- [ ] CTX1. Definir contrato de evento visual para o loop de automacao
  Notas: presenca, ausencia, postura, movimento e identidade reconhecida devem virar eventos estruturados reutilizaveis por `backend/automation/`.

- [ ] CTX2. Mapear rotinas visuais de baixo risco para actions ja existentes
  Notas: levantar -> luz, deitar -> luz/AC, ausencia longa -> desligar tudo, chegada + calor -> `ac_prepare_arrival` e possivel abertura de jogo.

- [ ] CTX3. Integrar preferencias de contexto visual a memoria existente
  Notas: usar `backend/memory/memory_manager.py` e SQLite para guardar regras favoritas, cooldowns, horarios e excecoes do usuario.

- [ ] CTX4. Criar modos contextuais encadeados
  Notas: `modo RPG` e outros cenarios devem reaproveitar o loop atual para executar sequencias observaveis com evidencia e controle.

- [ ] CTX5. Comecar com sugestao antes de autonomia nova
  Notas: quando o sistema detectar padroes recorrentes, sugerir novas regras ao usuario antes de automatizar sozinho.

- [ ] CTX6. Respeitar policy e fronteira de risco
  Notas: contexto visual pode acionar rotina de baixo risco, mas acoes sensiveis continuam com confirmacao e policy existentes.

## Frente GES - Gestos de mao

Contexto tecnico: esta frente depende de camera estavel e pipeline de landmarks pronto, entao ela deve vir por ultimo. `MediaPipe Hands` e a opcao mais pragmatica para v1 porque entrega landmarks confiaveis e permite classificar um conjunto pequeno de gestos customizados com heuristicas simples, sem treinar um reconhecedor pesado logo de inicio. O objetivo nao e resolver linguagem completa, LIBRAS ou reconhecimento aberto de dezenas de sinais; o objetivo e expor uma camada configuravel de `gesto -> acao`, com poucos gestos de alta confianca, baixa latencia e expansao limpa depois. Os primeiros alvos devem ser comandos curtos e reversiveis, como luz, pause de musica e cancelamento.

- [ ] GES1. Definir contrato configuravel de gesto -> acao
  Notas: permitir ao usuario mapear gestos a actions de baixo risco sem reescrever o pipeline para cada novo gesto.

- [ ] GES2. Implementar conjunto inicial de poucos gestos confiaveis
  Notas: `aceno`, `mao_aberta` e `punho` como base, com latencia curta e threshold de confianca conservador.

- [ ] GES3. Reaproveitar a camera e landmarks da Frente CAM
  Notas: nenhum pipeline paralelo de webcam; gestos entram como camada adicional sobre a camera ja estavel.

- [ ] GES4. Tornar cancelamento por gesto uma primitive do sistema
  Notas: `punho` deve servir como gesto global de cancelar acao/execucao quando a sessao estiver ativa.

- [ ] GES5. Preparar extensibilidade para gestos novos
  Notas: adicionar novos gestos ou, no futuro, LIBRAS parcial, sem quebrar mapeamentos existentes nem reescrever a arquitetura.

---

## Stack tecnico recomendado

- [ ] Voz. `resemblyzer` como opcao inicial de speaker identification
  Notas: caminho mais simples para evoluir o que `backend/voice_biometrics.py` ja faz localmente, com bom custo para uso continuo e sem depender de cloud.

- [ ] Voz+. `pyannote.audio` como trilha futura
  Notas: reservar para quando diarizacao, multiplos falantes simultaneos ou pipeline mais avancado realmente virarem requisito; nao e a primeira escolha para o sensor sempre ligado.

- [ ] Face. `InsightFace` como preferencia principal
  Notas: melhor uso de GPU local e melhor equilibrio entre deteccao + embedding facial na RTX 3050 6GB para reconhecimento local continuo.

- [ ] Face fallback. `face_recognition`/`dlib`
  Notas: fallback mais simples para setup ou prototipo, mas com custo/limite de performance menos atraente para uso passivo sempre ligado.

- [ ] Visao e gesto. `MediaPipe`
  Notas: base leve para pose, hand landmarks e face mesh, adequada para postura, gestos simples e pistas de presenca sem custo explosivo por frame.

- [ ] Presenca e movimento. `OpenCV`
  Notas: background subtraction, motion heuristics, captura e preprocessamento devem ser a primeira linha de deteccao para reduzir custo do pipeline.

- [ ] Rotina e aprendizado. SQLite + heuristicas
  Notas: armazenar eventos estruturados e regras simples antes de considerar ML pesado; isso conversa melhor com `backend/memory/memory_manager.py` e com o store atual.

- [ ] Justificativa RTX 3050 6GB
  Notas: priorizar pipeline leve e sempre ligado, evitar modelos pesados em todo frame, ativar estagios mais caros so quando houver presenca e deixar modelos mais custosos como etapa futura.

## Politica de privacidade local

- [ ] Todo processamento de camera e voz e local
  Notas: nenhuma dependencia cloud para deteccao, embeddings ou classificacao no fluxo normal.

- [ ] Nenhuma imagem, frame bruto ou embedding sai do dispositivo
  Notas: armazenamento e processamento ficam locais; identidade nao e exportada para servicos externos.

- [ ] Camera pausavel a qualquer momento
  Notas: usuario precisa poder desligar o sensor sem reiniciar o Jarvez nem corromper estado operacional.

- [ ] Dados de identidade ficam em `backend/data/identity/`
  Notas: embeddings, perfis e metadados sensiveis devem viver fora do Git e com ownership claro.

- [ ] Cadastro e gravacao de terceiros exigem acao explicita
  Notas: amigo/convidado so entra no sistema quando o usuario mandar; reconhecer ou gravar nao concede permissao extra.

- [ ] Reconhecimento nunca substitui confirmacao de action sensivel
  Notas: contexto visual e de voz melhora experiencia, mas nao derruba policy de seguranca existente.

## Dependencias entre frentes

- [ ] ID antes de CTX
  Notas: automacao contextual por pessoa depende de saber quem esta falando ou na frente da camera, mesmo que isso nao vire autenticacao.

- [ ] CAM antes de GES
  Notas: gestos dependem de pipeline de camera estavel, captura continua e landmarks confiaveis.

- [ ] CAM antes de CTX
  Notas: sem eventos visuais estruturados nao existe trigger visual real para o loop de automacao.

- [ ] ID e CAM antes do aprendizado de rotina
  Notas: rotina precisa de eventos confiaveis, timestamps e, quando possivel, associacao por pessoa.

- [ ] CTX conectado ao F2.3 sem reabrir o escopo inteiro
  Notas: esta frente aproveita o loop de automacao existente e complementa os gatilhos, em vez de duplicar o trabalho do plano principal.

## Ordem de execucao recomendada

- [ ] 1. Frente ID
  Notas: voz ja tem base local no repo, e identidade contextual destrava personalizacao e contexto por pessoa com menor custo incremental.

- [ ] 2. Frente CAM
  Notas: presenca e movimento precisam de camera estavel e pipeline passivo antes de qualquer automacao visual ou gesto.

- [ ] 3. Frente CTX
  Notas: depois que identidade e eventos de camera existirem, o loop de automacao atual pode consumir esses sinais com baixo risco.

- [ ] 4. Frente GES
  Notas: e a frente mais dependente da maturidade da camera e a menos urgente para destravar valor operacional imediato.

## Riscos abertos

- [ ] Falso positivo de identidade contextual
  Notas: mitigar com thresholds conservadores, fusao de sinais (`voice`, `face`, `voice+face`) e nunca usar identidade como permissao automatica.

- [ ] Pipeline de camera consumir recursos demais
  Notas: mitigar com amostragem, OpenCV como primeira linha, ativacao progressiva de landmarks e telemetria local de performance.

- [ ] Privacidade percebida como invasiva
  Notas: mitigar com processamento 100% local, pause facil da camera, politica clara e onboarding explicito para terceiros.

- [ ] Automacao contextual disparar cedo ou errado
  Notas: mitigar com cooldown, confianca minima, sugestao antes de autonomia nova e reuso da policy/observabilidade existentes.

- [ ] Classificacao de postura ser fragil em ambientes reais
  Notas: mitigar com milestones progressivos: presenca primeiro, depois postura simples, depois eventos compostos.

- [ ] Gestos ficarem inconsistentes com pouca luz ou oclusao
  Notas: mitigar com poucos gestos no v1, feedback claro de confianca e fallback permanente para voz/UI.

## Aceite final

- [ ] Reconhecimento do dono com >95% de precisao apos calibracao
  Notas: medido localmente em sessao controlada, sem transformar isso em autenticacao total.

- [ ] Presenca detectada em <2s apos entrada no campo da camera
  Notas: inclui transicao de ausencia para presenca com webcam passiva ligada.

- [ ] Gesto reconhecido em <500ms
  Notas: considerando conjunto pequeno de gestos suportados e thresholds conservadores.

- [ ] Regra de contexto disparada em <3s apos evento visual
  Notas: do evento detectado ate a automacao/acao correspondente entrar no loop operacional.

- [ ] Zero dados de identidade fora do dispositivo
  Notas: nenhum frame, embedding ou perfil enviado para cloud no fluxo normal.

- [ ] Camera pausavel a qualquer momento sem reiniciar o Jarvez
  Notas: pausa e retomada preservam integridade do estado e nao exigem restart da sessao.

## Assuncoes registradas

- [ ] Presenca e identidade sao contexto e experiencia, nao controle de acesso
  Notas: biometria melhora o wow factor e a personalizacao, mas nao substitui policy nem autenticacao sensivel.

- [ ] Confirmacao de actions sensiveis continua obrigatoria
  Notas: rosto e voz reconhecidos nao liberam mensagens, dados privados ou codigo sem confirmacao apropriada.

- [ ] O loop de automacao existente continua sendo a base
  Notas: esta frente pluga sinais visuais em `backend/automation/` e nas actions ja existentes.

- [ ] O plano parte de processamento local only-first
  Notas: tudo que envolve camera, voz, face e gesto e desenhado para rodar localmente no dispositivo.

- [ ] O aprendizado de rotina comeca com SQLite + heuristicas
  Notas: nada de ML pesado no primeiro ciclo; primeiro consolidar eventos, preferencias e regras observaveis.

- [ ] Nada desta tarefa implementa a feature
  Notas: este arquivo e apenas o plano completo da frente de presenca, identidade e visao.
