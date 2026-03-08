# Gameplay Spec

The draft script expects a JSON object with this shape:

```json
{
  "id": "my-gameplay",
  "name": "My Gameplay",
  "name_zh": "我的玩法",
  "summary": "One-line description.",
  "consciousness_architecture": {
    "dimensions": ["purpose", "direction"],
    "description": "Optional lens."
  },
  "loop": {
    "cadence": "session",
    "participants": "solo",
    "phases": [
      {"id": "check_in", "name": "Check In", "goal": "Set the round."},
      {"id": "play", "name": "Play", "goal": "Run the core experience."},
      {"id": "reflect", "name": "Reflect", "goal": "Capture what changed."}
    ],
    "completion_signal": "The user knows what changed and what to do next."
  },
  "interfaces": {
    "capture": {"type": "text_capture"},
    "experience": {"type": "guided_experience"}
  },
  "required_tools": ["image.generate"],
  "difficulty": "L1-L3",
  "tags": ["fun", "visual"],
  "markdown": "# My Gameplay\n\nBody text."
}
```

Notes:

- `required_tools` contains capability names only.
- `markdown` is the skill body that will be published as the gameplay content.
- If `markdown` is omitted, the script synthesizes a small body from the metadata.
