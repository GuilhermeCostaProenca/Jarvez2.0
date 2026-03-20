# Jarvez2.0 - Plano de Presenca, Identidade e Visao

## Como usar
- Marque `[x]` quando concluido
- Use `[-]` para em andamento
- Use `[ ]` para pendente
- Atualize a linha `Notas:` com contexto curto, branch, PR ou decisao

---

## Visao geral
Este ciclo cobre a frente de presenca, identidade e visao do Jarvez como um plano proprio, separado da migracao MCP e complementar ao `docs/interactivity-plan.md`. A premissa desta versao do plano mudou: biometria deixa de ser apenas contexto e passa a ser o mecanismo principal de bloqueio e desbloqueio do Jarvez.

Hoje o Jarvez ja possui base local de biometria de voz em `backend/voice_biometrics.py`, action de verificacao em `verify_voice_identity`, armazenamento local de perfis em `backend/identity/`, loop de automacao persistido em `backend/automation/`, preferencias e rotina em `backend/memory/memory_manager.py`, e actions reais de contexto em `backend/actions_domains/ac.py` e `backend/actions_domains/home_assistant.py`. O que falta agora e redesenhar essas pecas para um fluxo biometric-first: o Jarvez precisa reconhecer o dono por voz ou por rosto, desbloquear a sessao sem senha no uso normal, manter tudo local e continuar operando com baixa friccao, inclusive quando o usuario estiver falando da cama sem estar na frente da camera.

Decisoes base deste plano:
- Voz ou rosto podem desbloquear o Jarvez de forma independente; os dois juntos aumentam confianca, mas nao sao obrigatorios.
- Senha ou PIN saem do fluxo normal e ficam apenas como recuperacao de emergencia.
- O foco e conveniencia pessoal, nao seguranca maxima estilo cofres, bancos ou controle de acesso empresarial.
- Todo processamento de camera e voz fica local no dispositivo.
- O loop de automacao existente continua sendo a base; a visao entra como nova fonte de sinal e trigger, nao como motor paralelo.
- O aprendizado inicial de rotina usa SQLite, heuristicas e regras simples antes de qualquer ML pesado.
- O estado de autenticacao passa a ser explicito no backend: `locked`, `unlocked_by_voice`, `unlocked_by_face` ou `unlocked_combined`.

## Checklist Mestre

- [ ] ID. Identidade, onboarding e desbloqueio biometrico
  Notas: rebaseline em 2026-03-20. A implementacao atual ainda trata identidade como contexto; precisa migrar para auth state real sem senha no fluxo normal.

- [ ] CAM. Visao e presenca
  Notas: webcam continua como sensor passivo, mas agora tambem ajuda no relock, no liveness e na manutencao de sessao desbloqueada.

- [ ] CTX. Automacao por contexto visual
  Notas: automacao contextual continua existindo, mas passa a depender do novo estado de sessao desbloqueada quando a acao for pessoal.

- [ ] GES. Gestos de mao
  Notas: segue por ultimo; gestos continuam complementares e nao substituem o desbloqueio biometrico por voz ou rosto.

---

## Frente ID - Identidade, onboarding e desbloqueio biometrico

Contexto tecnico: o Jarvez ja tem base local reutilizavel em `backend/voice_biometrics.py`, `backend/identity/identity_store.py`, `backend/identity/speaker_id.py` e `backend/identity/face_id.py`. Hoje essa base esta orientada a reconhecimento contextual e step-up; a mudanca agora e promover essa infraestrutura para autenticacao principal da sessao. O desenho precisa aceitar dois cenarios de uso reais: desbloqueio por voz a distancia, inclusive da cama, e desbloqueio por rosto quando o usuario estiver na frente do PC. O contrato deixa de ser "quem provavelmente esta aqui?" e passa a ser "a sessao pode ser liberada agora?" com score, metodo, timestamp e relock claro.

- [ ] ID1. Redefinir o modelo de perfil local para autenticacao biometrica
  Notas: expandir `backend/data/identity/` para guardar `name`, `role`, `voice_embeddings`, `face_embeddings`, `confidence_level`, `registered_at`, `last_calibrated_at`, `preferred_unlock_modes`, `voice_unlock_threshold`, `face_unlock_threshold` e flags de recuperacao.

- [ ] ID2. Criar onboarding de voz orientado a uso real
  Notas: cadastro inicial com 5 a 10 amostras curtas, incluindo fala natural e fala a distancia; objetivo e reconhecer o usuario sem frase secreta fixa. O plano precisa aceitar refinamento progressivo do perfil so quando o score ja estiver alto.

- [ ] ID3. Promover speaker identification para voice unlock real
  Notas: `identify_speaker()` deixa de ser apenas contexto e passa a poder abrir a sessao sozinho quando ultrapassar o limiar configurado. `verify_voice_identity()` vira compatibilidade e fallback tecnico, nao o centro do fluxo.

- [ ] ID4. Promover face recognition para face unlock real
  Notas: `InsightFace` continua preferencia. O fluxo precisa reconhecer o dono sentado no desktop, manter score local e expor um caminho simples de relock quando o rosto sumir, houver troca de pessoa ou a confianca cair.

- [ ] ID5. Implementar estado de sessao bloqueada/desbloqueada
  Notas: publicar no snapshot algo como `auth_state: { status, method, name, confidence, last_verified_at }`. A memoria continua recebendo `recognized_identity`, mas autenticacao passa a morar em namespace proprio e ser checada pelas actions.

- [ ] ID6. Remover senha do fluxo normal e deixar apenas recuperacao
  Notas: o uso normal deve ser passwordless. PIN ou senha local ficam so para recalibracao, desastre de biometria, troca de microfone/camera ou lockout acidental.

- [ ] ID7. Definir relock e manutencao de sessao
  Notas: relock por ausencia prolongada, troca de voz/rosto, timeout configuravel, perda continua de confianca ou comando explicito do usuario.

- [ ] ID8. Tratar convidado como perfil reconhecivel, nao como dono
  Notas: cadastro explicito de terceiro continua existindo, mas guest nunca assume sessao do owner. Guest serve para saudacao, contexto e eventualmente sessao limitada, se isso virar requisito depois.

## Fluxo de onboarding recomendado

- [ ] ONB1. Onboarding inicial de voz do owner
  Notas: coletar 5 a 10 amostras curtas, com 20 a 40 segundos totais. Incluir fala natural, fala um pouco mais baixa, fala em tom normal e pelo menos algumas amostras simulando o uso real da cama.

- [ ] ONB2. Onboarding inicial de rosto do owner
  Notas: capturar de 10 a 20 frames validos, com pequenas variacoes de angulo, distancia e expressao. O objetivo e robustez de desktop, nao dataset grande.

- [ ] ONB3. Confirmar modo preferido de desbloqueio
  Notas: permitir `voice`, `face` ou `voice+face` como preferencia do owner, mas manter suporte a unlock independente por voz ou rosto.

- [ ] ONB4. Refinamento progressivo do perfil
  Notas: so atualizar embeddings quando o unlock ja tiver ocorrido com confianca alta. Nunca aprender a partir de tentativa duvidosa.

- [ ] ONB5. Recalibracao simples
  Notas: se o microfone, a webcam ou o ambiente mudarem, o usuario deve conseguir refazer onboarding sem apagar historico inteiro.

- [ ] ONB6. Cadastro explicito de convidado
  Notas: convidado so entra quando o owner pedir. Guest e reconhecivel, mas nao destrava a sessao do owner.

## Politica de unlock e relock

- [ ] AUTH1. Voice unlock independente
  Notas: se a voz do owner ultrapassar o limiar configurado, a sessao muda para `unlocked_by_voice` sem exigir camera naquele momento.

- [ ] AUTH2. Face unlock independente
  Notas: se o rosto do owner ultrapassar o limiar configurado, a sessao muda para `unlocked_by_face` sem exigir fala.

- [ ] AUTH3. Unlock combinado quando os dois sinais baterem
  Notas: quando voz e rosto coincidirem em janela curta, a sessao pode registrar `unlocked_combined` e elevar a confianca, mas isso nao e obrigatorio para uso diario.

- [ ] AUTH4. Relock por ausencia prolongada
  Notas: se o usuario sumir do ambiente por tempo suficiente, a sessao volta para `locked`.

- [ ] AUTH5. Relock por troca de identidade
  Notas: se outra voz ou outro rosto passarem a dominar a sessao, o sistema deve relockar antes de qualquer acao pessoal.

- [ ] AUTH6. Relock por timeout configuravel
  Notas: manter um timeout de conveniencia para evitar sessao destravada para sempre; o valor exato deve ser configuravel.

- [ ] AUTH7. Relock manual
  Notas: comando de voz, gesto ou acao explicita `lock_now` deve forcar `locked` imediatamente.

- [ ] AUTH8. Recuperacao de emergencia
  Notas: PIN, senha local ou token offline entram apenas aqui, quando a biometria falhar repetidamente ou o hardware mudar.

## Contrato de auth_state

- [ ] STATE1. Definir schema canonical de autenticacao
  Notas: persistir em namespace proprio algo como `auth_state: { status, method, profile_name, confidence, voice_confidence, face_confidence, authenticated_at, last_verified_at, relock_reason, session_id }`.

- [ ] STATE2. Separar `recognized_identity` de `auth_state`
  Notas: `recognized_identity` continua sendo contexto observacional; `auth_state` passa a ser a verdade de bloqueio/desbloqueio. Um pode existir sem o outro.

- [ ] STATE3. Definir status validos
  Notas: `locked`, `unlock_in_progress`, `unlocked_by_voice`, `unlocked_by_face`, `unlocked_combined`, `recovery_mode`. Nada fora disso no v1.

- [ ] STATE4. Definir metodos validos
  Notas: `voice`, `face`, `voice+face`, `recovery`. O metodo precisa ser sempre explicito para logs locais, UI e regras do backend.

- [ ] STATE5. Definir timestamps obrigatorios
  Notas: `authenticated_at` para a abertura da sessao atual e `last_verified_at` para a validacao mais recente durante manutencao de sessao.

- [ ] STATE6. Definir razoes de relock
  Notas: `manual_lock`, `presence_lost`, `timeout`, `identity_changed`, `confidence_dropped`, `camera_unavailable`, `microphone_unavailable`, `recovery_forced`.

## Maquina de estados recomendada

- [ ] FSM1. `locked -> unlock_in_progress`
  Notas: ocorre quando comecar tentativa valida de voice unlock ou face unlock. Evita race condition entre sinais concorrentes.

- [ ] FSM2. `unlock_in_progress -> unlocked_by_voice`
  Notas: ocorre quando a voz do owner passar o threshold de unlock antes de qualquer face match relevante.

- [ ] FSM3. `unlock_in_progress -> unlocked_by_face`
  Notas: ocorre quando o rosto do owner passar o threshold de unlock antes de qualquer voice match relevante.

- [ ] FSM4. `unlock_in_progress -> unlocked_combined`
  Notas: ocorre quando voz e rosto convergirem para o mesmo owner dentro de uma janela curta configurada.

- [ ] FSM5. `unlocked_by_voice -> unlocked_combined`
  Notas: se a camera confirmar o mesmo owner pouco depois do voice unlock, elevar confianca sem exigir novo unlock.

- [ ] FSM6. `unlocked_by_face -> unlocked_combined`
  Notas: se a voz confirmar o mesmo owner pouco depois do face unlock, elevar confianca sem exigir novo unlock.

- [ ] FSM7. `unlocked_* -> locked`
  Notas: transicao por timeout, ausencia, troca de identidade, comando explicito ou perda persistente de confianca.

- [ ] FSM8. `locked -> recovery_mode`
  Notas: so quando houver falha repetida ou indisponibilidade dos sensores e o usuario escolher recuperacao de emergencia.

## Integracao no backend

- [ ] BE1. Criar namespace proprio de auth no estado de sessao
  Notas: `backend/actions.py` deve persistir `auth_state` em namespace separado de `recognized_identity`.

- [ ] BE2. Adicionar helpers dedicados de auth
  Notas: criar helpers como `load_auth_state()`, `persist_auth_state()`, `lock_session()`, `unlock_session_by_voice()`, `unlock_session_by_face()` e `refresh_auth_state()`.

- [ ] BE3. Promover validacao de auth no dispatch
  Notas: `dispatch_action` precisa deixar de depender de senha/PIN como fluxo primario e passar a checar `auth_state.status` quando a action exigir sessao do owner.

- [ ] BE4. Preservar compatibilidade com actions existentes
  Notas: `verify_voice_identity` continua existindo, mas o caminho principal passa a ser unlock biometrico. Migracao deve evitar quebrar chamadas antigas.

- [ ] BE5. Separar actions de contexto e actions do owner
  Notas: luz, AC e ambiente podem rodar sem owner desbloqueado; actions pessoais devem exigir `auth_state` valido.

- [ ] BE6. Persistir eventos de autenticacao para calibracao local
  Notas: registrar `voice_unlock_attempted`, `voice_unlock_succeeded`, `voice_unlock_failed`, `face_unlock_attempted`, `auth_relocked` e motivos.

- [ ] BE7. Alimentar memoria sem confundir contexto e autenticacao
  Notas: `MemoryManager` pode continuar recebendo `recognized_identity`, mas o contexto privado do owner deve depender de `auth_state`.

## Integracao no snapshot e frontend

- [ ] UI1. Publicar `auth_state` no snapshot da sessao
  Notas: `backend/session_snapshot.py` deve expor `auth_state` ao lado de `recognized_identity`, nao no lugar dele.

- [ ] UI2. Tipar `auth_state` no frontend
  Notas: `frontend/lib/types/realtime.ts` precisa ganhar um tipo explicito para o contrato novo, com status, metodo, confidence e timestamps.

- [ ] UI3. Exibir estado de lock/unlock na sessao principal
  Notas: a UI deve mostrar claramente `bloqueado`, `desbloqueado por voz`, `desbloqueado por rosto` ou `modo recuperacao`, sem lotar a tela.

- [ ] UI4. Exibir motivo de relock quando relevante
  Notas: ajuda calibracao e evita sensacao de bug quando a sessao voltar para `locked`.

- [ ] UI5. Expor onboarding e recalibracao
  Notas: o usuario precisa iniciar cadastro de voz/rosto, refazer calibracao e acionar recovery sem mexer em arquivo manualmente.

- [ ] UI6. Nao misturar score bruto com UX confusa
  Notas: mostrar status simples para o usuario e manter scores detalhados mais para debug local ou tela tecnica.

## Thresholds e politica de score

- [ ] SCORE1. Adotar confidence normalizada de 0.0 a 1.0
  Notas: cada engine continua usando sua metrica interna, mas o contrato do Jarvez deve expor `confidence` normalizada para voz, rosto e combinado. A conversao de score bruto para confidence fica encapsulada no modulo de cada modalidade.

- [ ] SCORE2. Definir bandas de decisao para voz
  Notas: sugestao inicial para voice unlock: `>= 0.92` desbloqueia sozinho; `0.82 a 0.91` conta como candidato forte para combinacao; `< 0.82` nao desbloqueia. Esses valores sao ponto de partida e devem ser recalibrados por usuario.

- [ ] SCORE3. Definir bandas de decisao para rosto
  Notas: sugestao inicial para face unlock: `>= 0.90` desbloqueia sozinho; `0.80 a 0.89` conta como candidato forte para combinacao; `< 0.80` nao desbloqueia.

- [ ] SCORE4. Definir regra de combinacao de sinais
  Notas: se voz e rosto apontarem para o mesmo owner dentro de janela curta e ambos estiverem ao menos na banda de candidato, calcular `combined_confidence = 0.55 * voice_confidence + 0.45 * face_confidence`. Se `combined_confidence >= 0.86`, destravar em `unlocked_combined`.

- [ ] SCORE5. Exigir margem minima para evitar match ambiguo
  Notas: o top-1 precisa vencer o segundo melhor perfil por margem minima configuravel, por exemplo `>= 0.08` em confidence normalizada. Sem margem suficiente, manter `locked`.

- [ ] SCORE6. Rejeitar input ruim antes do matching
  Notas: audio muito curto, com clipping, com ruido extremo ou frame facial sem qualidade minima nao entram no calculo de unlock; primeiro falhar por qualidade, depois por identidade.

- [ ] SCORE7. Aprender threshold por usuario sem perder default global
  Notas: cada perfil pode guardar `voice_unlock_threshold` e `face_unlock_threshold`. O sistema nasce com defaults do produto e ajusta finamente apos onboarding e uso bem-sucedido.

- [ ] SCORE8. Nunca subir confidence por tentativa fracassada
  Notas: refinamento progressivo so usa unlocks bem-sucedidos e estaveis. Tentativa duvidosa nao treina perfil nem desloca threshold.

## Janelas de tolerancia e anti-flapping

- [ ] TOL1. Janela curta de combinacao
  Notas: voz e rosto podem se combinar em janela de 3 segundos. Fora disso, cada modalidade conta isoladamente.

- [ ] TOL2. Janela de estabilizacao logo apos unlock
  Notas: depois de desbloquear, manter uma janela de 8 a 10 segundos sem relock por oscilacao curta de score.

- [ ] TOL3. Tolerancia curta para queda momentanea de confianca
  Notas: se a confianca cair momentaneamente durante sessao ativa, aguardar 5 a 8 segundos antes de relockar. Isso evita pisca-pisca de estado.

- [ ] TOL4. Relock por ausencia visual prolongada no desktop
  Notas: se a sessao tiver sido mantida por rosto e a camera perder presenca por 2 a 3 minutos, relockar por `presence_lost`, salvo se houver voice unlock recente.

- [ ] TOL5. Timeout geral de conveniencia
  Notas: sugestao inicial de 20 a 30 minutos sem sinal confiavel do owner para voltar a `locked`, com configuracao por usuario.

- [ ] TOL6. Debounce de identidade trocada
  Notas: nao relockar na primeira anomalia; exigir repeticao curta e consistente da nova identidade antes de encerrar a sessao atual.

- [ ] TOL7. Sensor indisponivel nao deve derrubar sessao instantaneamente
  Notas: se a camera cair mas a sessao estiver valida por voz recente, manter sessao por janela curta; mesma ideia vale para microfone indisponivel em sessao mantida por rosto.

- [ ] TOL8. Relock manual sempre vence tolerancias
  Notas: `lock_now` ou comando equivalente deve ignorar grace period e relockar imediatamente.

## Matriz pratica de decisao

- [ ] DEC1. Cenario cama + voz forte
  Notas: voz reconhecida com score alto, sem camera util -> desbloquear por voz.

- [ ] DEC2. Cenario desktop + rosto forte
  Notas: rosto reconhecido com score alto, sem fala -> desbloquear por rosto.

- [ ] DEC3. Cenario desktop + voz e rosto medianos
  Notas: se ambos apontarem para o owner em janela curta, combinar sinais e destravar.

- [ ] DEC4. Cenario voz fraca e rosto ausente
  Notas: manter `locked` e pedir nova tentativa natural, sem mandar repetir senha falada.

- [ ] DEC5. Cenario rosto fraco e voz ausente
  Notas: manter `locked` e aguardar novo frame ou nova aproximacao.

- [ ] DEC6. Cenario convidado reconhecido
  Notas: registrar presenca/contexto de guest, sem assumir sessao do owner.

- [ ] DEC7. Cenario perda de confianca durante sessao
  Notas: iniciar janela curta de tolerancia; se a perda persistir, relock.

- [ ] DEC8. Cenario biometria indisponivel
  Notas: usar somente recuperacao de emergencia, nunca voltar a senha como fluxo principal.

## Regras praticas de decisao

- [ ] RULE1. Voz forte vence ausencia de camera
  Notas: se o contexto indicar uso a distancia e a voz passar o threshold forte, desbloquear sem esperar rosto.

- [ ] RULE2. Rosto forte vence ausencia de fala
  Notas: se o usuario estiver no desktop e o rosto passar o threshold forte, desbloquear sem pedir comando falado.

- [ ] RULE3. Dois sinais medianos podem vencer juntos
  Notas: sinais medianos do mesmo owner nao bastam isoladamente, mas podem destravar via combinacao dentro da janela prevista.

- [ ] RULE4. Sinal forte com identidade ambigua nao desbloqueia
  Notas: confidence alta sem margem suficiente para o segundo melhor perfil continua sendo ambigua e deve falhar.

- [ ] RULE5. Guest nunca faz unlock do owner
  Notas: mesmo com score alto para guest, a sessao do owner nao deve abrir.

- [ ] RULE6. Recovery nao recalibra automaticamente
  Notas: entrar por modo de recuperacao nao deve treinar biometria nem alterar thresholds ate o usuario validar isso explicitamente.

## UX operacional recomendada

- [ ] UX1. Sessao principal deve mostrar lock state de forma discreta
  Notas: exibir apenas um chip compacto como `Bloqueado`, `Desbloqueado por voz`, `Desbloqueado por rosto` ou `Recuperacao`, sem transformar a tela principal em painel tecnico.

- [ ] UX2. Falha de unlock deve pedir nova tentativa natural
  Notas: evitar UX de "senha falhou". Respostas esperadas: `Nao reconheci sua voz com confianca suficiente. Tenta falar de novo.` ou `Nao consegui confirmar seu rosto agora. Tenta se aproximar um pouco.`

- [ ] UX3. Feedback deve citar modalidade usada
  Notas: quando destravar, informar `Sessao desbloqueada por voz` ou `Sessao desbloqueada por rosto` para deixar claro o que funcionou.

- [ ] UX4. Recovery precisa ser raro, mas claro
  Notas: se biometria falhar repetidamente, o sistema deve oferecer `modo de recuperacao` com linguagem direta, sem voltar a tratar senha como fluxo normal.

- [ ] UX5. Recalibracao deve existir na UI
  Notas: o usuario precisa conseguir refazer cadastro de voz, rosto ou ambos sem mexer em arquivo e sem apagar o perfil inteiro por acidente.

- [ ] UX6. Guest deve ser apresentado como contexto, nao como sessao ativa
  Notas: exemplo de retorno: `Reconheci Joao como convidado`, sem alterar o estado de unlock do owner.

- [ ] UX7. Lock manual precisa ser facil
  Notas: comando falado, gesto opcional e controle visual simples para travar na hora.

- [ ] UX8. Scores detalhados ficam fora da UX principal
  Notas: percentuais, margem de match e detalhes tecnicos devem ir para tela tecnica, debug local ou logs, nao para a sessao principal.

## Fluxo de onboarding na pratica

- [ ] FLOW1. Entrada no modo de cadastro
  Notas: o owner inicia explicitamente algo como `cadastrar minha voz`, `calibrar meu rosto` ou `refazer biometria`.

- [ ] FLOW2. Cadastro guiado de voz em etapas curtas
  Notas: o Jarvez conduz o usuario por 5 a 10 falas curtas, com instrucoes simples e sem frases secretas fixas. O ideal e variar distancia, volume e naturalidade.

- [ ] FLOW3. Cadastro guiado de rosto em etapas curtas
  Notas: o Jarvez pede pequenas variacoes de angulo e distancia, captura apenas frames validos e mostra progresso simples.

- [ ] FLOW4. Confirmacao do perfil criado
  Notas: ao fim do onboarding, mostrar quais modalidades ficaram prontas: `voz`, `rosto` ou `voz e rosto`.

- [ ] FLOW5. Teste imediato de unlock
  Notas: logo depois do onboarding, o sistema deve rodar um teste rapido real de desbloqueio para validar se a calibracao ficou boa.

- [ ] FLOW6. Ajuste de preferencia por contexto de uso
  Notas: o owner pode marcar coisas como `uso voz da cama`, `uso rosto no desktop`, `quero relock mais rapido` ou `prefiro sessao mais longa`.

- [ ] FLOW7. Reonboarding parcial
  Notas: o usuario pode recalibrar so voz ou so rosto, sem refazer tudo.

- [ ] FLOW8. Guest onboarding separado
  Notas: cadastro de guest sempre deixa claro que isso nao cria sessao do owner nem muda preferencia de unlock.

## Fluxo de falha e recovery

- [ ] REC1. Falha simples gera nova tentativa, nao recovery imediato
  Notas: uma ou duas falhas seguidas devem apenas pedir nova tentativa natural.

- [ ] REC2. Falha repetida oferece recovery
  Notas: depois de N falhas consecutivas configuraveis, oferecer `modo de recuperacao` em vez de repetir a mesma mensagem para sempre.

- [ ] REC3. Recovery deve ser local e temporario
  Notas: entrar por recovery so libera a sessao atual ou a recalibracao imediata; nao deve reconfigurar o sistema sozinho.

- [ ] REC4. Recovery deve permitir reonboarding
  Notas: se o problema for hardware novo, ruido, webcam ruim ou mudanca de ambiente, o fluxo deve encaminhar direto para recalibracao.

- [ ] REC5. Recovery nao deve aprender biometria em silencio
  Notas: nenhuma amostra coletada no recovery entra no perfil automaticamente sem confirmacao explicita do owner.

- [ ] REC6. Logs locais devem registrar motivo da falha
  Notas: diferenciar `qualidade ruim`, `nao reconhecido`, `match ambiguo`, `sensor indisponivel` e `threshold insuficiente` para ajudar calibracao posterior.

## UX de snapshot e frontend

- [ ] VIEW1. Snapshot deve carregar estado simples e suficiente
  Notas: `auth_state`, `recognized_identity`, `relock_reason`, `last_verified_at` e `recovery_available` bastam para a UI principal.

- [ ] VIEW2. Frontend deve refletir transicoes sem flicker
  Notas: grace periods e anti-flapping precisam existir tambem na renderizacao, para nao alternar `Bloqueado/Desbloqueado` visualmente a cada oscilacao curta.

- [ ] VIEW3. Sessao bloqueada precisa continuar util
  Notas: mesmo em `locked`, o Jarvez pode ouvir, responder de forma limitada e orientar o usuario a desbloquear, sem parecer quebrado.

- [ ] VIEW4. Sessao desbloqueada precisa parecer continua
  Notas: uma vez em `unlocked_by_voice` ou `unlocked_by_face`, a interface deve passar sensacao de continuidade ate haver relock de verdade.

- [ ] VIEW5. Recovery precisa ter CTA claro
  Notas: se `recovery_mode` estiver disponivel, a UI deve mostrar uma acao clara para seguir com recuperacao ou recalibracao.

- [ ] VIEW6. Tela tecnica separada para tuning
  Notas: thresholds, scores por modalidade, historico de falhas e logs de relock devem ficar em rota separada ou painel tecnico, nao na sessao principal.

## Frente CAM - Visao e presenca

Contexto tecnico: a webcam continua sendo um sensor passivo e local. A diferenca nesta versao do plano e que a camera nao serve apenas para contexto e automacao; ela tambem ajuda a sustentar a camada de autenticacao quando a sessao estiver desbloqueada por rosto. O caminho de menor risco segue sendo `OpenCV` para captura, background subtraction e heuristicas de movimento, combinado com `MediaPipe` para pose e landmarks quando houver pessoa em frame. Numa RTX 3050 6GB, o objetivo continua sendo pipeline leve e sempre ligado, sem classificador pesado rodando em todo frame.

- [ ] CAM1. Manter pipeline passivo de camera com estados claros
  Notas: `running`, `paused`, `camera_unavailable`, `face_unlock_ready`; o pipeline precisa sobreviver a falhas e reabrir a webcam sem reiniciar o Jarvez.

- [ ] CAM2. Detectar presenca e ausencia para relock automatico
  Notas: se o usuario sumir do campo da camera por tempo suficiente, a sessao deve poder voltar para `locked`, exceto quando tiver sido desbloqueada recentemente por voz e a ausencia visual nao for relevante.

- [ ] CAM3. Detectar postura e aproximacao ao desktop
  Notas: postura nao autentica sozinha, mas ajuda a entender se o usuario esta na mesa, na cama, chegando ou saindo, o que afeta quando tentar face unlock e quando manter o estado desbloqueado.

- [ ] CAM4. Adicionar liveness leve para rosto
  Notas: como o foco e conveniencia, nao precisa virar hardware-grade; ainda assim o plano deve prever heuristicas simples como sequencia de frames coerente, mudanca angular minima e rejeicao de frame estatico obvio.

- [ ] CAM5. Persistir eventos visuais estruturados, nao frames
  Notas: eventos como `presence_detected`, `left_room`, `approached_pc`, `face_unlock_attempted`, `face_unlock_succeeded`, `face_unlock_failed` ficam em SQLite para auditoria local e ajuste de thresholds.

- [ ] CAM6. Preservar privacidade e controle do sensor
  Notas: pause da camera precisa continuar imediato; nenhum frame bruto persiste; embeddings e eventos ficam locais.

## Frente CTX - Automacao por contexto visual

Contexto tecnico: o Jarvez ja possui o substrato desta frente em `backend/automation/rules.py`, `scheduler.py`, `triggers.py` e `executor.py`, alem das actions reais em `backend/actions_domains/ac.py` e `backend/actions_domains/home_assistant.py`. A mudanca aqui e que automacao visual passa a conversar com um auth state real. O sistema pode continuar ligando luz, AC e modos contextuais com baixa friccao, mas agora consegue distinguir melhor "o dono acabou de desbloquear por voz" de "tem qualquer pessoa no quarto".

- [ ] CTX1. Conectar eventos visuais e biometricos ao loop atual
  Notas: adicionar eventos do tipo `voice_unlock_succeeded`, `face_unlock_succeeded`, `auth_relocked`, `presence_lost` sem criar motor paralelo.

- [ ] CTX2. Separar automacao pessoal de automacao ambiente
  Notas: luz, AC e ambiente podem reagir a presenca; acoes ligadas ao dono ou ao seu contexto pessoal devem checar sessao desbloqueada.

- [ ] CTX3. Reaproveitar preferencias e rotina existentes
  Notas: `backend/memory/memory_manager.py` e o store atual seguem como base para preferencias de chegada, modo RPG, horario e padroes observados.

- [ ] CTX4. Usar voice unlock como sinal forte de "sou eu"
  Notas: se o usuario desbloquear por voz da cama, isso ja pode destravar automacoes pessoais permitidas, sem depender da camera naquele momento.

- [ ] CTX5. Continuar sugerindo regras antes de ampliar autonomia
  Notas: aprendizado progressivo continua em SQLite + heuristicas; primeiro sugerir, depois automatizar.

- [ ] CTX6. Manter fronteira de risco pragmatica
  Notas: como o usuario explicitou baixa sensibilidade, o plano pode reduzir friccao depois do unlock, mas ainda precisa prever kill switch, relock e logs locais para evitar comportamento errado persistente.

## Frente GES - Gestos de mao

Contexto tecnico: esta frente continua dependente de camera estavel e landmarks prontos. Ela permanece complementar: gestos nao substituem voz ou rosto como mecanismo principal de unlock, mas podem servir para atalho de acoes, cancelamento global ou relock manual. `MediaPipe Hands` continua sendo a opcao mais pragmatica para v1.

- [ ] GES1. Manter contrato configuravel de gesto -> acao
  Notas: mapa simples, extensivel e carregado de preferencias do usuario.

- [ ] GES2. Preservar conjunto inicial de poucos gestos confiaveis
  Notas: aceno, mao aberta e punho continuam suficientes para v1.

- [ ] GES3. Adicionar gesto de lock ou cancelamento forte
  Notas: um gesto simples pode servir como `lock_now` ou `cancel_all`, principalmente quando o usuario estiver no escritorio.

- [ ] GES4. Reaproveitar o mesmo pipeline da camera
  Notas: nenhuma segunda captura paralela; gestos usam o frame que a Frente CAM ja estiver processando.

- [ ] GES5. Deixar base pronta para expansao futura
  Notas: gestos novos entram como configuracao, nao como reescrita do engine.

---

## Stack tecnico recomendado

- [ ] Voz. `resemblyzer` como trilha principal de voice unlock
  Notas: leve, local e adequada para iterar rapidamente sobre embeddings e comparacao de similaridade em uso continuo.

- [ ] Voz fallback. infraestrutura existente em `backend/voice_biometrics.py`
  Notas: reutilizar o buffer atual e a logica ja presente enquanto o unlock por voz real amadurece.

- [ ] Voz avancada. `pyannote.audio` como trilha futura
  Notas: considerar so se diarizacao, multiplos falantes ou pipeline muito mais robusto realmente virarem requisito.

- [ ] Face. `InsightFace` como motor principal
  Notas: melhor equilibrio entre deteccao e embedding facial para uso local na RTX 3050 6GB.

- [ ] Face fallback. `face_recognition` ou `dlib`
  Notas: manter como fallback tecnico, nao como alvo principal.

- [ ] Visao e gesto. `MediaPipe`
  Notas: continua sendo a base leve para pose, hands e sinais estruturados de postura/movimento.

- [ ] Presenca e movimento. `OpenCV`
  Notas: primeira linha do pipeline sempre ligado, reduzindo custo dos estagios mais caros.

- [ ] Rotina e aprendizado. SQLite + heuristicas
  Notas: eventos e ajustes de threshold primeiro; ML pesado depois, se realmente precisar.

- [ ] Justificativa RTX 3050 6GB
  Notas: suficiente para embeddings e inferencia local, mas o v1 continua melhor com pipeline leve, sampling e uso seletivo de estagios mais caros.

## Politica de privacidade local

- [ ] Todo processamento de camera e voz e local
  Notas: nenhum reconhecimento depende de cloud no fluxo normal.

- [ ] Nenhuma imagem, frame bruto ou embedding sai do dispositivo
  Notas: apenas eventos estruturados, scores e metadados locais.

- [ ] Camera pausavel a qualquer momento
  Notas: pausa precisa continuar sem reiniciar o Jarvez.

- [ ] Dados de identidade ficam em `backend/data/identity/`
  Notas: fora do Git, com ownership local e sem replicacao externa.

- [ ] Voz e rosto viram chave de desbloqueio local
  Notas: o plano assume conveniencia-first para uso pessoal, nao conformidade enterprise.

- [ ] Recuperacao de emergencia continua local
  Notas: PIN, senha ou token de recuperacao ficam so para desastre, nunca como fluxo normal.

## Dependencias entre frentes

- [ ] ID antes de CTX
  Notas: automacao pessoal depende do novo auth state.

- [ ] CAM antes de GES
  Notas: gestos continuam dependentes de camera estavel.

- [ ] CAM antes de face unlock robusto
  Notas: sem pipeline de camera confiavel, face unlock nao sustenta uso diario.

- [ ] ID e CAM antes do relock inteligente
  Notas: relock por ausencia ou troca de pessoa depende dos dois sinais.

- [ ] CTX depois de ID e CAM
  Notas: primeiro liberar/desbloquear bem; depois automatizar em cima disso.

## Ordem de execucao recomendada

- [ ] 1. Rebaseline da Frente ID
  Notas: mover o sistema de identidade de contexto para autenticacao real sem senha no fluxo normal.

- [ ] 2. Ajustes da Frente CAM para relock e liveness leve
  Notas: camera passa a sustentar face unlock e manutencao da sessao.

- [ ] 3. Integracao da Frente CTX com auth state
  Notas: automacao visual passa a distinguir presenca qualquer de sessao do dono desbloqueada.

- [ ] 4. Frente GES
  Notas: fica por ultimo porque nao bloqueia o unlock principal.

## Fases de implementacao recomendadas

- [ ] F1. Promover a Frente ID de contexto para auth state real
  Notas: criar `auth_state`, unlock por voz, unlock por rosto, relock e recuperacao de emergencia. Esta e a fase critica do redesenho.

- [ ] F2. Ajustar camera e eventos visuais para sustentar face unlock
  Notas: garantir pipeline estavel, liveness leve, eventos de ausencia e logs locais suficientes para calibracao.

- [ ] F3. Integrar auth state com actions, memoria e snapshot
  Notas: actions passam a ler `auth_state`; memoria continua recebendo `recognized_identity`; frontend passa a exibir sessao bloqueada/desbloqueada.

- [ ] F4. Reencaixar automacao contextual no modelo novo
  Notas: diferenciar automacao de ambiente de automacao pessoal baseada em owner desbloqueado.

- [ ] F5. Refinar UX e calibracao
  Notas: ajustar thresholds, mensagens, fallback de emergencia e experiencia de onboarding depois que o unlock principal estiver funcional.

## Implementacao Fase 1

Objetivo da Fase 1: sair do modelo atual de identidade apenas contextual e chegar a um primeiro fluxo passwordless funcional para uso diario, com unlock por voz ou por rosto, auth state real, relock basico e recovery local.

- [ ] P1. Backend: introduzir `auth_state` real
  Notas: criar namespace proprio, helpers dedicados e schema canonical em `backend/actions.py`, `backend/session_snapshot.py` e `backend/memory/memory_manager.py`.

- [ ] P2. Backend: voice unlock funcional
  Notas: promover `backend/identity/speaker_id.py` para unlock real com threshold por perfil, onboarding de voz, logs de tentativa e transicao para `unlocked_by_voice`.

- [ ] P3. Backend: face unlock funcional
  Notas: promover `backend/identity/face_id.py` para unlock real com threshold por perfil, liveness leve e transicao para `unlocked_by_face`.

- [ ] P4. Backend: relock e recovery
  Notas: implementar relock por timeout, ausencia, identidade trocada e comando manual; adicionar `recovery_mode` com fluxo local sem virar caminho normal.

- [ ] P5. Backend: separar actions de ambiente e actions do owner
  Notas: `dispatch_action` passa a usar `auth_state` para actions pessoais, mantendo acoes de ambiente disponiveis sem unlock.

- [ ] P6. Frontend: refletir lock state sem poluir a sessao
  Notas: adicionar tipo de `auth_state`, chip visual discreto, feedback de desbloqueio e CTA de recovery/recalibracao.

- [ ] P7. Onboarding: fluxo guiado de voz e rosto
  Notas: expor actions ou UI para cadastrar, testar e recalibrar voz/rosto sem mexer em arquivos manuais.

- [ ] P8. Telemetria local: tentativas, falhas e relocks
  Notas: persistir eventos suficientes para tuning local sem vazar biometria nem salvar frame bruto.

Escopo da Fase 1:
- unlock por voz sozinho
- unlock por rosto sozinho
- `auth_state` no snapshot
- relock basico
- recovery local
- onboarding inicial funcional

Fora do escopo da Fase 1:
- gestos como parte do unlock
- automacao contextual baseada em auth state
- calibracao automatica muito avancada
- diarizacao, multiplos owners e politicas complexas por pessoa
- hardening tipo hardware dedicado

Criterios de aceite da Fase 1:
- o owner consegue desbloquear por voz da cama sem senha
- o owner consegue desbloquear por rosto no desktop sem senha
- a sessao expõe `locked`, `unlocked_by_voice`, `unlocked_by_face` e `recovery_mode`
- actions pessoais passam a respeitar `auth_state`
- actions de ambiente continuam fluindo sem friccao desnecessaria
- relock manual e automatico funcionam
- recovery local permite retomar o controle e recalibrar

## Riscos abertos

- [ ] Voice unlock falhar quando o usuario estiver deitado ou falando baixo
  Notas: mitigar com onboarding que inclua fala natural a distancia, ajuste de threshold por ambiente e refinamento progressivo do perfil.

- [ ] Face unlock ser inconsistente com webcam comum
  Notas: mitigar com boas condicoes de iluminacao, tolerancia calibrada, liveness leve e fallback natural para voz.

- [ ] A experiencia ficar pior que a senha se o relock for agressivo demais
  Notas: mitigar com timeout pragmatico, janela de tolerancia e configuracao de sessao.

- [ ] Falso positivo biometrico
  Notas: aceitavel em nivel pessoal ate certo ponto, mas precisa de thresholds calibrados, logs locais e recuperacao de emergencia.

- [ ] Mudanca de microfone, camera ou ambiente derrubar a calibracao
  Notas: mitigar com fluxo simples de recalibracao e suporte a multiplas amostras por perfil.

- [ ] O repo atual ainda refletir a premissa antiga
  Notas: a implementacao existente de identidade contextual precisa ser refeita para alinhar com este plano.

## Aceite final

- [ ] Voice unlock do dono funcionar com >95% de acerto apos calibracao
  Notas: medido com fala natural, incluindo cenario de cama e distancia maior do microfone.

- [ ] Face unlock do dono funcionar com >95% de acerto no desktop apos calibracao
  Notas: medido com webcam comum e iluminacao razoavel.

- [ ] Unlock ocorrer em <2s apos fala valida ou match facial valido
  Notas: o objetivo e parecer imediato no uso normal.

- [ ] Sessao mudar de `locked` para `unlocked_by_voice` ou `unlocked_by_face` sem senha
  Notas: senha fica fora do fluxo comum.

- [ ] Relock acontecer automaticamente em cenarios configurados
  Notas: ausencia prolongada, perda consistente de presenca ou comando explicito.

- [ ] Zero dados biometricos fora do dispositivo
  Notas: perfis, embeddings e eventos ficam locais.

## Assuncoes registradas

- [ ] O Jarvez vai operar em modo biometric-first
  Notas: voz ou rosto sao o caminho principal de desbloqueio.

- [ ] Voz ou rosto podem desbloquear sozinhos
  Notas: nao existe obrigatoriedade de combinar os dois em cada unlock.

- [ ] Senha e recuperacao, nao fluxo normal
  Notas: o usuario explicitou que nao quer depender dela no dia a dia.

- [ ] O foco e conveniencia pessoal
  Notas: o objetivo nao e competir com hardware dedicado de fabricantes como Apple em termos de seguranca absoluta.

- [ ] O loop de automacao existente continua sendo a base
  Notas: o auth state novo entra no backend atual; nao cria um segundo sistema.

- [ ] Nada desta tarefa implementa a mudanca
  Notas: este arquivo rebaselineia o plano; a implementacao precisa vir depois.
