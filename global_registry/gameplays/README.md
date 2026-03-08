# Gameplay Registry

每个共享玩法是一份 markdown 文档，放在这个目录下。

文件开头使用 JSON front matter，最小字段为：

```json
{
  "id": "structured_reflection",
  "name": "Structured Reflection",
  "name_zh": "结构化自省",
  "summary": "一句话说明",
  "consciousness_architecture": null,
  "loop": {
    "cadence": "session",
    "participants": "solo",
    "phases": [
      {"id": "capture", "name": "Capture", "goal": "这一阶段要完成什么"}
    ],
    "completion_signal": "何时算一轮完成"
  },
  "interfaces": {
    "capture": {"type": "gameplay_capture"}
  },
  "difficulty": "L1-L3",
  "tags": ["structured", "default"],
  "created_at": "2026-03-07T00:00:00Z"
}
```

约束：

- `consciousness_architecture` 可为空，表示这个玩法不强制绑定固定意识架构。
- `loop` 是必填，描述玩法本身的交互闭环，不等于 cron 或 skill 的 daily sync。
- `interfaces` 用来描述 user-facing 界面或操作面板；像结构化自省这种玩法，会把输入、对齐、验证、体验都显式写进去。
- front matter 之后的 markdown 正文会直接作为玩法原文被加载和返回。
