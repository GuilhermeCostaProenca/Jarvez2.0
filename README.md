# Jarvez2.0

Projeto unificado do Jarvez com:

- `backend/`: agente de voz (LiveKit + Google + Mem0)
- `frontend/`: interface web (Next.js)

## Rodar tudo (comando unico)

1. Execute setup (uma vez):

```powershell
.\setup.ps1
```

2. Preencha variaveis:
- `backend/.env`
- `frontend/.env.local`

No `backend/.env`, personalize:
- `JARVEZ_USER_NAME` (nome exibido no contexto do agente)

Observacao:
- O `user_id` da memoria agora e automatico por participante da sessao (LiveKit identity).
- Se nao houver identidade disponivel, o backend usa fallback `anon-{room}-{random}`.

3. Inicie o projeto:

```powershell
.\start-dev.ps1
```

Isso abre duas janelas automaticamente (backend e frontend), mas a inicializacao e feita por um unico comando.

## Acoes reais com Home Assistant

Configure no `backend/.env`:

- `HOME_ASSISTANT_URL` (ex: `http://192.168.1.10:8123`)
- `HOME_ASSISTANT_TOKEN` (long-lived access token)
- `HOME_ASSISTANT_ALLOWED_SERVICES` (padrao: `light.turn_on,light.turn_off`)
- `ACTION_CONFIRMATION_TTL_SECONDS` (padrao: `60`)
- `HOME_ASSISTANT_TIMEOUT_SECONDS` (padrao: `5`)
- `HOME_ASSISTANT_RETRY_COUNT` (padrao: `2`)
- `JARVEZ_SECURITY_PIN` (obrigatorio para liberar modo privado)
- `JARVEZ_SECURITY_PASSPHRASE` (opcional, segundo segredo)
- `JARVEZ_SECURE_SESSION_TTL_SECONDS` (padrao: `600`)
- `JARVEZ_SECURE_IDLE_LOCK_SECONDS` (padrao: `300`)
- `JARVEZ_VOICE_BIOMETRY_ENABLED` (padrao: `1`)
- `JARVEZ_VOICE_MATCH_THRESHOLD` (padrao: `0.78`)
- `JARVEZ_VOICE_REQUIRE_STEPUP_BELOW` (padrao: `0.85`)
- `JARVEZ_VOICE_PROFILE_KEY` (obrigatorio para armazenar perfis criptografados)
- `JARVEZ_VOICE_PROFILES_PATH` (padrao: `data/voice_profiles.enc`)
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `SPOTIFY_REDIRECT_URI` (ex: `http://127.0.0.1:3001/api/spotify/callback`)
- `SPOTIFY_TOKENS_PATH` (padrao: `data/spotify_tokens.json`)
- `SPOTIFY_DEFAULT_DEVICE_NAME` (ex: `Alexa`)
- `ONENOTE_CLIENT_ID`
- `ONENOTE_CLIENT_SECRET`
- `ONENOTE_REDIRECT_URI` (ex: `http://127.0.0.1:3001/api/onenote/callback`)
- `ONENOTE_SCOPES` (padrao: `offline_access User.Read Notes.ReadWrite`)
- `ONENOTE_TOKENS_PATH` (padrao: `data/onenote_tokens.json`)
- `WHATSAPP_ACCESS_TOKEN` (Cloud API token)
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_VERIFY_TOKEN`
- `WHATSAPP_APP_SECRET` (opcional, recomendado para validar assinatura)
- `WHATSAPP_GRAPH_VERSION` (padrao: `v22.0`)
- `WHATSAPP_INBOX_PATH` (padrao: `data/whatsapp_inbox.json`)
- `WHATSAPP_DEFAULT_COUNTRY_CODE` (padrao: `55`)
- `JARVEZ_TTS_VOICE` (padrao: `pt-BR-AntonioNeural`)
- `RPG_SOURCE_PATHS` (lista separada por `;` com pastas/arquivos de RPG)
- `RPG_KNOWLEDGE_DB_PATH` (padrao: `data/rpg_knowledge.db`)
- `RPG_NOTES_DIR` (padrao: `data/rpg_notes`)
- `RPG_SESSION_LOGS_DIR` (padrao: `data/rpg_sessions`)
- `RPG_CHARACTERS_DIR` (padrao: `data/rpg_characters`)
- `RPG_CHARACTER_TEMPLATE_PDFS` (pdfs de ficha/regras para referencia)

Exemplos de `entity_id`:

- `light.sala`
- `light.quarto`
- `light.escritorio`

Comandos de voz suportados (MVP):

- \"Ligue a luz da sala\"
- \"Desligue a luz do quarto\"
- \"Defina o brilho da luz da sala para 120\"
- \"Sim, confirmo\" (para executar a acao sensivel pendente)
- \"Autenticar: meu PIN e 1234\" (libera sessao privada)
- \"Bloquear modo privado\" (encerra autenticacao)
- \"Cadastre minha voz como Guilherme\" (enroll_voice_profile)
- \"Verifique minha identidade por voz\" (verify_voice_identity)
- \"Liste os perfis de voz\" / \"Apague o perfil Guilherme\"
- \"Salva isso como segredo\" / \"Salva isso como publico\"
- \"Esquece esse segredo: <termo>\"
- \"Conecte meu Spotify\" (abre login OAuth)
- \"Toca Blinding Lights na Alexa\"
- \"Pausa a musica\" / \"Proxima faixa\"
- \"Volume do Spotify para 35%\"
- \"Monta uma playlist surpresa pra mim\"
- \"Conecte meu OneNote\" (abre login OAuth)
- \"Liste minhas secoes do OneNote\"
- \"Busca no OneNote por personagem: <nome>\"
- \"Crie uma pagina de personagem no OneNote\"
- \"Adicione esta anotacao na pagina <id> do OneNote\"
- \"Ler minhas mensagens do WhatsApp\"
- \"Mandar mensagem no WhatsApp para <numero>: <texto>\"
- \"Mandar audio no WhatsApp para <numero>: <texto>\"
- \"Jarvez modo hetero top\"
- \"Jarvez modo mona\"
- \"Jarvez modo rpg\"
- \"Jarvez volta para o modo normal\"
- \"Jarvez, procura nas regras de Tormenta: como funciona X?\"
- \"Jarvez, o que a lore diz sobre Y em Game of Thrones?\"
- \"Jarvez, salva isso no lore de RPG: ...\"
- \"Jarvez, cria personagem rapido: nome X, classe Y, raca Z\"
- \"Jarvez, gravar sessao\" / \"Jarvez, parar gravacao da sessao\"
- \"Jarvez, faz resumo da sessao e salva em arquivo\"
- \"Jarvez, me da ideias para a proxima sessao\"

Importante para biometria:
- Fale de 2 a 4 segundos antes de pedir `enroll_voice_profile` ou `verify_voice_identity`.
- O score de voz e calculado a partir de embedding acustico do audio recente (microfone), nao por identity hash.

## Modelo de seguranca

- Toda acao passa por policy gate no backend.
- Acoes sensiveis exigem sessao autenticada.
- Biometria de voz funciona como fator adicional; confianca media/baixa exige step-up com PIN/frase.
- Acoes sensiveis exigem confirmacao explicita (two-step).
- `call_service` e interno e respeita allowlist de servicos.
- O token de confirmacao expira e e valido so para o mesmo participante/sala.
- Sem autenticacao, o agente deve manter respostas privadas bloqueadas.

## Memoria com escopo

- A memoria agora e separada em `public` e `private`.
- Conteudo sensivel e salvo como `private` por padrao.
- O agente tambem pergunta quando detectar conteudo pessoal:
  - "Quer que eu trate isso como segredo (privado) ou publico?"
- Sem autenticacao ativa, apenas memoria `public` e considerada.
- Apos autenticar, o agente pode carregar memoria `private` da mesma identidade.
- Comandos explicitos de soberania: salvar como secreto/publico e esquecer memoria por termo.

## Awareness leve (frontend)

- Detecta contexto local no navegador: `coding`, `study`, `video`, `browsing`, `idle`.
- Proatividade com cooldown anti-spam (mensagens curtas).
- Botao de `Modo silencioso` para pausar proatividade.

## Troubleshooting rapido

- `Token de confirmacao invalido ou expirado`:
  gere nova confirmacao pedindo a acao novamente.
- `Home Assistant nao configurado`:
  valide `HOME_ASSISTANT_URL` e `HOME_ASSISTANT_TOKEN`.
- `Servico nao permitido`:
  adicione o servico na `HOME_ASSISTANT_ALLOWED_SERVICES` se realmente necessario.
- `Nao detectei audio suficiente`:
  fale por alguns segundos e repita o comando de biometria.
- `Spotify nao autenticado`:
  clique em `Conectar Spotify` no app ou abra `http://127.0.0.1:3001/api/spotify/login`.
- `OneNote nao autenticado`:
  clique em `Conectar OneNote` no app ou abra `http://127.0.0.1:3001/api/onenote/login`.
- `Alexa nao aparece como device`:
  abra o app Spotify, confirme que a Alexa esta online no Spotify Connect e tente `spotify_get_devices`.
- `WhatsApp webhook nao valida`:
  confira se `WHATSAPP_VERIFY_TOKEN` no Meta Developer e no `.env` sao iguais.
- `WhatsApp nao envia mensagem`:
  valide `WHATSAPP_ACCESS_TOKEN` e `WHATSAPP_PHONE_NUMBER_ID`.
- `Audio TTS falhou`:
  confira conectividade e tente texto menor para o `whatsapp_send_audio_tts`.

## Configuracao WhatsApp Cloud API

1. No Meta Developer, configure webhook:
   - Callback URL: `http://127.0.0.1:3001/api/whatsapp/webhook`
   - Verify token: valor de `WHATSAPP_VERIFY_TOKEN`
2. Assine eventos de mensagens (`messages`).
3. Defina no backend:
   - `WHATSAPP_ACCESS_TOKEN`
   - `WHATSAPP_PHONE_NUMBER_ID`
4. O inbox recebido fica salvo em `backend/data/whatsapp_inbox.json`.

## Modos de personalidade

Modos disponiveis:
- `default` (classico)
- `faria_lima` (alias por voz: `hetero top`)
- `mona`
- `rpg`

Comandos por voz:
- \"Jarvez modo hetero top\"
- \"Jarvez modo mona\"
- \"Jarvez modo rpg\"
- \"Jarvez modo normal\"

Ao trocar o modo:
- o estilo de resposta muda na sessao atual;
- o circulo visual do app muda de cor conforme o modo.

## Base de conhecimento RPG (PDF/Lore)

Para indexar PDFs/textos de RPG:

```powershell
cd backend
.\.venv\Scripts\python.exe ingest_rpg_knowledge.py
```

No runtime do Jarvez:
- use `rpg_search_knowledge` para responder regras/historia com base nos documentos indexados;
- use `rpg_save_lore_note` para salvar novas informacoes e reindexar automaticamente;
- use `rpg_reindex_sources` para atualizar toda a base quando adicionar novos arquivos.
- use `rpg_create_character_sheet` para gerar ficha rapida em markdown/json.
- use `rpg_session_recording` para iniciar/parar/status da gravacao da sessao.
- use `rpg_write_session_summary` para criar resumo em arquivo da ultima sessao.
- use `rpg_ideate_next_session` para criar ideias da proxima sessao com base no historico.

## Smoke test de aceite (E2E)

Executar:

```powershell
.\scripts\e2e-smoke.ps1
```

Esse script valida compile/test no backend, `npm run check` no frontend e imprime a checklist manual final de aceite.
