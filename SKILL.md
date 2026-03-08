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

The product model is:

- local first for private consciousness data
- shared backend only for onboarding, gameplays, tasks, credits, and tool jobs
- default shared backend base URL: `https://self-consciousness-backend.onrender.com`
- gameplay and daily alignment are different things
- raw consciousness is recorded in the moment; background processing is a later layer

## Core Rules

1. Always treat `~/.self-consciousness/` as the user's private workspace.
2. Unless the user explicitly overrides it, use `https://self-consciousness-backend.onrender.com` as the shared backend base URL.
3. Register the user through `/api/v1/onboarding/register` before doing any shared action.
4. Keep raw consciousness local in the four main tables:
   - `gameplays`
   - `scores`
   - `consciousness_records`
   - `snapshots`
5. Do not upload raw consciousness records, snapshots, or score history.
6. Scoring is performed locally by the user's OpenClaw agent using this skill's instructions.
7. Do not rely on any backend scoring API.
8. Shared backend is only for:
   - onboarding
   - shared gameplay registry
   - community gameplay recommendation
   - task marketplace
   - credits
   - tool jobs

## First Run

On first activation:

1. Ask for or infer a `user_id`.
2. Use `https://self-consciousness-backend.onrender.com` as the default shared backend unless the user provided another one.
3. Call `POST /api/v1/onboarding/register`.
4. Confirm:
   - `user_id`
   - credits should start at `500`
   - local workspace path under `~/.self-consciousness/users/<user_id>/`
5. Save the backend base URL in `~/.self-consciousness/profile.json`.
5. Ask the user to choose one onboarding mode:
   - `structured_alignment_workspace`
   - `playful_alignment_experience`
6. Save the choice through `POST /api/v1/onboarding/preference`.

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
- `snapshots`
  - structured state snapshots, not raw logs

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

## Two Top-Level Experiences

### Structured Alignment Workspace

This is the default serious mode.

The user expresses only:

- purpose
- direction
- constraints
- evaluation
- interaction

The agent must respond on those same five dimensions, align dimension by dimension,
then produce the final answer in the form the user asked for.

Use this mode when the user wants clarity, planning, correction, or precise alignment.

### Playful Alignment Experience

This is the exploration mode.

The agent proposes a more playful or experimental gameplay and guides the user through it.
The goal is still alignment, but the surface experience can be challenge-like, narrative,
visual, or otherwise more playful.

Use this mode when the user wants novelty, energy, challenge, or a less procedural experience.

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

## Gameplay Operations

Shared gameplay registry lives on the backend.

Use:

- `GET /api/v1/gameplays`
- `GET /api/v1/gameplays/{id}`
- `POST /api/v1/gameplays/recommend`
- `POST /api/v1/gameplays/pull`
- `POST /api/v1/gameplays/{user_id}/iterate`
- `GET /api/v1/gameplays/{user_id}/current`
- `GET /api/v1/gameplays/{user_id}/history`

`/api/v1/gameplays/recommend` is for community discovery, not private analysis.
Only send coarse context such as:

- `onboarding_mode`
- `current_gameplay_id`
- `preferred_gameplay_ids`
- `exclude_recent_ids`
- `desired_tags`
- `available_tools`
- `stage_band`

Do not send raw consciousness records, snapshots, or full score history.

When the user wants to create a new gameplay:

1. use the `gameplay-creator` skill
2. write a markdown draft under the user's local `gameplay_drafts/`
3. publish it with `POST /api/v1/gameplays/contribute`

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
- image default model: `bytedance/seedream-v3`
- video default model: `bytedance/seedance-v1-lite-t2v-720p`

Use:

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
