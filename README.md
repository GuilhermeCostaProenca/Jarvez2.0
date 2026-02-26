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
- `JARVEZ_USER_ID` (id de memoria no Mem0)
- `JARVEZ_USER_NAME` (nome usado no contexto do agente)

3. Inicie o projeto:

```powershell
.\start-dev.ps1
```

Isso abre duas janelas automaticamente (backend e frontend), mas a inicializacao e feita por um unico comando.
