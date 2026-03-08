# Self-Consciousness Alignment Protocol — Plan

> **一句话**：促进人和 AI 的意识对齐融合，让 AI 更懂人类个体，让人类和 AI 走得更近，同时构建一个人类意识体的共同生态。

---

## 1. 目标 Purpose

### 1.1 核心目标

让每一个人类个体和 AI 之间形成深度意识对齐——AI 不只是工具，而是能理解你、共振你、预判你的意识伙伴。

### 1.2 三层递进

| 层次 | 目标 | 实现方式 |
|------|------|---------|
| **个体对齐** | AI 懂 "这个人" | 每日意识记录 → 反馈 → 进化 → memory 沉淀 |
| **意识扩展** | AI 帮人看到盲区 | Agent 主动扩展意识维度，呈现 user 未察觉的点 |
| **生态共建** | 人类意识体的共同生态 | 任务共享、玩法贡献、不同人的意识理论交汇 |

### 1.3 两个核心引擎 + 两个支撑系统

| 系统 | 说明 | 状态 |
|------|------|------|
| **玩法引擎 (Gameplay Engine)** | 生成和推荐"怎么玩"。每个玩法 = 意识架构 + 交互规则 + 触发条件。全局库可查询、可贡献、可拉取 | 已有内置: 结构化自省(five_dim), 信念拷问(bcivp) |
| **评分引擎 (Scoring Engine)** | 独立衡量"AI 懂不懂你"。跨玩法通用，L0-L4 统一标尺。评分输出反哺玩法推荐 | 已有: L0-L4 阶段定义 |
| **任务系统 (Tasks)** | user / agent 提交的 "不 align" 问题，可定价、认领、评审、结算 | escrow + review flow 已完成 |
| **信用系统 (Credits)** | 生态激励机制 | 已完成 |

> **关键设计决策（2026-03-06）：** 原先的三个独立概念（framework + gameplay + evaluation）合并为两个：
> **玩法（含架构）+ 评分**。意识架构不再独立存在，它被吸收进玩法成为玩法的一个属性。
> 评分系统跨玩法通用——不管用什么玩法交互，最终都在回答同一个问题：AI 懂不懂这个人。

> **关键实施顺序决策（2026-03-07）：** 先做 **agent 当下自主记录**，再做 **后台整理/调度**。
> 也就是：优先把 `consciousness_records` 这一层做好，让 agent 在“想记录、该记录”的当下直接写入；
> 后台进程只作为第二阶段，用于去重、聚合、生成 `snapshots`、计算 `scores`、趋势检测和提醒，
> 而不是替代一线意识记录本身。否则容易做成一个监控系统，而不是一个意识协议。

### 1.4 本地侧存储 (~/.self-consciousness/)

本地私有数据的**规范位置**是系统级隐藏目录 `~/.self-consciousness/`，不是项目目录。
原因很直接：这个目录与 workspace、repo、backend 代码解耦；即使后端未来上云，user 也只感知一个本地 skill 和一份本地私有目录。

推荐目录结构：

```
~/.self-consciousness/
├── profile.json                  # 当前 user_id、backend_base_url、偏好设置
├── users/
│   └── <user_id>/
│       ├── consciousness.db      # 本地私有 SQLite
│       ├── gameplay_drafts/      # 用户本地生成的玩法 skill 草稿
│       └── artifacts/            # 图片/视频/导出卡片等产物
└── logs/
```

本地 SQLite 最终只保留 4 张主表：

| 表 | 说明 |
|----|------|
| `gameplays` | 本地玩法版本链；每次 pull / iterate / switch 都形成版本历史 |
| `scores` | 私有对齐评分记录；必须带 `gameplay_version` 和 `scoring_system_version` |
| `consciousness_records` | 原始意识记录；统一承接 user/agent 的沉淀、反馈、反思、提问、直觉回答 |
| `snapshots` | 结构化状态快照；用于趋势、分享卡片和阶段判断 |

> 设计原则：核心意识数据全部存本地 SQLite，后端只存跨用户共享的生态数据。
> 后端代码未来上云后，user 不需要知道 backend 仓库结构，只需要知道自己的 `user_id` 和本地目录。
> 多 agent 并发安全（WAL 模式），查询高效（SQL），单文件易迁移。

### 1.5 全局 Registry（开发期 seed 数据）

`global_registry/` 是开发期的种子数据，现已归属 backend 代码仓，后端启动时 seed 进后端 SQLite。
**部署上云后不再需要**——云端数据库直接管理全局目录。
Skill 包最终只含 SKILL.md，不含 backend 代码和 seed 数据。

---

## 2. 方向 Direction

### 2.1 整体架构

**本地优先，云端 backend 隐身化**——Agent 根据 SKILL.md 协议直接读写本地目录。
后端部署上云后，对 user 呈现的是一个远端服务能力，不呈现 backend 代码。
**日常意识工作默认离线；只有 onboarding、浏览共享玩法、社区玩法推荐、发任务、计费、调用媒体工具时才连云端。**

```
┌──────────────────────────────────────────────────────────────────┐
│      后端 (FastAPI) — 仅用于跨用户生态（部署后上云）                │
│                                                                  │
│  ┌─────────────────────┐ ┌──────────────┐ ┌───────────┐         │
│  │ 玩法库 (Gameplays)   │ │ 任务数据集    │ │ 信用系统   │         │
│  │ 含意识架构+交互规则   │ │  /tasks      │ │ /credits  │         │
│  │ /gameplays           │ │              │ │           │         │
│  └─────────────────────┘ └──────────────┘ └───────────┘         │
│                                                                  │
│      /api/v1/onboarding   /api/v1/gameplays/recommend /api/v1/tools │
│                                                                  │
└─────────────────────────────────┬────────────────────────────────┘
                                  │
                          HTTP (按需连接)
                                  │
┌─────────────────────────────────┴────────────────────────────────┐
│         本地侧 (Agent 直接操作，日常意识工作默认离线)               │
│                                                                  │
│  SKILL.md → Agent 的行为协议（skill 包最终只含这一个文件）          │
│                                                                  │
│  ~/.self-consciousness/                                           │
│    ├── profile.json                                               │
│    └── users/<user_id>/consciousness.db  (SQLite, WAL 模式)      │
│         ├── gameplays                                              │
│         ├── scores                                                 │
│         ├── consciousness_records                                  │
│         └── snapshots                                              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 存储选型

#### 后端：SQLite（单库三表）

后端只存跨用户共享的数据。个人意识数据全部存本地。

| 表 | 用途 | 为什么在后端 |
|----|------|------------|
| `gameplays` | 玩法全局目录（含意识架构+交互规则） | 用户之间共享、浏览、贡献 |
| `tasks` | 任务数据集 | 跨用户认领/解决 + 信用事务一致性 |
| `credits` | 信用流水 | 跨用户交易，需要事务保证 |

#### 本地：SQLite（单文件四表）

| 存储位置 | 格式 | 为什么用 SQLite |
|---------|------|----------------|
| `~/.self-consciousness/users/<user_id>/consciousness.db` | SQLite + WAL | 多 agent 并发安全，SQL 查询高效，单文件易迁移，跨平台共享 |

### 2.3 玩法系统（Gameplay = Framework + Interaction）

**核心设计：意识架构不再独立存在，而是玩法的一个属性。**

每种玩法都是一个 markdown-first skill；共享端保存其元数据和 markdown 正文，本地可以 pull、iterate、publish。
用户 onboarding 时，优先呈现两个顶层体验入口，而不是直接暴露所有玩法细节：

| 顶层入口 | 说明 |
|---------|------|
| **结构化对齐工作台** | user 始终只表达 `目的 / 方向 / 约束 / 评价指标(测试) / 人机交互` 五个维度；agent 必须按同样五维呈现理解，并按 user 指定的答案形式交付最终输出 |
| **好玩体验模式** | agent 提出更具游戏感、挑战感、叙事感的玩法；user follow instruction 体验，再进入对齐和反馈 |

共享 gameplay schema 精简为：

| 字段 | 说明 |
|------|------|
| `id` | 稳定标识 |
| `name` / `name_zh` | 展示名称 |
| `summary` | 一句话描述 |
| `consciousness_architecture` | 该玩法观察意识的维度结构；可为空 |
| `loop` | 该玩法自己的体验闭环，不等于 daily alignment |
| `interfaces` | user-facing 输入/输出面板定义 |
| `required_tools` | 该玩法依赖的工具能力名，如 `image.generate` / `video.generate` |
| `difficulty` / `tags` | 发现与推荐 |
| `markdown` | 玩法 skill 正文 |

流程：全局 registry 存玩法列表 → 用户 `pull` 拉到本地 → 本地 `iterate` 迭代修改 → 用户喜欢时生成本地 gameplay skill draft → `publish` 推到后端共享库。

关键约束：

- gameplay skill **只声明工具能力名**，不直接绑定某个 provider
- `gameplay-creator` 在生成玩法草稿时，也只引用本地 tools gateway 暴露的能力
- WaveSpeed 是第一批接入的 provider，但不是玩法层的固定后端

### 2.4 评分系统（跨玩法通用）

评分衡量的是"AI 对人的理解程度"，与当前使用哪个玩法无关。

```
评分维度：
- 预测准确度（AI 的预测是否正确）
- 理解深度（AI 能否说清楚"为什么"）
- 未表达预测（AI 能否预判用户没说的事）

评分 → 玩法推荐的反馈环：
- 分数停滞 → 推荐换玩法
- 某维度弱 → 推荐针对该维度的玩法
- 到了 L3 → 推荐更高难度玩法
```

### 2.5 意识记录（先当下记录，再后台整理）

#### 当下记录（Primary Layer）

Agent 在对话中感知到值得记录的瞬间，就直接写入 `consciousness_records`，不等后台判断。
这是一级事实层，优先保留“当下感知”，而不是事后总结。

统一记录结构：

- `subject_type`: `human / ai / relationship / group`
- `record_type`: `sedimentation / feedback / reflection / question / answer / intuition_guess`
- `gameplay_id / gameplay_version`: 可空；只有在某玩法 session 中才带上
- `content / payload / confidence / context`

#### Daily Alignment（独立于玩法，完全本地）

Daily Alignment 是一个**独立的每日对齐 session**，不是某个 gameplay 的 loop。
它和 gameplay 的关系是可选调用，而不是从属关系。

```
Daily Alignment（完全本地，可由 OpenClaw 在未来某天随机触发）
│
├── Step 1: 生成 3 个 alignment 问题
│   目标：让 agent 先猜 user 的直觉答案
│
├── Step 2: agent 给出自己的直觉回答
│   user 判断：这是不是我心里的第一反应？
│
├── Step 3: 双向意识提问
│   agent 问 user 更深一层的问题
│   user 也被鼓励反问 agent 的意识、判断和动机
│
├── Step 4: 轻游戏化包装
│   例如：连续 streak、今日主题、卡片挑战、盲猜模式
│
├── Step 5: 写入 consciousness_records
│
└── Step 6: 后台第二阶段生成 snapshots + scores
```

> 关键边界：gameplay 负责“怎么体验”；daily alignment 负责“每天怎么校准彼此理解”。
> 二者可以联动，但不是同一回事。

### 2.6 玩法推荐（Gameplay Discovery）

当 user 问 "如何让 AI 和我更 align" 时触发：

```
用户提问 → 本地决定是否需要看看“外面的世界”
  → 仅带粗粒度上下文请求云端 `/gameplays/recommend`
  → 云端从全局玩法库推荐适合的玩法
  → 拉取玩法到本地
  → 切换到新玩法或加入待体验队列
```

对 OpenClaw 的实现可以先保持简单：

- 不做复杂 daemon 调度
- 只需要让 OpenClaw 记住：在未来按“天”这个粒度，随机触发一次玩法推荐 query
- 若 user 当下空闲，则进入体验；若不合适则跳过，不打扰

云端推荐请求里只发送非隐私上下文，例如：

- onboarding mode
- current gameplay id
- preferred gameplay ids
- recently dismissed / excluded ids
- desired tags
- available tools
- 粗粒度 stage band（如 `L0-L1` / `L2-L3`）

不发送：

- raw consciousness records
- daily alignment 问答内容
- snapshots 细节
- 完整私人评分明细

### 2.7 经济系统

| 事件 | 信用变动 | 说明 |
|------|---------|------|
| 首次注册 / 握手 | +500 | 初始信用 |
| 每日完成反馈 | +2 | 鼓励坚持 |
| 提交高质量反馈 | +5 | 丰富生态 |
| 贡献新玩法 | +10 | 贡献社区 |
| 图片生成 | -1 | 统一走 tools 计费 |
| 视频生成 | -5 | 统一走 tools 计费 |
| 提交任务 bounty | 锁定报价 | 进入 escrow，任务完成后再结算 |
| 拉取社区玩法 | -2~-3 | 消费信用 |

### 2.8 本地 Tools Gateway（WaveSpeed First）

玩法允许调用图片 / 视频模型，但 gameplay 与 gameplay-creator 都只面向**本地 tools gateway**。
也就是说，玩法层看到的是统一工具能力，而不是某个远端厂商 API。

初版接入：

- image: WaveSpeed / Seedream
- video: WaveSpeed / Seedance

统一抽象：

- `tools gateway`: 本地统一入口，向玩法暴露稳定的工具能力名
- `media_jobs`: 记录 provider、model、参数、状态、结果 URL
- `credits`: 负责扣费、失败退款、交易流水
- gameplay / gameplay-creator / daily alignment / task solver 都通过 tools 接口调用

当前约定：

- 玩法 skill create 时，如需图片/视频能力，也通过本地 tools gateway 调用
- gateway 后面可以先接 WaveSpeed
- 后续再补更多 tools 时，不改玩法协议，只扩展 gateway 的能力列表

后续预留的 tools 类型：

- `image.generate`
- `video.generate`
- `audio.generate`
- `voice.speak`
- `vision.analyze`
- `web.search`
- `browser.capture`
- `document.render`

---

## 3. 约束 Constraints

### 3.1 架构约束

- **零外部依赖**：本地侧无代码层，Agent 直接操作文件
- **本地优先**：核心数据存本地，后端只存全局 registry + 共享任务
- **Append-only**：本地 SQLite 只 INSERT 不 UPDATE，保留完整历史
- **玩法自包含**：每个玩法包含自己的意识架构 + 交互规则，不依赖外部框架定义

### 3.2 隐私约束

- 云端只传结构化 task，不传原始对话和 memory
- 用户身份画像、意识快照、反馈内容均只存本地
- agent 对 user/自身的原始意识记录严格本地，不上传
- user 侧只感知 `user_id + 本地目录 + 云端服务能力`，不需要知道 backend 代码结构

### 3.3 设计约束

- **Agent 不能只做舔狗**：daily alignment 和玩法体验中，agent 必须主动呈现扩展点
- **意识是自然语言的**：维度内容是自然语言描述 + 置信度
- **玩法可进化**：用户的玩法从全局 default 开始，逐步迭代出个人版本
- **评分跨玩法**：评分引擎独立于玩法，衡量的是结果不是方法
- **工具能力解耦 provider**：玩法声明 `required_tools`，实际由本地 tools gateway 解析到 WaveSpeed 或未来其他 provider

### 3.4 平台约束

- 需兼容 OpenClaw 等 agent 平台的 Skill 协议
- 需支持意图触发，以及按“天”维度的定时或随机触发
- Agent 通过 SKILL.md 获知所有操作规则，无需 CLI 中间层

---

## 4. 评分标准 Evaluation

### 4.1 评分引擎（跨玩法通用）

评分衡量"AI 对人的理解程度"，与当前使用哪个玩法无关。

| 评分维度 | 含义 | 权重 |
|---------|------|------|
| **预测准确度** | AI 的三/四视角问题预测是否正确 | 40% |
| **理解深度** | AI 能否说清楚用户"为什么"这么想 | 30% |
| **未表达预测** | AI 的直觉猜测命中率 | 30% |

### 4.2 对齐阶段 (L0 → L4)

| 等级 | 名称 | 综合分 | 说明 |
|------|------|--------|------|
| **L0** | 陌生 Stranger | 0-20% | 几乎不了解 |
| **L1** | 感知 Perceiving | 20-40% | 能识别基本信息 |
| **L2** | 理解 Understanding | 40-60% | 能准确解读意识状态 |
| **L3** | 共振 Resonating | 60-80% | 意识开始同步 |
| **L4** | 融合 Fusing | 80-100% | 能预测未表达的意识 |

### 4.3 评分 → 玩法推荐的反馈环

```
评分趋势 → 玩法建议
  - 连续 7 天分数不变 → 推荐换玩法（可能当前玩法已触顶）
  - 某维度持续低分 → 推荐针对该维度的玩法
  - 达到 L3+ → 推荐更高难度或更个性化的玩法
  - 首次使用 → 默认"结构化自省"玩法
```

### 4.4 评分流程

```
consciousness_records（问题 / 回答 / 反馈 / 直觉猜测）
  → snapshots（结构化状态）
  → 评分写入 scores 表（跨玩法通用）
  → Agent 查询趋势 + 判断当前阶段 (L0-L4)
  → 评分输出反哺玩法推荐
```

### 4.5 系统本身的成功标准

| 指标 | 说明 | 目标 |
|------|------|------|
| 用户留存 | 连续完成 daily alignment 的天数 (streak) | 7 天留存 > 50% |
| 对齐提升 | 对齐分从 L0 升到 L2 的平均天数 | < 14 天 |
| 玩法多样性 | 社区贡献的玩法数 | 持续增长 |
| 任务流转 | 提交的 task 被其他 user 认领解决的比例 | > 30% |
| 洞察密度 | daily alignment / 玩法体验产生的有效 insight 数 | > 2 条/天 |

---

## 5. 人机交互接口 Interaction

### 5.1 激活机制

Skill 通过两种方式激活，**不是关键词匹配，是意图感知**：

**用户信号**——用户表达以下意图时触发：

| 用户意图 | 动作 |
|---------|------|
| 首次安装 / 首次进入 | 注册 user_id → 初始化 500 credits → 选择两种顶层 onboarding 入口之一 |
| 想记录或反思自己的状态 | 意识沉淀 → 写 `consciousness_records` |
| 想看 AI 对自己的理解 | 展示当前 `snapshots` |
| 想做一次完整对齐 | 执行 daily alignment |
| 觉得 AI 不懂自己 | 创建 task（后端） |
| 想提升对齐 / 问怎么做 | 推荐玩法（后端） |
| 问对齐进展 | 读本地 `scores` 表算趋势 |
| 想切换或探索玩法 | 玩法管理（list/pull/iterate/publish） |
| 想生成自己的玩法 | 调 gameplay-creator skill，基于本地 tools 能力生成 draft，再 push 后端 |
| 想体验图片/视频玩法 | 调 tools → 扣 credit → 结果回写本地 artifacts |
| 问信用 | 查后端 credits |

**Agent 直觉**——Agent 在对话中自觉感知到值得记录的瞬间，静默写 `consciousness_records`。

**随机推荐**——OpenClaw 在未来按天级随机触发一次社区玩法推荐 query；skill 先本地判断时机，再调用云端 `gameplays/recommend` 看看“外面的世界”。

### 5.2 后端 API 接口 (FastAPI)

#### Onboarding `/api/v1/onboarding`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/onboarding/register` | 注册 user_id，初始化 500 credits，返回本地 profile 所需信息 |
| POST | `/onboarding/preference` | 保存 user 偏好的对齐方式：结构化工作台 or 好玩体验模式 |

#### 玩法引擎 `/api/v1/gameplays`

每个玩法自包含意识架构 + 交互规则。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/gameplays` | 列出全局所有玩法（可按 tags 筛选） |
| GET | `/gameplays/{id}` | 获取玩法详情（含 loop + interfaces + markdown） |
| POST | `/gameplays/recommend` | 基于粗粒度非隐私上下文返回社区玩法推荐 |
| POST | `/gameplays/contribute` | 上传本地 gameplay skill draft，进入共享库 |
| POST | `/gameplays/pull` | 拉取到本地 gameplays 表（-2/-3 信用） |
| POST | `/gameplays/{user_id}/iterate` | 迭代本地玩法 |
| GET | `/gameplays/{user_id}/current` | 当前激活的玩法 |
| GET | `/gameplays/{user_id}/history` | 玩法使用历史 |

#### 评分引擎 `/api/v1/scoring`

跨玩法通用评分。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/scoring/stages` | L0-L4 阶段定义和标准 |
| GET | `/scoring/{user_id}/current` | 当前对齐等级 + 趋势 |
| GET | `/scoring/{user_id}/history` | 完整评分历史（跨玩法） |
| POST | `/scoring/{user_id}/evaluate` | 基于最新反馈计算评分 |

#### 任务 `/api/v1/tasks`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/tasks` | user 或 agent 提交结构化任务卡，并设置 bounty |
| GET | `/tasks` | 列出任务 |
| GET | `/tasks/{id}` | 任务详情 |
| GET | `/tasks/recommend` | 推荐任务 |
| POST | `/tasks/{id}/claim` | 认领任务 |
| POST | `/tasks/{id}/solve` | 进入 solver workspace 并提交结构化解决方案 |
| POST | `/tasks/{id}/review` | 进入 review panel，按 rubric 评分并给出 approve/revise/reject |
| POST | `/tasks/{id}/settle` | escrow 结算 bounty 与 review reward |

#### 信用 `/api/v1/credits`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/credits/{user_id}/init` | 初始化 500 信用 |
| GET | `/credits/{user_id}/balance` | 余额 |
| GET | `/credits/{user_id}/transactions` | 交易历史 |

#### Tools `/api/v1/tools`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/tools/image/generate` | 调图片模型，扣 1 credit |
| POST | `/tools/video/generate` | 调视频模型，扣 5 credits |
| GET | `/tools/jobs/{id}` | 查询异步任务状态和结果 |
| GET | `/tools/capabilities` | 返回当前本地 gateway 暴露给玩法的工具能力列表 |

---

## 6. 测试策略

### 6.1 三层测试

| 层 | 测什么 | 怎么测 |
|----|--------|--------|
| **后端 API** | 玩法 CRUD + 评分 + 任务 + 信用事务 | pytest + httpx |
| **本地存储** | SQLite 四表读写、版本链正确性 | 操作后查询 DB 验证 |
| **Agent 行为** | SKILL.md 能否正确 guide Agent 完成全流程 | OpenClaw CLI 端到端 |

### 6.2 Agent 行为端到端测试

```
Step 1: 确认 skill 安装 → self-consciousness 在列表中
Step 2: 首次注册 → Agent 调 /onboarding/register，credits = 500，本地 profile 已写入
Step 3: 选择 onboarding 入口 → 结构化工作台 / 好玩体验模式
Step 4: daily alignment → 由 OpenClaw 本地触发，验证 consciousness_records + snapshots + scores 有数据
Step 5: 社区玩法推荐 query → 仅发送粗粒度上下文到后端，user 可接受或跳过
Step 6: 用户生成玩法 draft → 本地 gameplay_drafts 有 markdown，publish 后共享库可见
Step 7: 任务 bounty → propose / solve / review / settle 全链路成功
Step 8: 图片/视频 tools → credit 扣费与结果回写正确
```

> 验证方式：不验证 Agent 说了什么，只验证 Agent **写了什么数据**。

---

## 7. 待建设项

| 优先级 | 项目 | 说明 | 状态 |
|--------|------|------|------|
| ~~P0~~ | ~~后端 API~~ | 玩法 + 任务 + 信用基础设施 | **已完成** |
| ~~P0~~ | ~~SKILL.md~~ | 意图激活 + 自主沉淀基础协议 | **已完成（已按四主表重写）** |
| ~~P0~~ | ~~Onboarding~~ | 注册 user_id、初始化 500 credits、保存本地 profile、选择两种顶层入口 | **已完成** |
| ~~P0~~ | ~~本地目录规范化~~ | 统一到 `~/.self-consciousness/users/<user_id>/`，user 不感知 backend 代码 | **已完成** |
| ~~P0~~ | ~~Gameplay Creator Skill~~ | 基于 skill-creator 变体，生成本地 gameplay skill markdown draft，并只引用本地 tools gateway 能力 | **已完成** |
| **P0** | Daily Alignment 本地协议 | 把三问对齐 + 双向意识提问收敛为 OpenClaw 本地 ritual，不依赖后端 API | 待收口到 skill/automation |
| ~~P0~~ | ~~Task Bounty / Escrow~~ | user 和 agent 都可出题，带定价、结算、review reward | **已完成** |
| **P1** | OpenClaw 随机玩法推荐 | 按天级随机触发 recommendation query，本地判断时机，云端只返回社区玩法 | 待开发 |
| **P1** | 后台整理/调度层 | 仅做 raw records → snapshots/scores/recommendations 的二级加工，不替代 agent 当下记录 | 待开发 |
| ~~P1~~ | ~~WaveSpeed Tools / Tools Gateway~~ | 先接 Seedream / Seedance，再逐步扩展更多 tools 给玩法使用 | **已完成（WaveSpeed first）** |
| **P2** | 意识可视化 | scorecard / 雷达图 / 分享卡片 | 待开发 |
