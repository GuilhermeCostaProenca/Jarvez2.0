# Jarvez2.0 Technical Baseline

Atualizado em 2026-03-17 apos a Fase F da migracao MCP.

## Resumo

- `backend/actions.py` ficou com `125` actions registradas.
- `20` handlers marcados como `DEPRECATED: migrated to jarvez-mcp-*` foram removidos nesta limpeza final.
- A facade restante concentra:
  - control plane local (`session`, `policy`, `orchestration`, `ops`, `automation`, `browser_agent`, `runtime`, `channels`, `actions_core`);
  - glue de roteamento MCP e fallback legacy para dominios ja integrados;
  - glue local que continua fora do escopo de extracao total (catalogo/projeto ativo, knowledge indexes, journal, approvals, estado de sessao).

## Metodo de contagem

- Contagem feita a partir das ocorrencias reais de `register_action(` em [backend/actions.py](C:/Users/guilh/OneDrive/%C3%81rea%20de%20Trabalho/Jarvez2.0/backend/actions.py) no estado atual do repositorio.
- Baseline anterior estava desatualizado porque ainda refletia o monolito antes da remocao dos wrappers migrados para MCP.

## Superficie removida da facade

Foram removidos de `backend/actions.py` os handlers e registros locais migrados para repos MCP destes dominios:

- `research`
- `desktop`
- `github`
- `projects`
- `code-actions`
- `codex`
- `workflows`

## Estado atual da facade

Os dominios extraidos continuam acessiveis no Jarvez por dois caminhos:

1. MCP routing real no backend principal, quando o recorte ja foi integrado.
2. Glue local remanescente, quando a responsabilidade continua sendo do control plane do Jarvez e nao do repo externo.

Isso significa que a limpeza final removeu wrappers duplicados do monolito sem remover:

- `_route_via_mcp(...)`
- `call_mcp_tool_with_legacy_fallback(...)`
- fallbacks legados ainda necessarios
- handlers locais que nao possuem repo externo correspondente

## Validacao desta baseline

Executado com sucesso neste estado:

- `python -m compileall backend\\actions.py`
- `python backend\\test_actions_thinq_mcp.py`
- `python backend\\test_actions_rpg_mcp.py`
- `python backend\\test_actions_whatsapp_mcp.py`
- `python backend\\test_actions_ac_mcp.py`
- `python backend\\test_mcp_substrate.py`
