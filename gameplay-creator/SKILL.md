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
- `loop`
- `interfaces`
- `required_tools`
- markdown body

`consciousness_architecture` is optional. Use it only when the gameplay truly depends on a stable lens.

## Workflow

1. Clarify the gameplay in product terms:
   - what the user experiences
   - what one loop looks like
   - whether there is a stable consciousness lens
   - whether any tools are required
2. If tools are needed, only reference capability names such as `image.generate` or `video.generate`.
3. Write a gameplay spec JSON file or inline JSON.
4. Run `scripts/create_gameplay_draft.py` to write the draft under the local user workspace.
5. If the user wants to publish it, send the generated markdown to `/api/v1/gameplays/contribute`.

## Constraints

- Do not bind gameplay drafts directly to providers like WaveSpeed.
- Prefer one clear loop over a bag of mechanics.
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
