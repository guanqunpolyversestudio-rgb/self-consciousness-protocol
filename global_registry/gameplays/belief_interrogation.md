---
{
  "id": "belief_interrogation",
  "name": "Belief Interrogation",
  "name_zh": "信念拷问",
  "summary": "围绕显性信念和隐性行为做强对抗式循环，适合发现自我叙述和真实选择之间的偏差。",
  "consciousness_architecture": {
    "name": "BCIVP Lens",
    "description": "用 beliefs / confidence / intent / values / preference 五个维度拆解一条信念。",
    "dimensions": ["beliefs", "confidence", "intent", "values", "preference"]
  },
  "loop": {
    "cadence": "session",
    "participants": "solo",
    "phases": [
      {
        "id": "claim",
        "name": "Claim",
        "goal": "让 user 先给出一句明确主张，例如“我其实很重视长期主义”。"
      },
      {
        "id": "challenge",
        "name": "Challenge",
        "goal": "agent 追问反例、代价、延迟行动和隐藏收益。"
      },
      {
        "id": "contrast",
        "name": "Contrast",
        "goal": "把言语、行为和历史上下文摆在同一张桌子上比对。"
      },
      {
        "id": "score",
        "name": "Score",
        "goal": "记录这轮是否真的更接近真实信念，而不是更擅长解释。"
      },
      {
        "id": "rewrite",
        "name": "Rewrite",
        "goal": "把旧信念改写成更可验证的新表述，进入下一轮。"
      }
    ],
    "completion_signal": "本轮已经从一句口号，收敛成可验证的信念假设。"
  },
  "difficulty": "L2-L4",
  "tags": ["deep", "challenging", "psychological"],
  "created_at": "2026-03-07T00:00:00Z"
}
---

# 信念拷问

这个玩法适合已经有一定信任基础的 user。它不追求舒适，而追求把“我以为我相信的”和“我实际在做的”拆开。

## 适用场景

- 对齐进入平台期，需要更高压的玩法
- 用户经常给出价值观表述，但行动持续偏离
- 想确认某个决策到底是真想要，还是只是合理化

## Loop 产出

- 一条被改写过的信念
- 一组高压条件下的评分
- 下一轮要验证的反例或行为证据
