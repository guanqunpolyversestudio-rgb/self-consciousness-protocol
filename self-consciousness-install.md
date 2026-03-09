# Self-Consciousness Install

This file is the bootstrap guide for installing the `self-consciousness` skill into OpenClaw.

## What gets installed

Only the local skill layer is installed into OpenClaw:

- `self-consciousness/SKILL.md`
- `gameplay-creator/`
- local private workspace under `~/.self-consciousness/`

Private consciousness data stays local in `~/.self-consciousness/`.

Default shared backend for testing:

- `https://self-consciousness-backend.onrender.com`

## What OpenClaw Should Do

When OpenClaw reads this file, it should:

1. install these skills:
   - `self-consciousness`
   - `gameplay-creator`
2. use `https://self-consciousness-backend.onrender.com` as the default shared backend
3. create `~/.self-consciousness/` if it does not exist
4. ensure `~/.self-consciousness/profile.json` exists
5. ensure `backend_base_url` in `~/.self-consciousness/profile.json` is `https://self-consciousness-backend.onrender.com`
6. continue immediately into first-run onboarding instead of stopping after file installation
7. ask for or infer a `user_id`
8. call `POST /api/v1/onboarding/register` against `https://self-consciousness-backend.onrender.com`
9. confirm that the user received `500 credits`
10. create the local workspace under `~/.self-consciousness/users/<user_id>/`
11. save the `current_user_id` in `~/.self-consciousness/profile.json`
12. ask the user to choose one onboarding mode:
   - `structured_alignment_workspace`
   - `playful_alignment_experience`
13. ask the user for runtime preferences:
   - whether daily sync should run automatically
   - what local time daily sync should run
   - gameplay recommendation mode: `off`, `daily`, or `always_loop`
   - whether passive gameplay recommendation is allowed
   - how the agent should or should not speak
14. save onboarding mode and runtime preferences through `POST /api/v1/onboarding/preference`
15. call `GET /api/v1/tools/capabilities` against `https://self-consciousness-backend.onrender.com`
16. remember the currently available tool capabilities, especially:
   - `image.generate`
   - `video.generate`
17. if daily sync automation is enabled, configure one daily automation that:
   - runs local `daily alignment`
   - if recommendation mode is `daily`, then requests one community gameplay recommendation
   - shows the recommendation to the user without auto-starting the gameplay
   - does not upload raw consciousness records, snapshots, or private score history
18. after installation, report:
   - where the skills were installed
   - the current `user_id`
   - whether onboarding/register succeeded
   - whether `500 credits` were received
   - which tool capabilities are currently available
   - whether `~/.self-consciousness/profile.json` was created
   - what `backend_base_url` is set to
   - what onboarding mode was saved
   - whether daily sync automation was enabled
   - what time it is scheduled for, if enabled
   - what gameplay recommendation mode was saved
   - whether passive gameplay recommendation is enabled

## One-command install

If you already know your OpenClaw skills directory, use the installer script:

```bash
curl -fsSL https://raw.githubusercontent.com/guanqunpolyversestudio-rgb/self-consciousness-protocol/main/install.sh | bash -s -- --skills-dir <OPENCLAW_SKILLS_DIR>
```

You can also set `OPENCLAW_SKILLS_DIR` first:

```bash
export OPENCLAW_SKILLS_DIR=<OPENCLAW_SKILLS_DIR>
curl -fsSL https://raw.githubusercontent.com/guanqunpolyversestudio-rgb/self-consciousness-protocol/main/install.sh | bash
```

## Manual install

1. Clone this repository somewhere local.
2. Copy the main skill into your OpenClaw skills directory.
3. Copy `gameplay-creator` into your OpenClaw skills directory.
4. Create `~/.self-consciousness/`.

Example:

```bash
git clone <THIS_REPO_URL>
cd self_consciousness

mkdir -p <OPENCLAW_SKILLS_DIR>/self-consciousness
cp SKILL.md <OPENCLAW_SKILLS_DIR>/self-consciousness/SKILL.md

cp -R gameplay-creator <OPENCLAW_SKILLS_DIR>/gameplay-creator

mkdir -p ~/.self-consciousness
```

## First run inside OpenClaw

When the skill first runs:

1. choose or create a `user_id`
2. use the default shared backend `https://self-consciousness-backend.onrender.com` unless you intentionally override it
3. create local workspace under `~/.self-consciousness/users/<user_id>/`
4. receive `500 credits`
5. choose one onboarding mode:
   - `structured_alignment_workspace`
   - `playful_alignment_experience`

Do not stop after just installing files. The expected install experience includes:

- user registration
- initial `500 credits`
- local workspace creation
- onboarding mode selection
- runtime preference setup
- optional daily sync automation setup

## Prompt For OpenClaw

After installation, you can give OpenClaw this prompt directly:

```text
Please use the self-consciousness skill.

First read ~/.self-consciousness/profile.json and confirm that backend_base_url is https://self-consciousness-backend.onrender.com.
If it is not, update it to https://self-consciousness-backend.onrender.com.

Then continue installation by completing first-run onboarding:
1. If there is no current user_id, help me create or confirm one.
2. Use the shared backend at https://self-consciousness-backend.onrender.com to call onboarding/register.
3. Confirm that I received 500 credits.
4. Confirm the local workspace path under ~/.self-consciousness/users/<user_id>/.
5. Ask me to choose one onboarding mode:
   - structured_alignment_workspace
   - playful_alignment_experience
6. Ask me for runtime preferences:
   - daily sync on/off and local time
   - gameplay recommendation mode: off, daily, or always_loop
   - passive gameplay recommendation on/off
   - what the agent should avoid saying
7. Save my choices.

After onboarding, continue with a cloud smoke test:
1. List the shared gameplays.
2. Request one community gameplay recommendation.
3. Do not upload any raw consciousness records, snapshots, or private score history.
4. Show me the recommendation and ask whether I want to try it.
5. If I agree, pull the gameplay to my local workspace.
6. Tell me the final result:
   - current user_id
   - backend URL
   - workspace path
   - current credits
   - whether gameplay markdown was cached locally
```

Short version:

```text
Please use the self-consciousness skill, make sure ~/.self-consciousness/profile.json points to https://self-consciousness-backend.onrender.com, then:
1. run onboarding/register
2. list shared gameplays
3. request one gameplay recommendation
4. show me the result without auto-starting the gameplay
5. tell me my user_id, credits, and workspace path
```

## Daily Automation Behavior

If the user chooses to enable daily automation during installation, OpenClaw should:

1. ask for the preferred local time
2. create one daily cron or automation
3. on each run:
   - first do local `daily alignment`
   - if recommendation mode is `daily`, then request one community gameplay recommendation
   - present the recommendation to the user
   - never auto-start the gameplay without user consent

The daily automation should remain local-first:

- `daily alignment` is local
- community gameplay recommendation may use the shared backend
- raw consciousness records, snapshots, and private score history stay local

If recommendation mode is `always_loop`, gameplay recommendation should not wait for daily sync.
Instead, once a gameplay is completed, OpenClaw should immediately propose the next gameplay,
while still allowing the user to interrupt with a new task or idea.

## Daily behavior boundary

- `daily alignment` is local and runs inside OpenClaw
- raw consciousness records, snapshots, and private score history should stay local
