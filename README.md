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
