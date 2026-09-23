# Training Coach Agent：老铁 Old-Iron

一个开源、模块化的 AI 健身教练系统。让 AI Agent 指向本仓库后，它可以维护营养
数据库、管理 profile、追踪每日饮食、记录并分析已确认的实际训练，以及管理训练
计划草案，同时严格遵守各模块的数据沙箱。

> **开发中：** 模块 3–5 已可用于日常流程，但整个项目仍未达到生产环境标准，
> 也不能替代医疗服务。

> **AI Agent 上岗：** 先读 [SETUP.md](SETUP.md)，再读 [AGENTS.md](AGENTS.md)。

[English version](README.md)

## 模块一览

| # | 模块 | 状态 | 功能 |
|---|---|---|---|
| 1 | **Nutrition Database Management** | ✅ 已完成 | 管理个人食物库和餐单模板。 |
| 2 | **User Profile Management** | ✅ 已完成 | 管理身体数据、目标、宏量素、TDEE 和每周训练/有氧元数据。 |
| 3 | **Diet Tracker** | ✅ 日常可用 | 对餐食做增删改查，汇报摄入与目标宏量素，并标注估算/手动能量赤字。 |
| 4 | **Training Analyzer** | ✅ 日常可用 | 保存已确认的实际训练，计算训练量、Epley 1RM、RPE、频率和 PR 标记。 |
| 5 | **Training Planning** | ✅ 日常可用 | 生成、校验和确认训练计划草案，并另存减量计划，不修改 profile。 |
| 6 | **Monthly Summary** | 📋 规划中 | 汇总训练、饮食、身体与目标趋势。 |
| 7 | **Proactive Reminder** | 📋 规划中 | 提供遵循时区、克制且不打扰的提醒。 |

系统严格区分训练计划和实际训练。每次日常打卡都要明确询问今天是 `training`
还是 `rest`，不能由日历或计划替用户回答。

## 使用独立 Hermes profile

```bash
hermes profile create trainingcoach --description "Private modular fitness coach"
hermes profile use trainingcoach
hermes profile show trainingcoach
hermes config edit
hermes --in /absolute/path/to/training-coach-agent
```

执行 `hermes config edit` 时，把
[`coach-agent-profile/config.reference.yaml`](coach-agent-profile/config.reference.yaml)
中的配置合并进去，并替换绝对路径占位符。进入会话后告诉 Agent：`Read SETUP.md
and get started`。需要退出该 profile 时运行 `hermes profile use default`。

运行时用户数据位于 `data/` 并由 Git 忽略。凭据只能放在当前 Hermes profile 或
环境变量中，绝不能写入仓库。

## 教练人设

教练名叫 **老铁 Old-Iron**——严格但真心希望你进步的中文健身老炮。人设和安全
边界定义在 [`coach-agent-profile/SOUL.md`](coach-agent-profile/SOUL.md)。
