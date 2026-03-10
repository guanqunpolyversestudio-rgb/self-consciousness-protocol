# Self-Consciousness Install

This file is only a bootstrap guide.

After bootstrap, the main runtime behavior should come from:

- `self-consciousness/SKILL.md`
- `gameplay-creator/SKILL.md`

## Bootstrap Goal

Install the local CLI, install the OpenClaw skills, run first-time onboarding, then enter the normal skill flow.

## Bootstrap Steps

1. Install `selfcon`:

```bash
curl -fsSL https://raw.githubusercontent.com/guanqunpolyversestudio-rgb/self-consciousness-protocol/main/install.sh | bash
```

2. Install the skills into OpenClaw:

```bash
selfcon install --skills-dir <OPENCLAW_SKILLS_DIR>
```

3. Complete first-time onboarding:

```bash
selfcon onboard --user-id <your_user_id>
```

4. After onboarding:
- confirm the local workspace under `~/.self-consciousness/users/<user_id>/`
- confirm the user received `500 credits`
- save runtime preferences with `selfcon prefs set ...`
- if the user does not immediately introduce another task, start the first gameplay round

5. After bootstrap, follow the installed `SKILL.md` files for normal behavior.

## Minimal OpenClaw Prompt

```text
Please bootstrap the self-consciousness system.

1. Install `selfcon` with:
   curl -fsSL https://raw.githubusercontent.com/guanqunpolyversestudio-rgb/self-consciousness-protocol/main/install.sh | bash
2. Install the OpenClaw skills with:
   selfcon install --skills-dir <OPENCLAW_SKILLS_DIR>
3. Run onboarding with:
   selfcon onboard --user-id <user_id>
4. Then follow the installed self-consciousness SKILL.md.
5. If I do not immediately introduce another task, start the first gameplay round.
```

## Notes

- `selfcon` is the user-facing interface.
- Private consciousness data stays local in `~/.self-consciousness/`.
- Shared backend details stay implicit unless explicitly debugging.
