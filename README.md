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
