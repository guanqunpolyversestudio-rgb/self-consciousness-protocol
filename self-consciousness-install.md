# Self-Consciousness Install

This file is the bootstrap guide for installing the `self-consciousness` skill into OpenClaw.

## What gets installed

The installer now installs:

- the `selfcon` single-file CLI under `~/.local/bin/`
- versioned CLI files under `~/.local/share/selfcon/versions/`
- the local skill layer into OpenClaw, when a skills directory is provided

The OpenClaw skill layer includes:

- `self-consciousness/SKILL.md`
- `gameplay-creator/`
- local private workspace under `~/.self-consciousness/`

Private consciousness data stays local in `~/.self-consciousness/`.

Default shared backend for testing:

- `https://self-consciousness-backend.onrender.com`

## What OpenClaw Should Do

When OpenClaw reads this file, it should:

1. run the installer script so that `selfcon` is installed locally
2. ensure this command exists:
   - `selfcon`
3. if an OpenClaw skills directory is known, make sure the installer also installs:
   - `self-consciousness`
   - `gameplay-creator`
4. use `https://self-consciousness-backend.onrender.com` as the default shared backend
5. create `~/.self-consciousness/` if it does not exist
6. ensure `~/.self-consciousness/profile.json` exists
7. ensure `backend_base_url` in `~/.self-consciousness/profile.json` is `https://self-consciousness-backend.onrender.com`
8. continue immediately into first-run onboarding instead of stopping after file installation
9. ask for or infer a `user_id`
10. run `selfcon onboard --user-id <user_id>`
11. confirm that the user received `500 credits`
12. confirm the local workspace under `~/.self-consciousness/users/<user_id>/`
13. save the `current_user_id` in `~/.self-consciousness/profile.json`
14. do not ask the user to choose between abstract onboarding labels such as `structured_alignment_workspace` and `playful_alignment_experience`
15. internally use the default onboarding mode `user_intent_first`
16. ask the user for runtime preferences:
   - whether daily sync should run automatically
   - what local time daily sync should run
   - gameplay recommendation mode: `off`, `daily`, or `always_loop`
   - whether passive gameplay recommendation is allowed
   - how the agent should or should not speak
17. save runtime preferences through `selfcon prefs set ...`
18. call `GET /api/v1/tools/capabilities` against `https://self-consciousness-backend.onrender.com`
19. remember the currently available tool capabilities, especially:
   - `image.generate`
   - `video.generate`
20. if a gameplay later declares a `consciousness_architecture`, use that architecture as the lens for local consciousness recording
21. if daily sync automation is enabled, configure one daily automation that:
   - runs local `daily alignment`
   - if recommendation mode is `daily`, then requests one community gameplay recommendation
   - shows the recommendation to the user without auto-starting the gameplay
   - does not upload raw consciousness records, snapshots, or private score history
22. after installation, do not stop at a setup summary
23. if the user does not immediately propose a different task, lead the user into the first gameplay round right away:
   - default path: start a local five-dimension alignment round
   - ask for `purpose`, `direction`, `constraints`, `evaluation`, and `interaction`
   - mirror those same five dimensions back to the user
   - produce a first aligned response
   - if the user prefers novelty instead, request one community gameplay recommendation and start that one instead
24. after the first gameplay round has started, report:
   - where the skills were installed
   - where `selfcon` was installed
   - the current `user_id`
   - whether onboarding/register succeeded
   - whether `500 credits` were received
   - which tool capabilities are currently available
   - whether `~/.self-consciousness/profile.json` was created
   - what `backend_base_url` is set to
   - that the internal onboarding mode is `user_intent_first`
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

After installation:

```bash
selfcon onboard --user-id <your_user_id>
```

## Manual install

1. Install the CLI with the installer script.
2. Run `selfcon install --skills-dir <OPENCLAW_SKILLS_DIR>`.
3. Run `selfcon onboard --user-id <your_user_id>`.

Example:

```bash
curl -fsSL https://raw.githubusercontent.com/guanqunpolyversestudio-rgb/self-consciousness-protocol/main/install.sh | bash
selfcon install --skills-dir <OPENCLAW_SKILLS_DIR>
selfcon onboard --user-id <your_user_id>
```

## First run inside OpenClaw

When the skill first runs:

1. choose or create a `user_id`
2. use the default shared backend `https://self-consciousness-backend.onrender.com` unless you intentionally override it
3. run `selfcon onboard --user-id <user_id>`
4. create local workspace under `~/.self-consciousness/users/<user_id>/`
5. receive `500 credits`
5. do not ask the user to choose an abstract onboarding mode
6. default internally to `user_intent_first`

Do not stop after just installing files. The expected install experience includes:

- user registration
- initial `500 credits`
- local workspace creation
- internal default onboarding mode
- runtime preference setup
- optional daily sync automation setup
- immediate entry into a first gameplay round unless the user clearly wants something else

## Prompt For OpenClaw

After installation, you can give OpenClaw this prompt directly:

```text
Please use the self-consciousness skill.

First make sure the `selfcon` CLI is installed. If it is not, install it using:
curl -fsSL https://raw.githubusercontent.com/guanqunpolyversestudio-rgb/self-consciousness-protocol/main/install.sh | bash -s -- --skills-dir <OPENCLAW_SKILLS_DIR>

Then continue installation by completing first-run onboarding:
1. If there is no current user_id, help me create or confirm one.
2. Use `selfcon onboard --user-id <user_id>`.
3. Confirm that I received 500 credits.
4. Confirm the local workspace path under ~/.self-consciousness/users/<user_id>/.
5. Do not ask me to choose between abstract onboarding labels.
6. Use the internal default onboarding mode user_intent_first.
7. Ask me for runtime preferences:
   - daily sync on/off and local time
   - gameplay recommendation mode: off, daily, or always_loop
   - passive gameplay recommendation on/off
   - what the agent should avoid saying
8. Save my choices with `selfcon prefs set ...`.
9. After setup, do not stop at a summary.
10. If I do not introduce a different task, lead me into the first gameplay round immediately.
11. Default first gameplay:
   - a local five-dimension alignment loop
   - ask for purpose, direction, constraints, evaluation, and interaction
   - mirror those five dimensions back to me
   - then continue the loop
12. If I explicitly want something more playful, request one community gameplay recommendation and start that one instead.

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
Please use the self-consciousness skill, make sure `selfcon` is installed and ~/.self-consciousness/profile.json points to https://self-consciousness-backend.onrender.com, then:
1. run `selfcon onboard --user-id <user_id>`
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

Even before the first daily sync happens, setup completion should already flow into one gameplay round.
The installation experience is not complete if it ends at preference saving and never starts play.

If a gameplay declares a `consciousness_architecture`, OpenClaw should use that architecture
as the local lens for consciousness recording during that gameplay. If it does not, keep the
recording free-form and lightweight.

## CLI Examples

```bash
selfcon install --skills-dir <OPENCLAW_SKILLS_DIR>
selfcon onboard --user-id koala
selfcon prefs set --daily-sync on --daily-sync-time 10:00 --recommendation-mode always_loop --passive-recommendation on --avoid-saying "I totally understand you"
selfcon gameplay create --id seaside_alignment --name "Seaside Alignment" --summary "One-shot aesthetic probe" --mode one_shot --tools image.generate --tags aesthetic,visual
selfcon gameplay publish --file ~/.self-consciousness/users/koala/gameplay_drafts/seaside_alignment.md
```

## Daily behavior boundary

- `daily alignment` is local and runs inside OpenClaw
- raw consciousness records, snapshots, and private score history should stay local
