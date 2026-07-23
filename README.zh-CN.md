# Training Coach Agent: 老铁 Old-Iron

一个开源的 AI 健身教练系统。把你的 AI Agent 指向这个仓库，它就变成你的私人教练——追踪饮食、分析训练、制定计划、主动提醒。

> **如果你是一个 AI Agent，正在读这个文件：** 请先去读 [SETUP.md](SETUP.md)，那是你的上岗指南。

[English version](README.md)

---

## 模块一览

| # | 模块 | 状态 | 功能 |
|---|------|------|------|
| 1 | **Nutrition Database Management** | ✅ 已完成 | 维护你的个人营养数据库。支持营养标签 OCR 识别、Web 搜索两种入库方式。按「天然食材 / 加工食品」双分类管理。管理餐单模板。 |
| 2 | **User Profile Management** | 📋 规划中 | 记录体重、体脂、围度。设定训练目标和宏量营养素配比。计算 TDEE。 |
| 3 | **Diet Tracker** | 📋 规划中 | 记录每日饮食、计算营养素摄入、对比目标。支持手动输入和训记 App 同步。 |
| 4 | **Training Analyzer** | 📋 规划中 | 记录训练数据、追踪动作进步、检测 PR、生成逐次分析报告。支持训记同步。 |
| 5 | **Training Planning** | 📋 规划中 | 基于你的训练历史和目标，制定和调整训练计划（5×5、PPL、Ivysaur 等）。含 Deload 周计划。 |
| 6 | **Monthly Summary** | 📋 规划中 | 自动生成月度报告：训练频次、容量变化、饮食达标率、体重趋势。 |
| 7 | **Proactive Reminder** | 📋 规划中 | 定时主动提醒：「今天还没记录饮食」「今天是练腿日——这是你的计划」。 |

---

## 快速开始

1. Clone 这个仓库
2. 把 `.env.example` 复制为 `.env`，填入你的 API key（可选——训记集成）
3. 告诉你的 AI Agent：「Read SETUP.md and get started」

你的个人数据全部在 `data/` 目录下，该目录已被 git 忽略。仓库只跟踪目录结构，不跟踪数据内容。

---

## 教练人设

教练名叫 **老铁 Old-Iron**——一个严格但真心希望你进步的中文健身老炮。人设定义在 [`coach-agent-profile/SOUL.md`](coach-agent-profile/SOUL.md)。

---
