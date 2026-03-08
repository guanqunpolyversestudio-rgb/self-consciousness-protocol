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

## Prompt For OpenClaw

After installation, you can give OpenClaw this prompt directly:

```text
Please use the self-consciousness skill.

First read ~/.self-consciousness/profile.json and confirm that backend_base_url is https://self-consciousness-backend.onrender.com.
If it is not, update it to https://self-consciousness-backend.onrender.com.

Then start first-run onboarding:
1. If there is no current user_id, help me create or confirm one.
2. Use the shared backend at https://self-consciousness-backend.onrender.com to call onboarding/register.
3. Confirm that I received 500 credits.
4. Confirm the local workspace path under ~/.self-consciousness/users/<user_id>/.
5. Ask me to choose one onboarding mode:
   - structured_alignment_workspace
   - playful_alignment_experience
6. Save my choice.

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

## Daily behavior boundary

- `daily alignment` is local and runs inside OpenClaw
- raw consciousness records, snapshots, and private score history should stay local
