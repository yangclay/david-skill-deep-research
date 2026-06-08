# Karpathy System Prompt 设计调研 (2026-05-22)

> 调研任务: t_d1779cd7, 深度调研 Karpathy 关于 system prompt / agent persona 设计的原始语料
> 完整报告: `~/wiki/raw/articles/Karpathy系统提示设计-2026-05-22.md`

## 核心发现速查

### 1. Karpathy 的核心观点

- **System Prompt Learning** — LLM 应该自己学会写 system prompt，不是靠人类工程师手写规则。"LLMs are quite literally like the guy in Memento, except we haven't given them their scratchpad yet."
- **Context Engineering > Prompt Engineering** — 核心技能是"在 context window 中填入恰好正确的信息"，不是写规则
- **Collaborative, not autonomous** — agent 应该与人协作，不是自主跑 20 分钟甩 1000 行代码
- **Delegator 哲学** — "I am no longer a coder. I am a delegator."

### 2. CLAUDE.md (109k stars) — 65 行 4 原则

1. Think Before Coding — 不假设，不隐藏困惑
2. Simplicity First — 最少代码解决问题
3. Surgical Changes — 只改被要求改的
4. Goal-Driven Execution — 成功标准驱动，非步骤命令

### 3. Autoresearch 的 program.md 设计

五组件模式（"The Karpathy Loop"）：
1. Frozen harness — agent 不能改的评估基准
2. Editable artifact — agent 可改的唯一文件
3. Human spec — 自然语言目标、约束、停止条件
4. Scalar metric — 一个数字，单调衡量质量
5. Ratchet — 改进保留，退步回滚

### 4. soul.md 框架 (github.com/aaronjmars/soul.md, 510 stars)

四层结构：**identity → worldview → style → calibration**

- SOUL.md: Who I Am → Worldview → Opinions → Interests → Influences → Current Focus
- STYLE.md: Voice Principles → Vocabulary → Sentence Rules → Platform Differences → Rhetorical Moves

### 5. Viral System Prompt (God of Prompt)

XML 结构：`<role>` + `<core_behaviors priority="critical/high">` + `<leverage_patterns>` + `<meta>`

设计特点：
- 定义 operational philosophy，不是禁令清单
- 行为按 priority 分级
- leverage patterns（正向指导）> 禁令
- meta 部分定义人和 agent 的角色关系

## 对 Agent 设计的通用启示

**从"规则驱动"转向"身份驱动"：**
- SOUL.md 只负责"谁"（身份、信念、矛盾、边界）
- AGENTS.md 负责"怎么做"（路由、通道、监控规则）
- Worldview 推导行为 > 罗列规则覆盖场景
- 承认 Tensions（矛盾）> 假装不存在

## 来源

| # | 来源 | 可信度 | URL |
|---|---|---|---|
| 1 | Karpathy "System Prompt Learning" 推文 | A | https://x.com/karpathy/status/1921368644069765486 |
| 2 | Karpathy Dwarkesh 播客 | A | https://threadreaderapp.com/thread/1979644538185752935.html |
| 3 | autoresearch 仓库 (82.5k stars) | A | https://github.com/karpathy/autoresearch |
| 4 | soul.md Karpathy 示例 | A | https://github.com/aaronjmars/soul.md |
| 5 | God of Prompt viral prompt | B | https://en.rattibha.com/thread/2018482335130296381 |
| 6 | CLAUDE.md Skills Guide (100k+ stars) | A | https://github.com/forrestchang/andrej-karpathy-skills |
| 7 | System Prompt Learning 实现 | B | https://huggingface.co/posts/codelion/495839598023200 |
