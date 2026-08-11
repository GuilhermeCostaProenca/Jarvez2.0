# Jarvez 2.0 — Personal Voice AI Assistant

Jarvez is a personal AI assistant built to *do things*, not just chat: a voice-first agent with real actions, external integrations, long-term memory, and a safety layer.

## What it does

- **Voice conversation** with real actions (LiveKit + Google STT/TTS)
- **Real integrations:** Spotify, WhatsApp, OneNote, Home Assistant, LG ThinQ
- **Multi-agent orchestration** with sub-agents and multi-model routing
- **Long-term memory** per session (Mem0)
- **MCP action registry** (`backend/backend_mcp.py`) plus a browser agent for web tasks
- **Risk & autonomy policy** with a kill switch
- **Web-research dashboard** on a dedicated route

## Architecture

- `backend/` — voice agent, action registry, orchestration, providers and integrations (Python)
- `frontend/` — Next.js web interface for the session
- `docs/` — architecture and design notes

## Stack

Python · LiveKit · Mem0 · MCP · Node.js · TypeScript · Next.js · Docker

## Running

Run the setup once and start the dev environment:

```powershell
.\setup.ps1
.\start-dev.ps1
```

Then fill in the environment templates in `backend/.env` and `frontend/.env.local`.
