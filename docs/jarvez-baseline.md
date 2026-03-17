# Jarvez2.0 Technical Baseline

Generated on 2026-03-06 from static repository analysis.

## 1. Executive summary

Jarvez2.0 is a unified personal assistant stack split across:
- `backend/`: LiveKit voice agent runtime, action registry, policy/orchestration, local knowledge, integrations, code worker.
- `frontend/`: Next.js realtime client, OAuth/webhook routes, operational dashboards.

Current system shape:
- voice-first realtime assistant via LiveKit;
- 132 registered actions/tools;
- public/private memory with authentication gates;
- security with PIN/passphrase/voice biometrics;
- persona modes and character mode;
- project catalog, code search, local code worker, Codex CLI integration;
- multi-model routing, subagents, skills on demand;
- policy/risk/autonomy/killswitch/domain trust/trust drift;
- Trust Center with command queue, metrics, SLOs, canary, rollback, incident snapshot;
- real integrations: Spotify, OneNote, WhatsApp Cloud API, Home Assistant, LG ThinQ, local shell/desktop.

Key architectural fact: the main backend is not a conventional REST API. The primary runtime is the LiveKit worker in `backend/agent.py`. HTTP endpoints are split between Next.js API routes and the local code worker.

## 2. Repository structure

Top level:
- `backend/`
- `frontend/`
- `scripts/`
- `output/`
- `tmp/`
- `README.md`
- `AGENTS.md`
- `setup.ps1`
- `start-dev.ps1`

Critical backend files:
- `backend/agent.py`
- `backend/actions.py`
- `backend/prompts.py`
- `backend/code_worker.py`
- `backend/code_worker_client.py`
- `backend/code_knowledge.py`
- `backend/project_catalog.py`
- `backend/github_catalog.py`
- `backend/codex_cli.py`
- `backend/voice_biometrics.py`
- `backend/rpg_knowledge.py`

Important backend modules:
- `backend/orchestration/`: `planner.py`, `router.py`, `subagents.py`
- `backend/policy/`: `risk_engine.py`, `autonomy_rules.py`, `domain_trust.py`, `killswitch.py`, `trust_drift.py`
- `backend/providers/`: `provider_router.py`, `openai_provider.py`, `anthropic_provider.py`, `google_provider.py`
- `backend/skills/`: `loader.py`, `registry.py`, `schemas.py`
- `backend/evals/`: `metrics_store.py`, `scenario_suite.py`

Critical frontend files:
- `frontend/app/page.tsx`
- `frontend/components/app/app.tsx`
- `frontend/components/app/session-view.tsx`
- `frontend/hooks/useAgentActionEvents.ts`
- `frontend/lib/types/realtime.ts`
- `frontend/lib/research-dashboard-storage.ts`
- `frontend/lib/orchestration-storage.ts`

## 3. What Jarvez does today

### 3.1 Conversation and realtime
- Realtime voice conversation over LiveKit.
- Agent audio replies from backend session.
- Chat transcript and session HUD.
- Audio visualizer and remote participant state.
- Reconnect/error hooks on the client.

### 3.2 Memory and identity
- Public/private memory via Mem0.
- Automatic loading of public memory on join.
- Conditional loading of private memory for authenticated users.
- Memory forgetting by query.
- Manual memory scope selection.
- Identity auth via PIN/passphrase/security phrase.
- Voice profile enrollment, verification, deletion, and listing.

### 3.3 Persona and mode control
- Persona modes: `default`, `faria_lima`, `mona`, `rpg`, `hetero_top`.
- Functional modes: `default`, `coding`, `codex`.
- RPG character mode persisted in session state.

### 3.4 Web research
- Structured web search with dashboard payload.
- Dedicated dashboard route.
- Local persistence and re-open flow.
- Scheduled web briefing prompts from the frontend.

### 3.5 Coding and engineering workflow
- Multi-project catalog.
- Active project selection.
- Codebase indexing and search.
- File reads with line ranges.
- Git status and diff.
- Controlled patch application.
- Allowlisted command execution via code worker.
- Project explanation and change proposal actions.
- Codex CLI task execution and review.
- GitHub repo discovery, clone, and register flow.

### 3.6 Orchestration and autonomy
- Task orchestration with planning and provider routing.
- Subagent spawn/status/cancel.
- Skills list/read from local `SKILL.md` files.
- Risk classification per action.
- Policy explanation and action risk matrix.
- Autonomy modes, killswitch, domain trust, trust drift.
- Domain-level autonomy floor and containment.

### 3.7 Operations and observability
- Feature flags in runtime.
- Canary enrollment and global enablement.
- Progressive rollout controls.
- Incident snapshot.
- Metrics and SLO reports.
- Control loop and auto-remediation.
- Rollback by scenario.
- Trust Center command queue and audit trail.
- Notice delivery observability (`agent_audio`, `browser_tts`, `unconfirmed`).

### 3.8 Personal integrations
- Spotify playback/devices/playlist generation.
- OneNote notebook/section/page search and editing.
- WhatsApp webhook inbox plus text/TTS send.
- Home Assistant lights and service calls.
- LG ThinQ generic device control and specialized AC controls.
- Desktop open/run command actions.

### 3.9 RPG workflow
- Local RPG search/indexing.
- Character assumption mode.
- Character sheet generation.
- Threat sheet generation.
- Session recording/status/summary.
- Lore note save and next-session ideation.

## 4. Realtime and voice pipeline

### 4.1 Connection flow
1. Frontend calls `frontend/app/api/connection-details/route.ts`.
2. Next.js route issues LiveKit credentials and participant identity.
3. Frontend initializes session in `frontend/components/app/app.tsx`.
4. Backend worker in `backend/agent.py` joins the same room.

### 4.2 Agent startup
`backend/agent.py` performs:
- LiveKit room connection;
- participant identity/name resolution;
- Mem0 public memory load;
- conditional private memory load;
- `AgentSession` creation;
- function tool generation from exposed actions;
- realtime model startup with Google plugin;
- microphone audio stream capture for voice biometrics;
- optional ops control loop startup;
- initial reply generation.

### 4.3 Action execution flow
1. User message reaches the LiveKit agent.
2. Model decides whether to call a tool.
3. Backend validates auth/confirmation/risk/policy.
4. Handler executes inside `backend/actions.py` or helper modules.
5. Backend emits `ActionResult` and structured events.
6. Frontend `useAgentActionEvents.ts` parses `lk.agent.events`.
7. UI and local storage update derived state.

### 4.4 Client telemetry back to backend
The frontend can publish client telemetry on the room data channel topic `jarvez.client.telemetry`.
Current observed use: reporting `autonomy_notice_delivery` when browser TTS fallback is used.

## 5. Backend structure

### 5.1 Main runtime
- `backend/agent.py`: LiveKit worker and realtime agent lifecycle.

### 5.2 Action system
- `backend/actions.py`: `ActionSpec`, `ActionResult`, `ActionContext`, action registry, handlers, confirmation/auth/session stores.

### 5.3 Local code service
- `backend/code_worker.py`: HTTP server constrained to project/workspace operations.
- `backend/code_worker_client.py`: client wrapper.

Code worker endpoints:
- `GET /health`
- `POST /read-file`
- `POST /search-files`
- `POST /git-status`
- `POST /git-diff`
- `POST /apply-patch`
- `POST /run-command`

### 5.4 Provider layer
- `backend/providers/provider_router.py`
- `backend/providers/openai_provider.py`
- `backend/providers/anthropic_provider.py`
- `backend/providers/google_provider.py`

### 5.5 Orchestration
- `backend/orchestration/planner.py`
- `backend/orchestration/router.py`
- `backend/orchestration/subagents.py`

### 5.6 Policy and safety
- `backend/policy/risk_engine.py`
- `backend/policy/autonomy_rules.py`
- `backend/policy/domain_trust.py`
- `backend/policy/killswitch.py`
- `backend/policy/trust_drift.py`

### 5.7 Evals
- `backend/evals/metrics_store.py`
- `backend/evals/scenario_suite.py`

## 6. Frontend structure

Pages:
- `frontend/app/page.tsx`
- `frontend/app/orchestration/page.tsx`
- `frontend/app/research-dashboard/page.tsx`
- `frontend/app/trust-center/page.tsx`

Next API routes:
- `frontend/app/api/connection-details/route.ts`
- `frontend/app/api/spotify/login/route.ts`
- `frontend/app/api/spotify/callback/route.ts`
- `frontend/app/api/onenote/login/route.ts`
- `frontend/app/api/onenote/callback/route.ts`
- `frontend/app/api/whatsapp/webhook/route.ts`

Main app components:
- `frontend/components/app/app.tsx`
- `frontend/components/app/view-controller.tsx`
- `frontend/components/app/welcome-view.tsx`
- `frontend/components/app/session-view.tsx`
- `frontend/components/app/chat-transcript.tsx`
- `frontend/components/app/audio-visualizer.tsx`
- `frontend/components/app/action-confirmation-prompt.tsx`
- `frontend/components/app/coding-workspace.tsx`
- `frontend/components/app/orchestration-view.tsx`
- `frontend/components/app/research-dashboard-view.tsx`
- `frontend/components/app/trust-center-view.tsx`
- `frontend/components/app/tile-layout.tsx`

Hooks:
- `frontend/hooks/useAgentActionEvents.ts`
- `frontend/hooks/useAgentErrors.tsx`
- `frontend/hooks/useAutoReconnect.ts`
- `frontend/hooks/useAwarenessProactive.ts`
- `frontend/hooks/useDebug.ts`

Shared realtime typing and persistence:
- `frontend/lib/types/realtime.ts`
- `frontend/lib/research-dashboard-storage.ts`
- `frontend/lib/orchestration-storage.ts`

## 7. External integrations active in code
- LiveKit
- Google realtime model plugin
- OpenAI provider
- Anthropic provider
- Mem0
- Spotify Web API
- Microsoft Graph / OneNote
- WhatsApp Cloud API / Meta Graph
- Home Assistant
- LG ThinQ
- GitHub API
- Edge TTS
- local shell/desktop execution
- local code knowledge index
- local RPG knowledge index

## 8. Action inventory

Total registered actions found: `132`

Legend:
- `auth`: requires authenticated session
- `confirm`: requires confirmation gate
- `model`: exposed to the model

### 8.1 AC (`14`)
- `ac_apply_preset(device_name?: string, device_id?: string, preset: string, conditional?: boolean)` | auth | model
- `ac_configure_arrival_prefs(device_name?: string, desired_temperature?: number, hot_threshold?: number, vent_only_threshold?: number, eta_minutes?: integer, enable_swing?: boolean)` | model
- `ac_get_status(device_name?: string, device_id?: string)` | model
- `ac_prepare_arrival(device_name?: string, device_id?: string, desired_temperature?: number, hot_threshold?: number, vent_only_threshold?: number, eta_minutes?: integer, enable_swing?: boolean, dry_run?: boolean)` | auth | model
- `ac_send_command(device_name?: string, device_id?: string, conditional?: boolean, command: object)` | auth | confirm | model
- `ac_set_fan_speed(device_name?: string, device_id?: string, fan_speed: string, detail?: boolean, conditional?: boolean)` | auth | model
- `ac_set_mode(device_name?: string, device_id?: string, mode: string, conditional?: boolean)` | auth | model
- `ac_set_power_save(device_name?: string, device_id?: string, enabled: boolean, conditional?: boolean)` | auth | model
- `ac_set_sleep_timer(device_name?: string, device_id?: string, hours?: integer, minutes?: integer, conditional?: boolean)` | auth | model
- `ac_set_start_timer(device_name?: string, device_id?: string, hours?: integer, minutes?: integer, conditional?: boolean)` | auth | model
- `ac_set_swing(device_name?: string, device_id?: string, enabled: boolean, conditional?: boolean)` | auth | model
- `ac_set_temperature(device_name?: string, device_id?: string, temperature: number, unit?: string, conditional?: boolean)` | auth | model
- `ac_turn_off(device_name?: string, device_id?: string, conditional?: boolean)` | auth | model
- `ac_turn_on(device_name?: string, device_id?: string, conditional?: boolean)` | auth | model

### 8.2 Session/security/persona/memory (`13`)
- `authenticate_identity(pin?: string, passphrase?: string, security_phrase?: string)` | model
- `confirm_action(confirmation_token: string)` | auth | model
- `delete_voice_profile(name: string)` | model
- `enroll_voice_profile(name: string)` | model
- `forget_memory(query: string, scope?: 'all' | 'public' | 'private', limit?: integer)` | model
- `get_persona_mode()` | model
- `get_security_status()` | model
- `list_persona_modes()` | model
- `list_voice_profiles()` | model
- `lock_private_mode()` | model
- `set_memory_scope(scope: 'public' | 'private')` | model
- `set_persona_mode(mode: 'default' | 'faria_lima' | 'mona' | 'rpg' | 'hetero_top')` | model
- `verify_voice_identity()` | model

### 8.3 Web research (`1`)
- `web_search_dashboard(query: string, max_results?: integer)` | model

### 8.4 Home Assistant / local house controls (`4`)
- `call_service(domain: string, service: string, service_data: object)` | auth | confirm
- `set_light_brightness(entity_id: string, brightness: integer)` | auth | confirm | model
- `turn_light_off(entity_id: string)` | auth | confirm | model
- `turn_light_on(entity_id: string)` | auth | confirm | model

### 8.5 Local shell/desktop/git/engineering mode (`6`)
- `coding_mode_get()` | model
- `coding_mode_set(mode: 'default' | 'coding' | 'codex')` | model
- `git_clone_repository(repository_url: string, destination?: string, branch?: string, depth?: integer)` | auth | confirm | model
- `git_commit_and_push_project(message?: string, commit_message?: string, summary?: string, project_id?: string, query?: string, project_query?: string, fuzzy_query?: string, project?: string, project_name?: string, name?: string, confirmation_summary?: string)` | auth | confirm | model
- `open_desktop_resource(target: string, target_kind?: 'auto' | 'url' | 'path' | 'app')` | auth | model
- `run_local_command(command: string, arguments?: array<any>, working_directory?: string, wait_for_exit?: boolean, timeout_seconds?: integer)` | auth | confirm | model

### 8.6 Orchestration/providers/skills/subagents (`8`)
- `orchestrate_task(request?: string, query?: string, prompt?: string, action_hint?: string)` | model
- `providers_health_check(include_ping?: boolean, ping_prompt?: string)`
- `save_web_briefing_schedule(query: string, time_of_day?: string)` | model
- `skills_list(query?: string, refresh?: boolean)` | model
- `skills_read(skill_id?: string, skill_name?: string)` | model
- `subagent_cancel(subagent_id: string)` | model
- `subagent_spawn(request: string, action_hint?: string, auto_complete?: boolean, wait_for_completion?: boolean)` | model
- `subagent_status(subagent_id?: string)` | model

### 8.7 Policy/autonomy (`6`)
- `autonomy_killswitch(operation?: 'status' | 'enable' | 'disable' | 'enable_domain' | 'disable_domain', domain?: string, reason?: string)` | auth | model
- `autonomy_set_mode(mode: 'safe' | 'aggressive' | 'manual')` | model
- `policy_action_risk_matrix(query?: string, include_internal?: boolean)` | model
- `policy_domain_trust_status(domain?: string)` | model
- `policy_explain_decision(action_name: string)` | model
- `policy_trust_drift_report(signature?: string, rows?: array<object>)` | model

### 8.8 Ops/canary/incident management (`11`)
- `ops_apply_playbook(playbook: 'provider_degradation' | 'strict_guardrails' | 'block_domain' | 'unblock_domain' | 'restore_runtime_overrides', domain?: string, reason?: string, dry_run?: boolean)` | auth | confirm
- `ops_auto_remediate(dry_run?: boolean, force?: boolean, domain?: string, metrics_limit?: integer, cooldown_seconds?: integer)` | auth | confirm
- `ops_canary_promote(dry_run?: boolean, force?: boolean, step_if_passed?: boolean, rollback_on_fail?: boolean, min_samples?: integer, success_rate_min?: number, max_regression_vs_stable?: number, require_no_alerts?: boolean, metrics_limit?: integer, cooldown_seconds?: integer)` | auth | confirm
- `ops_canary_rollout_set(operation: 'set_percent' | 'step_up' | 'step_down' | 'pause' | 'resume', percent?: integer, dry_run?: boolean)` | auth | confirm
- `ops_canary_set(operation: 'enroll' | 'unenroll' | 'enable_global' | 'disable_global')` | auth | confirm
- `ops_canary_status(metrics_limit?: integer)` | auth
- `ops_control_loop_tick(dry_run?: boolean, auto_remediate?: boolean, auto_promote_canary?: boolean, force_remediation?: boolean, force_promotion?: boolean, domain?: string, metrics_limit?: integer, freeze_threshold?: integer, freeze_window_seconds?: integer, freeze_cooldown_seconds?: integer)` | auth | confirm
- `ops_feature_flags_set(feature: string, enabled: boolean)` | auth | confirm
- `ops_feature_flags_status()` | auth
- `ops_incident_snapshot(include_ping?: boolean, ping_prompt?: string, metrics_limit?: integer)` | auth
- `ops_rollback_scenario(scenario: 'provider_outage' | 'latency_spike' | 'reliability_breach' | 'trust_drift_breach' | 'recover_to_stable', domain?: string, reason?: string, dry_run?: boolean)` | auth | confirm

### 8.9 Evals (`5`)
- `evals_get_metrics(limit?: integer)`
- `evals_list_scenarios()`
- `evals_metrics_summary(limit?: integer)`
- `evals_run_baseline(task_type?: 'chat' | 'code' | 'review' | 'research' | 'automation' | 'unknown')`
- `evals_slo_report(limit?: integer)`

### 8.10 Code worker / code ops (`11`)
- `code_apply_patch(project_id?: string, query?: string, project?: string, project_name?: string, name?: string, changes: array<any>, confirmation_summary?: string)` | auth | confirm
- `code_explain_project(project_id?: string, request?: string, query?: string, project?: string, project_name?: string, name?: string, read_paths?: array<any>, limit?: integer)`
- `code_git_diff(project_id?: string, query?: string, project?: string, project_name?: string, name?: string, paths?: array<any>)`
- `code_git_status(project_id?: string, query?: string, project?: string, project_name?: string, name?: string)`
- `code_propose_change(project_id?: string, request?: string, query?: string, project?: string, project_name?: string, name?: string, read_paths?: array<any>, limit?: integer)`
- `code_read_file(project_id?: string, query?: string, project?: string, project_name?: string, name?: string, path: string, start_line?: integer, end_line?: integer)`
- `code_reindex_repo(paths?: array<any>)`
- `code_run_command(project_id?: string, query?: string, project?: string, project_name?: string, name?: string, command: string, arguments?: array<any>, timeout_seconds?: integer, confirmation_summary?: string)` | auth | confirm
- `code_search_in_active_project(project_id?: string, query: string, project?: string, project_name?: string, name?: string, limit?: integer)`
- `code_search_repo(query: string, limit?: integer)`
- `code_worker_status()`

### 8.11 Codex (`4`)
- `codex_cancel_task()` | model
- `codex_exec_review(request?: string, query?: string, project_id?: string, project?: string, project_name?: string, name?: string)` | model
- `codex_exec_status()` | model
- `codex_exec_task(request?: string, query?: string, prompt?: string, project_id?: string, project?: string, project_name?: string, name?: string)` | model

### 8.12 GitHub (`3`)
- `github_clone_and_register(repository?: string, full_name?: string, name?: string, query?: string, destination?: string, destination_root?: string, branch?: string, depth?: integer)` | auth | confirm | model
- `github_find_repo(repository?: string, full_name?: string, name?: string, query?: string)` | auth | model
- `github_list_repos(query?: string, limit?: integer, visibility?: 'all' | 'public' | 'private')` | auth | model

### 8.13 Projects (`9`)
- `project_clear_active()` | model
- `project_get_active()` | model
- `project_list(include_inactive?: boolean)` | model
- `project_refresh_index(project_id?: string, query?: string, project?: string, project_name?: string, name?: string)` | model
- `project_remove(project_id: string)` | model
- `project_scan()` | model
- `project_search(project_id?: string, query: string, project?: string, project_name?: string, name?: string, limit?: integer)` | model
- `project_select(project_id?: string, query?: string, project_query?: string, fuzzy_query?: string, project?: string, project_name?: string, name?: string)` | model
- `project_update(project_id: string, name?: string, aliases?: array<any>, priority_score?: integer, is_active?: boolean)` | model

### 8.14 Spotify (`9`)
- `spotify_create_surprise_playlist(name?: string, public?: boolean)` | auth | model
- `spotify_get_devices()` | model
- `spotify_next_track()` | model
- `spotify_pause()` | model
- `spotify_play(query?: string, uri?: string, device_name?: string, device_id?: string)` | model
- `spotify_previous_track()` | model
- `spotify_set_volume(volume_percent: integer, device_name?: string, device_id?: string)` | model
- `spotify_status()` | model
- `spotify_transfer_playback(device_name?: string, device_id?: string, play?: boolean)` | model

### 8.15 OneNote (`8`)
- `onenote_append_to_page(page_id: string, content: string)` | auth | confirm | model
- `onenote_create_character_page(section_id: string, title: string, body?: string)` | auth | confirm | model
- `onenote_get_page_content(page_id: string)` | model
- `onenote_list_notebooks(query?: string)` | model
- `onenote_list_pages(section_id?: string, section_name?: string, query?: string)` | model
- `onenote_list_sections(notebook_name?: string, notebook_id?: string)` | model
- `onenote_search_pages(query?: string, title?: string, name?: string, section_id?: string, section_name?: string)` | model
- `onenote_status()` | model

### 8.16 WhatsApp (`3`)
- `whatsapp_get_recent_messages(contact?: string, limit?: integer)` | auth | model
- `whatsapp_send_audio_tts(to: string, text: string)` | auth | confirm | model
- `whatsapp_send_text(to: string, text: string)` | auth | confirm | model

### 8.17 ThinQ generic (`5`)
- `thinq_control_device(device_name?: string, device_id?: string, conditional?: boolean, command: object)` | auth | confirm | model
- `thinq_get_device_profile(device_name?: string, device_id?: string)` | model
- `thinq_get_device_state(device_name?: string, device_id?: string)` | model
- `thinq_list_devices()` | model
- `thinq_status()` | model

### 8.18 RPG (`12`)
- `rpg_assume_character(name: string, source?: 'auto' | 'onenote' | 'pdf' | 'manual', section_name?: string, referencia_visual_url?: string, pinterest_pin_url?: string, descricao_visual?: string)` | model
- `rpg_clear_character_mode()` | model
- `rpg_create_character_sheet(name: string, world?: string, race?: string, class_name?: string, class?: string, character_class?: string, origin?: string, level?: integer, concept?: string, attributes?: object, build_choices?: object, generation_mode?: 'auto' | 'strict', prefer_engine?: 't20' | 'fallback' | 'auto')` | model
- `rpg_create_threat_sheet(name: string, world?: string, threat_type?: string, size?: string, role?: 'Solo' | 'Lacaio' | 'Especial', challenge_level: string, concept?: string, has_mana_points?: boolean, is_boss?: boolean, displacement?: string, attributes?: object, attacks_override?: array<any>, abilities_override?: array<any>, spells_override?: array<any>, special_qualities?: string, equipment?: string, treasure_level?: string, generation_mode?: 'suggested' | 'structured')` | model
- `rpg_get_character_mode()` | model
- `rpg_get_knowledge_stats()` | model
- `rpg_ideate_next_session(session_file?: string)` | model
- `rpg_reindex_sources(paths?: array<any>)` | model
- `rpg_save_lore_note(title?: string, world?: string, content: string)` | model
- `rpg_search_knowledge(query: string, limit?: integer)` | model
- `rpg_session_recording(mode: 'start' | 'stop' | 'status', title?: string, world?: string)` | model
- `rpg_write_session_summary(session_file?: string)` | model

## 9. TODOs, FIXMEs, incomplete implementations

Repository-wide search found very little first-party TODO debt.

Real TODO found:
- `backend/vendor/t20-sheet-builder/build/domain/entities/Role/Arcanist/.../ArcanistLineageDraconicDamageReductionEffect.js`
  - `TODO: ArcanistLineageDraconicDamageReductionEffect.apply()`

Notable technical gaps visible from structure:
- frontend lacks a dedicated automated test suite;
- main backend remains heavily centralized in `backend/actions.py`;
- important operational state exists only in browser `localStorage`;
- realtime voice runtime is still directly tied to the Google realtime model in `backend/agent.py`, while the multi-model router exists mostly for action/orchestration paths.

## 10. Technology stack

### Backend
Language:
- Python

Declared requirements:
- `livekit-agents[images]`
- `livekit-plugins-google`
- `livekit-plugins-noise-cancellation`
- `python-dotenv`
- `requests`
- `mem0ai`
- `cryptography`
- `numpy`
- `edge-tts`
- `pypdf`
- `reportlab`

Observed backend technologies:
- LiveKit Agents / RTC
- Google realtime plugin
- Mem0
- Requests
- Edge TTS
- local JSON persistence

### Frontend
Language/tooling:
- TypeScript
- Next.js App Router
- React 19
- pnpm

Pinned/declared versions in `frontend/package.json`:
- `next`: `15.5.9`
- `react`: `^19.0.0`
- `react-dom`: `^19.0.0`
- `typescript`: `^5`
- `packageManager`: `pnpm@9.15.9`

Observed frontend libraries:
- `@livekit/components-react`
- `livekit-client`
- `livekit-server-sdk`
- Radix UI packages
- `lucide-react`
- `sonner`
- `motion`
- `three`
- `vanta`
- `@xyflow/react`
- `shiki`

## 11. Tests and validation assets

Backend tests present:
- `backend/test_actions.py`
- `backend/test_codex_cli.py`
- `backend/test_code_knowledge.py`
- `backend/test_github_catalog.py`
- `backend/test_memory_scope.py`
- `backend/test_project_catalog.py`
- `backend/test_rpg_engine.py`
- `backend/test_voice_biometrics.py`

Smoke test:
- `scripts/e2e-smoke.ps1`
  - compiles critical backend files;
  - runs selected backend unit tests;
  - runs frontend `npm run check`;
  - includes manual acceptance checklist.

Frontend automated tests:
- none found as dedicated Jest/Vitest/Playwright app specs.
- current frontend quality gates are mainly lint, typecheck, and build.

## 12. Practical baseline reading

Strong today:
- private personal assistant core;
- realtime voice session;
- action execution against real systems;
- coding workflow inside the assistant;
- policy/trust/ops foundation;
- operational observability UI;
- multiple real external integrations.

Main risk concentrations:
- `backend/actions.py`
- `backend/agent.py`
- `frontend/hooks/useAgentActionEvents.ts`
- `frontend/components/app/session-view.tsx`
- `frontend/lib/types/realtime.ts`
