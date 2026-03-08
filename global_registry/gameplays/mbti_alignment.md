---
{
  "id": "mbti_alignment",
  "name": "MBTI Alignment",
  "name_zh": "MBTI对齐",
  "summary": "用人格维度做 baseline loop，同时检查 user 被理解程度和 agent 的自知度。",
  "consciousness_architecture": {
    "name": "MBTI Lens",
    "description": "以 E/I、S/N、T/F、J/P 四条维度作为低门槛起始镜头。",
    "dimensions": ["E_I", "S_N", "T_F", "J_P"]
  },
  "loop": {
    "cadence": "baseline",
    "participants": "solo",
    "phases": [
      {
        "id": "user_self_report",
        "name": "User Self Report",
        "goal": "user 先给出自己的人格偏向和例子。"
      },
      {
        "id": "ai_prediction",
        "name": "AI Prediction",
        "goal": "agent 预测 user 的人格分布，并说明依据。"
      },
      {
        "id": "ai_self_report",
        "name": "AI Self Report",
        "goal": "agent 也对自己做同样的维度自评。"
      },
      {
        "id": "compare",
        "name": "Compare",
        "goal": "比较 user 自评、agent 预测、user 对 agent 的评价三者差异。"
      },
      {
        "id": "calibrate",
        "name": "Calibrate",
        "goal": "把最大误差位点转成后续对齐假设。"
      }
    ],
    "completion_signal": "已经形成一张 baseline 对比图，并知道哪些人格判断最不可靠。"
  },
  "difficulty": "L0-L1",
  "tags": ["personality", "baseline", "test", "bidirectional"],
  "created_at": "2026-03-07T00:00:00Z"
}
---

# MBTI对齐

这是一个低门槛入口玩法。它的价值不在于 MBTI 本身绝对正确，而在于快速建立“我如何看自己、你如何看我、我如何看你”的三方校准。

## 适用场景

- 初次对齐，需要快速拉起 baseline
- 想先从轻结构化维度开始
- 想测 agent 的自知度，而不只是 agent 对 user 的理解

## Loop 产出

- baseline 对比图
- 一组起始评分
- 若干后续需要深挖的人格误差点
