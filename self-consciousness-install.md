# Self-Consciousness Install

This file is the bootstrap guide for installing the `self-consciousness` skill into OpenClaw.

## What gets installed

Only the local skill layer is installed into OpenClaw:

- `self-consciousness/SKILL.md`
- `gameplay-creator/`
- local private workspace under `~/.self-consciousness/`

Private consciousness data stays local in `~/.self-consciousness/`.

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
2. create local workspace under `~/.self-consciousness/users/<user_id>/`
3. receive `500 credits`
4. choose one onboarding mode:
   - `structured_alignment_workspace`
   - `playful_alignment_experience`

## Daily behavior boundary

- `daily alignment` is local and runs inside OpenClaw
- raw consciousness records, snapshots, and private score history should stay local
