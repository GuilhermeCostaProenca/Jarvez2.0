# AGENTS.md

Este arquivo orienta agentes que editem, testem ou expandam o `Jarvez2.0`.

## Objetivo do projeto

`Jarvez2.0` é um projeto unificado com:

- `backend/`: agente de voz, registry de actions, orquestração, policy, providers e integrações reais.
- `frontend/`: interface web em Next.js para a sessão do Jarvez.

O foco principal do sistema é:

- conversa por voz com actions reais;
- integrações externas (Spotify, OneNote, WhatsApp, ThinQ, Home Assistant);
- modos de personalidade e contexto;
- orquestração com subagentes e roteamento multi-model;
- policy de risco, autonomia e kill switch;
- ferramentas de busca e local knowledge;
- dashboard de pesquisa web em rota dedicada;
- modo RPG com fichas, lore e sessão gravada.

---

## Estrutura do repositório

### Backend

- `backend/agent.py`
  Entrypoint do agente LiveKit. Inicializa sessão, memória, tools e pipeline de voz.

- `backend/actions.py`
  Registry central de tools/actions. Arquivo grande e sensível — concentra specs, handlers, registro e parte do estado de sessão. **Não altere sem necessidade real.**

- `backend/prompts.py`
  Instruções de comportamento e regras de tool calling do agente. Pequenas mudanças afetam o agente inteiro.

- `backend/orchestration/`
  Orquestração de tarefas, planejamento e subagentes.
  - `router.py` — roteamento de tarefa para modelo/agente
  - `planner.py` — plano curto de execução
  - `subagents.py` — spawn, status e cancel de subagentes

- `backend/policy/`
  Engine de risco, autonomia e confiança.
  - `risk_engine.py` — tier R0–R3 por action
  - `autonomy_rules.py` — regras de autonomia por modo e domínio
  - `domain_trust.py` — trust score por domínio
  - `killswitch.py` — kill switch global e por domínio
  - `trust_drift.py` — drift entre cliente e backend

- `backend/providers/`
  Provedores de modelo com contrato unificado.
  - `provider_router.py` — roteador multi-model com fallback
  - `openai_provider.py`, `anthropic_provider.py`, `google_provider.py`

- `backend/skills/`
  Skills locais carregadas sob demanda.
  - `loader.py`, `registry.py`, `schemas.py`

- `backend/evals/`
  Suíte de avaliação e métricas operacionais.
  - `metrics_store.py`, `scenario_suite.py`

- `backend/code_worker.py`
  Serviço HTTP local para operações de código (leitura, diff, patch, comandos).

- `backend/code_knowledge.py` e `backend/rpg_knowledge.py`
  Índices locais de busca semântica.

- `backend/project_catalog.py`
  Catálogo multi-repo de projetos.

- `backend/codex_cli.py`
  Integração com Codex CLI para execução e review de tarefas.

### Frontend

- `frontend/app/`
  Rotas Next.js. Rotas dedicadas: `/orchestration`, `/research-dashboard`, `/trust-center`.

- `frontend/components/app/`
  Views principais da UI.

- `frontend/hooks/useAgentActionEvents.ts`
  Faz parse dos eventos de actions e sincroniza estado da UI. **Arquivo crítico — parse incorreto quebra tudo.**

- `frontend/lib/types/realtime.ts`
  Tipos compartilhados do fluxo de eventos entre backend e frontend.

- `frontend/lib/research-dashboard-storage.ts`
  Persistência local do dashboard de pesquisa e agendamentos.

- `frontend/lib/orchestration-storage.ts`
  Persistência local de traces, subagentes, policy events, métricas, canário e Trust Center.

---

## Repositórios de referência

Estão em `./references/`. **Consulte antes de implementar qualquer feature nova.**

| Pasta | O que é | Quando consultar |
|-------|---------|-----------------|
| `references/skills` | Skills do OpenClaw em Python | Criar ou refatorar qualquer skill |
| `references/lobster` | Motor de workflows do OpenClaw | Implementar fluxos multi-etapa ("um comando → sequência de ações") |
| `references/gerador-ficha-tormenta20` | Engine completa T20 em TypeScript | Qualquer action de RPG, fichas de jogador ou ameaça |
| `references/artonMap` | Dados geográficos de Arton | Lore e localizações do mundo T20 |
| `references/playwright-mcp` | Browser agent MCP oficial Microsoft | Browser automation, scraping, "entre no LinkedIn" |
| `references/whatsapp-mcp` | WhatsApp MCP bidirecional (Python + Go) | Melhorar integração WhatsApp, acesso de qualquer lugar |
| `references/spotify-mcp-server` | Spotify MCP leve | Referência para migrar integração Spotify atual |

**Consulta online** (não clonar, usar como catálogo):
- `https://github.com/punkpeye/awesome-mcp-servers` — lista de centenas de MCP servers prontos. Sempre consulte aqui antes de programar uma integração do zero.

---

## Fluxos críticos

### 1. Nova action no backend

Sempre que criar uma nova action:

1. Implemente o handler em `backend/actions.py` (ou no módulo de domínio se já estiver quebrado).
2. Retorne `ActionResult` consistente:
   - `success`
   - `message`
   - `data` quando necessário
   - `error` quando houver falha
   - `risk`, `policy_decision` e `evidence` para actions reais
3. Registre a action com `register_action(...)`.
4. Se o modelo precisar saber quando usar a action, atualize `backend/prompts.py`.
5. Se o frontend consumir `data`, atualize `frontend/lib/types/realtime.ts`.
6. Nunca afirme que uma ação "foi executada" sem retorno real da tool.

### 2. UI reagindo a actions

Se uma action precisa atualizar a interface:

1. O backend deve enviar os dados em `ActionResult.data`.
2. O parse acontece em `frontend/hooks/useAgentActionEvents.ts`.
3. O estado derivado deve ser tipado em `frontend/lib/types/realtime.ts`.
4. A tela deve consumir esse estado em um componente da pasta `frontend/components/app/`.

### 3. Dashboard de pesquisa web

1. O backend usa `web_search_dashboard`.
2. O retorno vem em `data.web_dashboard`.
3. O frontend salva o payload em `localStorage`.
4. O frontend tenta abrir `/research-dashboard` em nova guia.
5. A rota dedicada renderiza o compilado salvo localmente.

Observação: abertura automática de nova guia pode ser bloqueada pelo navegador; o dashboard continua acessível manualmente em `/research-dashboard`.

### 4. Nova integração externa

Antes de programar qualquer integração do zero:
1. Verifique `./references/` se já existe um MCP server de referência.
2. Verifique `https://github.com/punkpeye/awesome-mcp-servers` para MCP server público pronto.
3. Só implemente do zero se nenhuma referência existir.

---

## Comandos de desenvolvimento

### Rodar tudo

```powershell
.\setup.ps1
.\start-dev.ps1
```

### Rodar só o frontend

```powershell
cd frontend
pnpm install
pnpm dev
```

### Rodar checks no frontend

```powershell
cd frontend
pnpm lint
pnpm typecheck
pnpm build
```

### Rodar smoke test

```powershell
.\scripts\e2e-smoke.ps1
```

### Validar backend rapidamente

```powershell
python -m compileall backend\actions.py backend\prompts.py
```

---

## Convenções de código

### Backend

- Mantenha handlers pequenos e explícitos.
- Use `requests` para integrações HTTP já existentes no backend.
- Respeite o padrão de validação de parâmetros já usado em `actions.py`.
- Quando uma action for sensível, avalie `requires_confirmation=True` e `requires_auth=True`.
- Actions reais devem sempre retornar `evidence` com prova de execução.

### Frontend

- Preserve o padrão existente em React + Next.js App Router.
- Tipos novos devem entrar em `frontend/lib/types/realtime.ts`.
- Persistência local deve ficar em utilitário próprio, não espalhada em vários componentes.
- Para páginas novas, prefira criar rota dedicada em `frontend/app/`.
- Para visualização de dados longos/ricos, prefira página separada em vez de overlay sobre a sessão principal.

### UI/UX do Jarvez

- A tela principal da sessão deve permanecer limpa.
- Use rotas dedicadas para experiências extensas: dashboards, relatórios, compilados.
- Preserve o visual já existente: vidro fosco, contraste alto, bordas suaves, layout responsivo.

---

## Arquivos sensíveis

| Arquivo | Por quê é sensível |
|---------|-------------------|
| `backend/actions.py` | Muito grande e central. Mudanças afetam muitas tools. |
| `backend/prompts.py` | Pequenas alterações mudam o comportamento do agente inteiro. |
| `backend/policy/risk_engine.py` | Erros aqui podem permitir execuções fora da política. |
| `frontend/hooks/useAgentActionEvents.ts` | Parse incorreto quebra sincronização de todas as actions. |
| `frontend/components/app/session-view.tsx` | View principal — não transformar em painel lotado. |

---

## Regras de edição

- Não remova ou reverta mudanças do usuário sem pedido explícito.
- Se encontrar arquivos já modificados e fora do escopo, ignore-os.
- Se criar nova feature visual grande, prefira arquivo novo em vez de inflar componentes centrais.
- Se alterar uma estrutura de payload entre backend e frontend, atualize os dois lados na mesma tarefa.
- Não apague funcionalidades existentes sem pedido explícito.

---

## Problemas conhecidos

- `pnpm lint` do frontend pode falhar por erros pré-existentes fora do escopo da tarefa. Valide apenas os arquivos alterados.
- O Next em Windows + OneDrive pode apresentar comportamento estranho com `.next` e troca de porta (`3000` → `3001`).
- O voice runtime de voz usa Google diretamente em `agent.py` — o multi-model router não é o executor principal do turno falado ainda.
- Grande parte do estado operacional está em memória no backend e em `localStorage` no frontend.

---

## Boas práticas para futuras tarefas

- Antes de implementar, localize o fluxo real no código. Não assuma.
- Antes de mexer em UI, descubra se a experiência deveria ficar na sessão principal, numa aba nova ou numa rota dedicada.
- Para qualquer resposta "inteligente" baseada em dados externos, prefira payload estruturado em vez de só texto.
- Para features que "abrem algo na internet", pense em: conteúdo, persistência, reabertura e fallback caso popup seja bloqueado.
- Para novas integrações, sempre verifique `./references/` e `awesome-mcp-servers` antes de programar.

---

## Resumo operacional

Se você for um agente editando este projeto:

1. Leia este arquivo inteiro antes de começar.
2. Consulte `./references/` antes de implementar qualquer integração ou skill.
3. Descubra o fluxo real no código antes de alterar.
4. Faça mudanças mínimas, mas completas.
5. Atualize backend, tipos e frontend juntos quando houver novo payload.
6. Valide pelo menos os arquivos alterados.
7. Preserve a experiência principal do Jarvez sem poluir a tela de sessão.
8. Nunca afirme execução sem evidência real.