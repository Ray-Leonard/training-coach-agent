# Training Coach Agent：老铁 Old-Iron

一个开源、模块化的 AI 健身教练系统。把本仓库链接交给一个已有的 Agent 后，
它可以维护营养数据库、管理 Fitness User Profile、追踪每日饮食、记录并分析已
确认的实际训练，以及管理训练计划草案，同时严格遵守各模块的数据沙箱。

> **开发中：** 模块 3–5 已可用于日常流程，但整个项目仍未达到生产环境标准，
> 也不能替代医疗服务。

> **AI Agent 上岗：** 安装协议见 [SETUP.md](SETUP.md)，安装完成后的 Training
> Coach runtime 遵守 [AGENTS.md](AGENTS.md)。

[English version](README.md)

## 这个项目提供什么

Training Coach 将 Agent 的运行身份和用户健身数据分开：

- **Agent Profile：** 宿主 profile 中的运行时 Soul、workspace、skills、provider
  配置和 gateway 集成；
- **Fitness User Profile：** 用户的身体数据、目标、TDEE、宏量素和每周设置，保存
  在 `data/user/` 下。

运行时与语言无关。安装期间由用户选择日常交流语言，最终 Soul 会被安装到当前
Agent Profile；仓库里的 Soul 文件始终只是只读示例。

## 模块一览

| # | 模块 | 状态 | 功能 |
|---|---|---|---|
| 1 | **Nutrition Database Management** | ✅ 已完成 | 管理个人食物库和餐单模板。 |
| 2 | **User Profile Management** | ✅ 已完成 | 执行 User Onboarding & Fitness Profile Creation，之后管理身体数据、目标、宏量素、TDEE 和每周训练/有氧元数据。 |
| 3 | **Diet Tracker** | ✅ 日常可用 | 对餐食做增删改查，汇报摄入与目标宏量素，并标注估算/手动能量赤字。 |
| 4 | **Training Analyzer** | ✅ 日常可用 | 保存已确认的实际训练，计算训练量、Epley 1RM、RPE、频率和 PR 标记。 |
| 5 | **Training Planning** | ✅ 日常可用 | 生成、校验和确认训练计划草案，并另存减量计划，不修改 Fitness User Profile。 |
| 6 | **Monthly Summary** | 📋 规划中 | 汇总训练、饮食、身体与目标趋势。 |
| 7 | **Proactive Reminder** | 📋 规划中 | 提供遵循时区、克制且不打扰的提醒。 |

系统严格区分训练计划和实际训练。每次日常打卡都要明确询问今天是 `training`
还是 `rest`，不能由日历或计划替用户回答。

## 安装流程

把本仓库链接交给一个能够 clone 仓库并配置 Agent Profile 的已有 Agent。安装分为
三个明确阶段：

```text
Phase 0 — Agent Profile Installation
  已有 Agent clone 仓库、创建并配置 trainingcoach、询问交流语言，
  并安装运行时 SOUL.md。

Phase 0.5 — Profile Handoff & Gateway Setup
  已有 Agent 邀请用户切换到 trainingcoach，并设置该 profile 的 gateway。

Phase 1 — User Onboarding & Fitness Profile Creation
  切换完成后，Training Coach 遵守 AGENTS.md；用户开始健身资料 onboarding
  时，才创建 data/user/profile.json。
```

已有 Agent 只在 Phase 0 和 Phase 0.5 期间读取 `SETUP.md`。切换完成后，Training
Coach runtime **不会读取 `SETUP.md`**，而是遵守 `AGENTS.md`、当前 profile 的
`SOUL.md` 和当前请求所需的 skill。

安装并完成 profile handoff 后，切换到新的 Training Coach profile，完成 gateway
setup，开启新对话，然后告诉它：

```text
开始我的健身资料 onboarding。
```

在 Phase 1 之前，`data/user/profile.json` 不存在是正常的。安装阶段创建的是
Agent Profile；之后的 User Onboarding 才会创建 Fitness User Profile。

## 数据与隐私

运行时用户数据位于 `data/` 并由 Git 忽略。凭据只能放在当前 Agent Profile 或
环境变量中，绝不能写入仓库。每个模块只拥有自己的数据沙箱，不得修改其他模块
的输出。

## 教练人设

教练名叫 **老铁 Old-Iron**——严格但真心希望你进步的健身老炮，运行时与语言无关。
人设和安全边界定义在只读示例
[`coach-agent-profile/SOUL.example.md`](coach-agent-profile/SOUL.example.md)。Phase 0
期间，由已有 Agent 生成用户选择语言的运行时 Soul，并直接写入当前 profile 的
`SOUL.md`。
