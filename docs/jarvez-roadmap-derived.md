# Jarvez2.0 Derived Technical Roadmap

Derived from:
- `docs/jarvez-baseline.md`
- `docs/jarvez-vs-openclaw-gap-analysis.md`

## 1. Goal

Evolve Jarvez from a strong private assistant core into a broader operator platform without losing its current advantages in:
- safety;
- trust and policy;
- coding workflow;
- operational observability.

## 2. Current phase reading

From the repository state, Jarvez is approximately here:
- core runtime: strong
- operational policy/guardrails: strong
- coding workflow: strong
- platform breadth: limited
- productization/package surface: limited
- frontend test automation: weak

## 3. Roadmap principles

- Do not rewrite the runtime from scratch.
- Preserve the LiveKit-based voice core until a better abstraction actually exists.
- Reduce centralization risk in `backend/actions.py` incrementally.
- Expand surfaces only after hardening what already works.
- Keep the session UI clean; put heavy observability into dedicated routes.

## 4. Phase 1: hardening the current core

### Objectives
- raise confidence in existing runtime;
- reduce fragility in the most central modules;
- close observability and testing gaps.

### Workstreams
- split `backend/actions.py` by domain behind a stable registry boundary;
- add deeper backend integration tests for critical actions;
- add frontend automated tests for event parsing and state derivation;
- tighten command execution and workspace boundaries in the code worker;
- add more explicit end-to-end trace correlation across session, action, and UI;
- audit all auth-required and confirm-required actions for consistency.

### Exit criteria
- critical flows covered by automated tests;
- no policy-critical logic living only in the client;
- incident/trust/trace views stable under long sessions.

## 5. Phase 2: gateway abstraction inside Jarvez

### Objectives
- create a single architectural surface that can later support more channels and clients.

### Workstreams
- introduce a Jarvez gateway abstraction for sessions, messages, events, telemetry, and tools;
- standardize inbound/outbound message envelopes independent of LiveKit;
- separate transport adapters from assistant runtime logic;
- normalize channel identity, peer identity, and routing concepts;
- unify OAuth/webhook/config state under a more central control layer.

### Exit criteria
- assistant runtime no longer assumes a single LiveKit-first client shape for all future surfaces;
- new channels can plug into a shared routing and policy layer.

## 6. Phase 3: multi-surface communications

### Objectives
- close the biggest gap versus OpenClaw breadth.

### Priority order
1. WhatsApp full conversational surface
2. Web chat external surface
3. Telegram
4. Slack
5. Discord

### Workstreams
- channel adapter interface;
- inbound DM safety policies;
- sender allowlist/pairing model;
- per-channel chunking/reply behavior;
- shared inbox and routing audit trail.

### Exit criteria
- at least three non-LiveKit user-facing channels;
- common routing, policy, and observability across them.

## 7. Phase 4: automation surface expansion

### Objectives
- broaden capability beyond direct chat.

### Workstreams
- browser automation toolchain;
- cron and wakeup jobs;
- generic webhook triggers;
- event-driven automations;
- provider-independent scheduling model.

### Exit criteria
- Jarvez can execute unattended low-risk automations with auditability and rollback hooks.

## 8. Phase 5: productization

### Objectives
- make setup and operation materially easier.

### Workstreams
- onboarding wizard;
- environment diagnostics / doctor command;
- service/daemon mode for the gateway runtime;
- packaging and update strategy;
- deployment docs for local/private installs.

### Exit criteria
- fresh setup is reproducible and diagnosable without manual code spelunking.

## 9. Phase 6: native and device ecosystem

### Objectives
- move from browser-centric personal assistant to multi-device personal operator.

### Workstreams
- lightweight desktop control surface;
- remote/mobile companion surface;
- wake-word or push-to-talk layer;
- device telemetry/notification hooks.

### Exit criteria
- user can reach Jarvez from more than one active surface without the current repo feeling fragmented.

## 10. Immediate backlog from current codebase

### Highest leverage technical items
- modularize `backend/actions.py`
- add frontend test coverage around `useAgentActionEvents.ts`
- add integration tests for policy, trust drift, and command queue correlation
- harden code worker path/command constraints
- unify backend as source of truth where the frontend still owns too much operational state
- document env/config for every integration in a single place

### Highest leverage product items
- improve WhatsApp from tool integration into a fuller user-facing channel
- add external web chat or remote session entry
- build a more explicit gateway/control-plane concept over the current pieces

## 11. Risks to manage during expansion

- channel sprawl before the gateway abstraction exists;
- widening features while `backend/actions.py` remains over-centralized;
- putting more safety-critical state only in `localStorage`;
- adding autonomy without stronger cross-channel policy consistency;
- product breadth outpacing test coverage.

## 12. Recommended next execution order

1. Create modular boundaries inside the current backend.
2. Add missing automated tests, especially frontend event-state coverage.
3. Introduce a gateway/channel abstraction layer.
4. Expand WhatsApp and add WebChat.
5. Add Telegram/Slack/Discord adapters.
6. Add browser automation and cron/webhook automation.
7. Productize onboarding and diagnostics.

## 13. Success criteria

Jarvez will be in a strong competitive position when it has:
- the current private assistant core fully hardened;
- at least three external communication surfaces beyond the current session;
- one coherent gateway/control-plane model;
- browser and scheduled automation primitives;
- onboarding/doctor flows that make setup and recovery routine.

## 14. Strategic thesis

Do not try to beat OpenClaw by copying all of its breadth first.
Beat it by combining:
- broader surfaces over time,
- stronger safety and policy instrumentation,
- better coding/operator workflow,
- higher trust in real execution.
