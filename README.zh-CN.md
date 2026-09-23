# Training Coach Agent：老铁 Old-Iron

一个开源、模块化的 AI 健身教练系统。让 AI Agent 指向这个仓库，它就能维护
营养数据库、管理用户 profile、追踪每日饮食，并在不跨写模块数据的前提下生成
训练计划草案。

> **AI Agent 上岗：** 请先读 [SETUP.md](SETUP.md)，然后读 [AGENTS.md](AGENTS.md)。

[English version](README.md)

---

## 模块一览

| # | 模块 | 状态 | 功能 |
|---|---|---|---|
| 1 | **Nutrition Database Management** | ✅ 已完成 | 管理个人食物库和餐单模板，支持营养标签或 Web 数据入库。 |
| 2 | **User Profile Management** | ✅ 已完成 | 管理身体数据、目标、宏量素、TDEE，以及每周训练/有氧 meta 信息。 |
| 3 | **Diet Tracker** | 🧪 MVP 可用 | 记录每日饮食，确定性计算摄入和估算/手动赤字，支持可配置的多日营期。 |
| 4 | **Training Analyzer** | 📋 规划中 | 记录实际训练、检测 PR、分析训练进步。 |
| 5 | **Training Planning** | 🧪 MVP 可用 | 生成独立保存的详细训练 split 和日程草案，不修改 profile。 |
| 6 | **Monthly Summary** | 📋 规划中 | 汇总训练、饮食、身体和目标趋势，生成月度报告。 |
| 7 | **Proactive Reminder** | 📋 规划中 | 提供遵循时区、克制且不打扰的主动提醒。 |

MVP 明确区分**计划中的训练**和**用户确认实际发生的训练**。每日追踪都必须
询问用户今天训练还是休息，不能从日历或计划中推断。

---

## 快速开始

1. Clone 这个仓库。
2. 把 `.env.example` 复制成 `.env`，实际 key 由你自己填写。
3. 告诉 AI Agent：`Read SETUP.md and get started`。
4. 需要训练计划时，加载 `skills/training-planning/SKILL.md`。
5. 需要记录饮食或运行营期时，加载 `skills/diet-tracker/SKILL.md`。

用户数据位于 `data/`，已被 Git 忽略；仓库只保留目录结构 marker。每个模块只
写自己的 data sandbox，详见 [AGENTS.md](AGENTS.md)。

---

## 教练人设

教练名叫 **老铁 Old-Iron**——一个严格但真心希望你进步的中文健身老炮。人设和
安全边界定义在 [`coach-agent-profile/SOUL.md`](coach-agent-profile/SOUL.md)。

---
