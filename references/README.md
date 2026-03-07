# references/

Repositórios de referência do Jarvez. **Não são dependências do projeto — são fontes de padrão, dados e arquitetura.**

Consulte antes de implementar qualquer feature nova. Nunca copie código diretamente sem adaptar ao contexto do Jarvez.

---

## Arquitetura e Skills

### `skills/` — openclaw/skills
Skills do OpenClaw em Python.

**Quando consultar:** sempre que for criar ou refatorar uma skill no Jarvez. Aqui está o padrão de como uma skill é estruturada, declarada e exposta ao agente.

### `lobster/` — openclaw/lobster
Motor de workflows do OpenClaw. Sistema de pipelines tipados que transforma skills e tools em automações compostas executadas com um único comando.

**Quando consultar:** ao implementar fluxos multi-etapa. Exemplo: "modo RPG" abrindo Spotify + OneNote + carregando lore + mudando persona em sequência.

---

## RPG / Tormenta 20

### `gerador-ficha-tormenta20/` — YuriAlessandro/gerador-ficha-tormenta20
Engine completa de Tormenta 20 em TypeScript. Contém dados e lógica de geração para:
- fichas de jogador (todas as classes, raças, poderes, magias, itens iniciais)
- fichas de ameaça
- recompensas
- regras do sistema T20

**Quando consultar:** qualquer action de RPG no Jarvez — `rpg_create_character_sheet`, `rpg_create_threat_sheet` e derivadas. É a fonte de verdade dos dados T20.

### `artonMap/` — YuriAlessandro/artonMap
Mapa interativo de Arton em JavaScript com dados geográficos do mundo de Tormenta 20.

**Quando consultar:** ao trabalhar com lore de localizações, regiões ou contexto geográfico do mundo nas sessões de RPG.

---

## MCP Servers

### `playwright-mcp/` — microsoft/playwright-mcp
MCP server oficial da Microsoft para browser automation com Playwright.

**Quando consultar:** ao implementar qualquer automação de browser — "entre no LinkedIn e me traga notícias", scraping, preenchimento de formulários, captura de dados de sites. É a peça que habilita autonomia real de browser no Jarvez.

### `whatsapp-mcp/` — lharries/whatsapp-mcp
MCP server bidirecional para WhatsApp. Usa Python + Go bridge, conecta via QR code na conta pessoal e armazena histórico local em SQLite.

**Quando consultar:** ao melhorar a integração WhatsApp atual do Jarvez para acesso bidirecional real de qualquer lugar.

### `spotify-mcp-server/` — marcelmarais/spotify-mcp-server
MCP server leve para Spotify. Playback, playlists e histórico via tool call padrão.

**Quando consultar:** ao refatorar a integração Spotify atual do Jarvez para o padrão MCP.

---

## Catálogo online (não clonar)

**`https://github.com/punkpeye/awesome-mcp-servers`**
Lista com centenas de MCP servers prontos organizados por categoria: comunicação, produtividade, dev tools, automação, dados e muito mais.

Sempre consulte aqui antes de programar qualquer integração do zero. Se existir um MCP server público para o que você precisa, use-o como referência ou ponto de partida.

---

## Regras de uso

1. Verifique esta pasta antes de implementar qualquer integração ou skill nova.
2. Se existe referência aqui, estude o padrão antes de escrever código.
3. Nunca copie código sem adaptar — contexto, stack e arquitetura do Jarvez são diferentes.
4. Se encontrar um MCP server melhor para alguma categoria, substitua a referência e atualize este README.