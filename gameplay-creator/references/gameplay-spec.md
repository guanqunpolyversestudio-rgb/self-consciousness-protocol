# Gameplay Spec

The draft script expects a JSON object with this shape:

```json
{
  "id": "my-gameplay",
  "name": "My Gameplay",
  "name_zh": "我的玩法",
  "summary": "One-line description.",
  "mode": "one_shot",
  "tools": ["image.generate"],
  "tags": ["fun", "visual"],
  "metadata": {
    "output_contract": "return 5 images and one summary card"
  },
  "markdown": "# My Gameplay\n\nBody text."
}
```

Notes:

- `tools` contains capability names only.
- `mode` should normally be one of `one_shot`, `loop`, or `open`.
- `one_shot` means the gameplay normally ends after one run and waits for user feedback.
- `loop` means the gameplay is designed to continue across rounds until the user pauses or stops it.
- `mode` is still a hint; the real protocol lives in the markdown body.
- `metadata` is optional and can store any extra structure without expanding the fixed schema.
- if the gameplay needs an explicit consciousness lens, put it under `metadata.consciousness_architecture`
- `markdown` is the gameplay body that will be published as the gameplay content.
- If `markdown` is omitted, the script synthesizes a small body from the metadata.
