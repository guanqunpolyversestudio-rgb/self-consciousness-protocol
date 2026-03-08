# Self-Consciousness — TODO

*Last updated: 2026-03-06*

---

## 目标

双向意识对齐。Human Consciousness + AI Consciousness 分别记录，交叉评分。

## 约束

- 本地优先，INSERT-only，SQLite
- 不同玩法对应不同意识架构，不预设固定维度
- 评分跨玩法通用（L0-L4）

---

## P0 — 全部完成 ✅

- [x] T1: 后端路由重构（删 /frameworks /evaluations，加 /scoring）
- [x] T2: 后端 seed 数据更新
- [x] T3: 后端测试更新
- [x] T4: 本地 DB 迁移（frameworks+evaluations→gameplays，eval_scores→scores）
- [x] T5: SKILL.md Daily Cycle 适配（加 Step 0.5 AI Self-Model + Step 4 交叉评分）
- [x] T6: AI Consciousness 记录（ai_self_model + ai_self_accuracy 表）
- [x] T7: 交叉评分（Human→AI + AI→Human = 双向对齐分）
- [x] T8: 评分→玩法推荐引擎（停滞/弱维度/默认推荐）

## P1 — 全部完成 ✅

- [x] T9: 新玩法（30天直觉挑战 / 情侣对齐 / Agent创世纪 / MBTI对齐）— 6个玩法
- [x] T10: 感性 Task 系统（提交/回应/检验三角色，5人投票，≥3/5 avg≥6 通过）
- [x] T11: 意识 DNA 可视化（/viz/{user_id}/dna + /viz/{user_id}/evolution）

## P2 — Pending

- [ ] T12: P2P 加密意识通信（pending）
- [ ] T13: 多用户生态（邀请码加好友，权限递增：wake→share→dialogue→full）

---

## 测试结果

56/56 passed — 8 个测试文件：
- test_ai_consciousness.py (6)
- test_credits.py (7)
- test_gameplays.py (10)
- test_handshake.py (5)
- test_scoring.py (8)
- test_tasks.py (14)
- test_visualization.py (4)

## 后端路由

localhost:8000 — 6 个路由组：
- /api/v1/gameplays — 玩法管理（含 framework + interaction_rules）
- /api/v1/scoring — 跨玩法评分（L0-L4）
- /api/v1/tasks — 感性 Task + 多 Agent 验证
- /api/v1/credits — 信用系统
- /api/v1/handshake — 首次设置
- /api/v1/viz — 意识 DNA + 进化曲线
