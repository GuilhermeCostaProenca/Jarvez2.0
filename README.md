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

## Modelo de seguranca

- Toda acao passa por policy gate no backend.
- Acoes sensiveis exigem sessao autenticada (participante atual + PIN).
- Acoes sensiveis exigem confirmacao explicita (two-step).
- `call_service` e interno e respeita allowlist de servicos.
- O token de confirmacao expira e e valido so para o mesmo participante/sala.
- Sem autenticacao, o agente deve manter respostas privadas bloqueadas.

## Troubleshooting rapido

- `Token de confirmacao invalido ou expirado`:
  gere nova confirmacao pedindo a acao novamente.
- `Home Assistant nao configurado`:
  valide `HOME_ASSISTANT_URL` e `HOME_ASSISTANT_TOKEN`.
- `Servico nao permitido`:
  adicione o servico na `HOME_ASSISTANT_ALLOWED_SERVICES` se realmente necessario.
