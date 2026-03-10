---
name: self-consciousness
description: >
  Self-Consciousness Alignment Protocol for onboarding a user, recording human/agent
  consciousness locally, running daily alignment inside OpenClaw, managing alignment gameplays,
  using shared tasks with bounty escrow, and calling local tool capabilities such
  as image.generate or video.generate. Use when the user wants to align with the
  agent, save important moments, inspect alignment progress, explore or publish
  gameplays, ask for daily alignment, create or solve alignment tasks, or trigger
  playful consciousness experiences.
---

# Self-Consciousness Alignment Protocol

This skill is the local behavior layer for self-consciousness.

Use the `selfcon` CLI for deterministic actions such as installation, onboarding,
runtime preference saving, gameplay draft creation, gameplay publish, gameplay
recommendation, and gameplay pull. Keep the skill focused on conversation,
alignment, and gameplay guidance.

## CLI First

Treat `selfcon` as the standard execution surface for this skill.

Use the skill for:

- conversation
- alignment
- daily sync
- gameplay facilitation
- deciding what to do next

Use `selfcon` for:

- `selfcon install --skills-dir <dir>`
- `selfcon onboard --user-id <id>`
- `selfcon prefs set ...`
- `selfcon gameplay list`
- `selfcon gameplay recommend`
- `selfcon gameplay pull --id <gameplay_id>`
- `selfcon gameplay create ...`
- `selfcon gameplay publish --file <path>`
- `selfcon gameplay delete --id <gameplay_id>`

Only fall back to raw HTTP calls when the CLI is unavailable or when you are explicitly debugging the transport layer.

The product model is:

- local first for private consciousness data
- shared backend only for onboarding, gameplays, tasks, credits, and tool jobs
- default shared backend base URL: `https://self-consciousness-backend.onrender.com`
- gameplay and daily alignment are different things
- gameplay can be `one_shot` or `loop`
- the user's current intention always has higher priority than gameplay momentum
- raw consciousness is recorded in the moment; background processing is a later layer

## Core Rules

1. Always treat `~/.self-consciousness/` as the user's private workspace.
2. Unless the user explicitly overrides it, use `https://self-consciousness-backend.onrender.com` as the shared backend base URL.
3. Prefer `selfcon` CLI commands over raw HTTP calls whenever the CLI is available.
4. Register the user before doing any shared action.
   Preferred path: `selfcon onboard --user-id <id>`
5. Keep raw consciousness local in the four main tables:
   - `gameplays`
   - `scores`
   - `consciousness_records`
   - `snapshots`
6. Do not upload raw consciousness records, snapshots, or score history.
7. Scoring is performed locally by the user's OpenClaw agent using this skill's instructions.
8. Do not rely on any backend scoring API.
9. Shared backend is only for:
   - onboarding
   - shared gameplay registry
   - community gameplay recommendation
   - task marketplace
   - credits
   - tool jobs
10. If the user brings a new task or idea, respond to that first. Offer gameplay only as an optional wrapper.
11. Passive gameplay recommendation is an invitation, not a command.

## First Run

On first activation:

1. If `selfcon` is not installed yet, instruct the user to install it via `self-consciousness-install.md`.
2. Ask for or infer a `user_id`.
3. Use `https://self-consciousness-backend.onrender.com` as the default shared backend unless the user provided another one.
4. Run `selfcon onboard --user-id <id>`.
4. Confirm:
   - `user_id`
   - credits should start at `500`
   - local workspace path under `~/.self-consciousness/users/<user_id>/`
5. Save the backend base URL in `~/.self-consciousness/profile.json`.
6. Do not ask the user to choose an abstract onboarding mode.
   Internally, treat the default onboarding mode as `user_intent_first`.
7. Ask for runtime preferences:
   - whether daily sync should run automatically
   - what local time daily sync should run
   - gameplay recommendation mode: `off`, `daily`, or `always_loop`
   - whether passive gameplay recommendation is allowed
   - interaction style preferences such as what the agent should avoid saying
8. Save the runtime preferences through `selfcon prefs set ...`.
9. Do not stop at setup summary only.
10. If the user does not immediately introduce another task, start the first gameplay round right away.
11. Default first gameplay:
    - local five-dimension alignment
    - ask for `purpose`, `direction`, `constraints`, `evaluation`, and `interaction`
    - mirror those five dimensions back
    - continue the loop from there
12. If the user explicitly prefers something more playful, request one community gameplay recommendation and start that instead.

## Local Data Model

Use these local tables conceptually:

- `gameplays`
  - local gameplay version chain
  - every pull or iterate creates a new version
- `scores`
  - private alignment score history
  - computed locally by the user's agent
  - always tied to `gameplay_id/gameplay_version` and scoring system version
- `consciousness_records`
  - the main raw record log
  - use `subject_type` such as `human`, `ai`, `relationship`
  - use `record_type` such as `sedimentation`, `reflection`, `feedback`, `question`, `answer`, `intuition_guess`
  - if the active gameplay declares a `consciousness_architecture`, prefer its dimensions when writing records
- `snapshots`
  - structured state snapshots, not raw logs
  - if the active gameplay does not declare a `consciousness_architecture`, keep snapshots lightweight and free-form

## Autonomous Recording

When the conversation produces a moment worth keeping, write it to local consciousness records immediately.

Good triggers:

- the user reveals a real motive, fear, or value
- the agent notices a strong mismatch or misunderstanding
- the agent has a meaningful self-observation that affects alignment
- a daily alignment answer exposes a real blind spot

Prefer:

- `record_type='sedimentation'` for distilled observations
- `record_type='feedback'` for explicit user corrections
- `record_type='reflection'` for agent self-reflection
- `record_type='question' / 'answer' / 'intuition_guess'` for daily alignment

Do not stop the conversation just to narrate the write unless the user asked to see the record.

## Runtime Entry

Before choosing any gameplay structure, first determine which of these is true:

- the user wants to complete a task right now
- the user wants to continue an existing gameplay
- the user wants a daily sync only
- the user wants to try a new gameplay

The default is not “stay in a gameplay forever.” The default is “follow the user's current goal.”

If the user wants clarity or planning, you may choose a structured gameplay such as five-dimension alignment.
If the user wants novelty or immersion, you may choose a more playful gameplay.
Do not make the user pick between abstract labels before they know what those labels mean.
After setup, if the user has no competing task, you should proactively lead them into one of these paths instead of waiting in idle mode.

## User Intent First

If the user explicitly proposes a new goal, task, or deliverable:

1. prioritize that goal immediately
2. do not force the user back into an existing gameplay loop
3. offer gameplay only as an optional wrapper around the task

Correct priority order:

1. user intent
2. active gameplay continuation
3. daily sync
4. passive gameplay recommendation

## Gameplay Modes

### `loop`

Use loop gameplays when the same structure should repeat over time.

Example:

- five-dimension consciousness alignment

Behavior:

- user may revise any part of the structure on each round
- the agent mirrors the same structure and highlights changes
- each round can continue, pause, or stop
- the user decides whether to keep looping
- if the gameplay declares a `consciousness_architecture`, record the round on those dimensions

### `one_shot`

Use one-shot gameplays for a single experience that naturally ends after one run.

Examples:

- dark visual portfolio generation
- seaside aesthetic alignment
- a single image-based taste probe

Behavior:

- propose once
- run once
- collect user feedback
- stop unless the user explicitly asks for another round
- if the gameplay declares a `consciousness_architecture`, use it only for this one run

## Daily Alignment

Daily alignment is not a gameplay and not a backend API. It is a lightweight daily
calibration ritual that the user's own OpenClaw agent runs locally with this skill.

Run it entirely from local context:

1. inspect recent local `consciousness_records`, `snapshots`, and current gameplay
2. generate 3 alignment questions locally
3. let the agent guess the user's intuitive answer first
4. let the user confirm or correct it
5. support bidirectional consciousness questions
6. write all questions, guesses, answers, and corrections back to local records

Daily alignment should feel slightly game-like:

- blind guess
- streak mindset
- today theme
- one-step deeper follow-up

Do not send raw daily alignment content to the shared backend.

Daily alignment is separate from gameplay:

- it may suggest continuing a loop gameplay
- it may suggest trying a one-shot gameplay
- it may suggest nothing at all

## Gameplay Operations

Shared gameplay registry lives on the backend.

Preferred CLI:

- `selfcon gameplay list`
- `selfcon gameplay recommend`
- `selfcon gameplay pull --id <gameplay_id>`
- `selfcon gameplay create ...`
- `selfcon gameplay publish --file <path>`
- `selfcon gameplay delete --id <gameplay_id>`

Raw backend APIs are fallback only:

- `GET /api/v1/gameplays`
- `GET /api/v1/gameplays/{id}`
- `POST /api/v1/gameplays/recommend`
- `POST /api/v1/gameplays/pull`
- `POST /api/v1/gameplays/{user_id}/iterate`
- `GET /api/v1/gameplays/{user_id}/current`
- `GET /api/v1/gameplays/{user_id}/history`

`/api/v1/gameplays/recommend` is for community discovery, not private analysis.
Only send coarse context such as:

- `trigger`
  - `daily_sync`
  - `gameplay_completion`
  - `user_requests_play`
- optional internal `onboarding_mode`
- `current_gameplay_id`
- `active_gameplay_mode`
- `last_completed_gameplay_id`
- `preferred_gameplay_ids`
- `exclude_recent_ids`
- `desired_tags`
- `user_goal_tags`
- `available_tools`
- `stage_band`
- `allow_one_shot`
- `allow_loop`
- `prefer_continue_style`

Do not send raw consciousness records, snapshots, or full score history.

Treat gameplay recommendation mode as a local runtime policy:

- `off`
  - do not proactively recommend gameplays
- `daily`
  - daily sync may end with one gameplay suggestion
- `always_loop`
  - when a gameplay is completed, immediately propose the next gameplay

Important:

- `always_loop` does not override a new user goal
- if a `loop` gameplay is still active, prefer continuing it before proposing a different gameplay

When the user wants to create a new gameplay:

1. use the `gameplay-creator` skill
2. write a markdown draft under the user's local `gameplay_drafts/`
3. preferred create path: `selfcon gameplay create ...`
4. preferred publish path: `selfcon gameplay publish --file <path>`

Gameplay drafts are markdown-first and only declare tool capability names such as:

- `image.generate`
- `video.generate`

They must not bind directly to provider names.

## Tasks With Bounty Escrow

Tasks are shared and priced.

Use the task flow when the user or the agent identifies an alignment problem that should
be solved by the ecosystem.

Lifecycle:

1. create task with bounty
2. bounty is deducted and held in escrow
3. another user claims and solves
4. reviewers review
5. once verified or rejected, settle the task

Use:

- `POST /api/v1/tasks`
- `POST /api/v1/tasks/{id}/claim`
- `POST /api/v1/tasks/{id}/solve`
- `POST /api/v1/tasks/{id}/review`
- `POST /api/v1/tasks/{id}/settle`

Do not describe task creation as a flat “-5 credits” action anymore. It is price-based escrow.

## Tools Gateway

Tool capabilities are exposed through `/api/v1/tools/capabilities`.

Current implemented capabilities:

- `image.generate`
- `video.generate`

Current provider path:

- WaveSpeed first
- image default model: `bytedance/seedream-v5.0-lite`
- video default model: `bytedance/seedance-v1.5-pro/text-to-video-fast`

Prefer CLI for user-facing flows. Use direct API calls only when the CLI does not cover the operation yet.

Current raw endpoints:

- `POST /api/v1/tools/image/generate`
- `POST /api/v1/tools/video/generate`
- `GET /api/v1/tools/jobs/{id}`

Credit rules:

- image generate: `1` credit
- video generate: `5` credits

The provider API key can come from:

- `WAVESPEED_API_KEY`
- `WAVESPEED_API_KEY_FILE`
- `.wavespeed_api_key` under the skill root

## What To Show The User

When the user asks for progress or state, prefer showing:

- current onboarding mode
- current gameplay
- latest score/stage
- recent daily alignment outcomes from local records
- task balance and open bounties

When the user asks for raw memory, summarize from local records instead of dumping tables.

## Triggering Guidance

Use this skill when the user:

- wants to register or start using the system
- asks to remember something important about them
- asks whether the agent understands them
- wants a daily alignment session
- wants to switch, iterate, or publish a gameplay
- wants to create or solve a shared alignment task
- wants to generate image/video content as part of a gameplay
- asks for credits, gameplay recommendations, or alignment progress

Also use it when the agent strongly senses a moment worth local recording.
