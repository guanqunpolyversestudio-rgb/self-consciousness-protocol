---
name: gameplay-creator
description: Create or revise markdown-first gameplay drafts for self-consciousness. Use whenever the user wants to invent a new gameplay, turn a fun alignment experience into a shareable gameplay skill, or publish a local gameplay draft to the shared gameplay registry.
---

# Gameplay Creator

Create gameplay drafts as markdown files with JSON front matter. Keep the draft small, concrete, and publishable.

## What to produce

Every gameplay draft needs:

- `id`
- `name`
- `summary`
- optional `mode`
- optional `tools`
- optional `tags`
- optional `metadata`
- markdown body

Keep the fixed schema minimal. Put specific flow, tool instructions, and one-shot or looping logic in the markdown body. Use `metadata` only when a small amount of extra structure is genuinely helpful.

Default semantic expectations:

- `one_shot` gameplay should normally end after one run and ask for user feedback
- `loop` gameplay should make it obvious how to continue, pause, or stop
- user intent still overrides gameplay continuation
- if a gameplay needs explicit consciousness dimensions, store them under `metadata.consciousness_architecture`

## Workflow

1. Clarify the gameplay in product terms:
   - what the user experiences
   - whether it is one-shot, looping, or intentionally open
   - whether any tools are required
2. If tools are needed, only reference capability names such as `image.generate` or `video.generate`.
3. Prefer `selfcon gameplay create ...` for deterministic draft creation when the CLI is available.
4. Otherwise write a gameplay spec JSON file or inline JSON.
5. Run `scripts/create_gameplay_draft.py` to write the draft under the local user workspace.
6. If the user wants to publish it, prefer `selfcon gameplay publish --file <path>`.

## Constraints

- Do not bind gameplay drafts directly to providers like WaveSpeed.
- Prefer a small metadata surface over many fixed top-level fields.
- `structured_reflection` style gameplay should keep user and agent on the same dimensions.
- Use `references/gameplay-spec.md` when you need the field-level shape.

## Script

Use:

```bash
python3 gameplay-creator/scripts/create_gameplay_draft.py \
  --user-id <user_id> \
  --spec-file /path/to/spec.json
```

You can also pass `--spec-json '<json>'` for smaller drafts.
