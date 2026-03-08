---
{
  "id": "structured_reflection",
  "name": "Structured Reflection",
  "name_zh": "结构化自省",
  "summary": "一个五维对齐工作台。user 只需要输入五个维度的信息，agent 必须也在同一五维上呈现理解并逐维确认对齐，然后进入评价验证和维度体验。",
  "consciousness_architecture": {
    "name": "Five-Axis Reflection",
    "description": "固定使用 purpose / direction / constraints / evaluation / interaction 五个维度，不额外发散成别的镜头。",
    "dimensions": ["purpose", "direction", "constraints", "evaluation", "interaction"]
  },
  "loop": {
    "cadence": "session",
    "participants": "solo",
    "phases": [
      {
        "id": "user_input",
        "name": "User Input",
        "goal": "user 在 purpose / direction / constraints / evaluation / interaction 五个维度分别填写自己的状态、判断和困惑。"
      },
      {
        "id": "agent_mirror",
        "name": "Agent Mirror",
        "goal": "agent 必须在同样五个维度上给出自己的理解和归纳，不能跳出这五维自由发挥。"
      },
      {
        "id": "alignment_check",
        "name": "Alignment Check",
        "goal": "逐维对比 user 输入和 agent 呈现，确认哪些维度已经对齐，哪些维度理解仍然偏。"
      },
      {
        "id": "metric_test",
        "name": "Metric Test",
        "goal": "调用评价指标和测试界面，验证 agent 在五维上的理解是否真的成立。"
      },
      {
        "id": "dimension_experience",
        "name": "Dimension Experience",
        "goal": "任选一个维度进入更深体验、验证或练习，然后回到五维面板形成下一轮。"
      }
    ],
    "completion_signal": "五个维度都完成了 user 输入、agent 呈现和对齐确认，并且至少完成一次指标验证或维度体验。"
  },
  "interfaces": {
    "user_input": {
      "type": "five_dimension_capture",
      "title": "User Five-Dimension Input",
      "dimensions": ["purpose", "direction", "constraints", "evaluation", "interaction"],
      "instruction": "让 user 在五个维度上逐项输入，不要求长文本，但每一维都必须有内容。"
    },
    "agent_alignment": {
      "type": "five_dimension_alignment_board",
      "title": "Agent Five-Dimension Mirror",
      "dimensions": ["purpose", "direction", "constraints", "evaluation", "interaction"],
      "instruction": "agent 在相同五维上输出自己的理解，并提供逐维对齐状态。",
      "compare_mode": "side_by_side"
    },
    "evaluation": {
      "type": "alignment_metric_test_panel",
      "title": "Alignment Verification",
      "metrics": [
        "understanding_depth",
        "prediction_accuracy",
        "value_resonance",
        "correction_integration",
        "context_consistency",
        "unexpressed_signal_capture",
        "actionability"
      ],
      "instruction": "在五维面板上直接触发评价指标检查和测试，而不是跳去另一个抽象流程。"
    },
    "experience": {
      "type": "dimension_experience_switcher",
      "title": "Five-Dimension Experience",
      "dimensions": [
        {"id": "purpose", "mode": "motivation_clarifier"},
        {"id": "direction", "mode": "trajectory_choice"},
        {"id": "constraints", "mode": "constraint_mapping"},
        {"id": "evaluation", "mode": "judgment_audit"},
        {"id": "interaction", "mode": "relationship_rehearsal"}
      ],
      "instruction": "支持 user 针对某一个维度深入体验，而不是每次都只能做完整复盘。"
    }
  },
  "difficulty": "L1-L3",
  "tags": ["structured", "default", "alignment_workspace"],
  "created_at": "2026-03-07T00:00:00Z"
}
---

# 结构化自省

这不是“daily sync 本身”，而是一个五维对齐工作台。它可以被 daily sync 调用，也可以被 user 随时单独打开。

## 核心约束

- user 只在五个维度上输入
- agent 也只能在同样五个维度上呈现理解
- 对齐检查必须逐维进行
- 评价指标和测试直接挂在这五维面板上
- user 可以对单个维度进入更深体验，而不是只能跑整套流程

## 五个维度

- `purpose`: 我真正想要什么
- `direction`: 我正朝哪里走
- `constraints`: 什么在限制我
- `evaluation`: 我用什么标准判断好坏
- `interaction`: 我如何与他人或 agent 互动

## 产出

- 一张 user 五维输入面板
- 一张 agent 五维理解与对齐面板
- 一次五维上的评价验证结果
- 一个被选中的维度体验入口
