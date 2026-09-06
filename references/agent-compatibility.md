# Agent 兼容矩阵

Orion Research 遵循 [Anthropic Agent Skills 标准](https://agentskills.io)（SKILL.md 位于仓库根目录 + references/ 子目录）。**SKILL.md 格式被 27+ 主流 Agent 支持**（Claude Code、OpenAI Codex、OpenClaw、Cursor、Windsurf、Gemini CLI、Goose、Amp 等），同一份文件无需修改即可跨 Agent 使用。

方法论与工具调用分离——"做什么"通用，"用什么工具"按 Agent 环境映射。

## 核心工具映射

| 本 skill 需要的能力 | Hermes | Claude Code | OpenClaw | Codex | 通用替代方案 |
|---|---|---|---|---|---|
| 代码执行（编排搜索管道） | `execute_code` | bash / code_execution | bash | bash / code_execution | Python 脚本 + `subprocess` |
| 搜索 | 内置 `web_search` | WebSearch / WebFetch | HTTP 工具 | 内置搜索工具 | Tavily / SerpAPI / Brave API |
| 抓取单页 | `scripts/web-fetch.sh` | WebFetch / curl | HTTP 工具 | WebFetch / curl | `curl` / `requests` |
| 反爬页面 | `scripts/scrape-stealth.py` | Playwright MCP | Playwright | 浏览器工具 | Playwright / Scrapling |
| 整站抓取 | `scripts/crawl_site.py` | crawl4ai | crawl4ai | crawl4ai | `crawl4ai` |
| 语义重排 | Jina Rerank API | Jina Rerank API | Jina Rerank API | Jina Rerank API | Jina / Cohere Rerank |
| 记忆/经验记录 | Hermes 记忆系统 | CLAUDE.md 更新 | 记忆文件 | 记忆文件 | 追加到记忆文件 |
| API key 管理 | `.env`（按环境读取） | 环境变量 | 环境变量 | 环境变量 | 环境变量（不要硬编码） |

## 安装方式

### 通用：skills.sh CLI（一行装到所有已装 Agent）

```bash
npx skills add yangclay/orion-research
```

自动检测本机已安装的 Agent（Claude Code / Codex / Cursor / OpenClaw 等），把 skill 分发到各 Agent 的 skills 目录。也可指定单个 skill：

```bash
npx skills add yangclay/orion-research --skill orion-research
```

### Anthropic Claude / Claude Code

```bash
mkdir -p ~/.claude/skills/orion-research
cp -r SKILL.md references/ scripts/ gotchas/ evals/ ~/.claude/skills/orion-research/
```

### OpenAI Codex

```bash
mkdir -p ~/.codex/skills/orion-research
cp -r SKILL.md references/ scripts/ gotchas/ evals/ ~/.codex/skills/orion-research/
```

项目级：放入 `.codex/skills/` 或 `.agents/skills/`。Codex 自动读取 SKILL.md frontmatter 的 name/description 作为触发信号。

### OpenClaw

```bash
# 从 GitHub 仓库直接安装（SKILL.md 在仓库根目录，符合 OpenClaw 要求）
openclaw skills install git:yangclay/orion-research@main

# 装到所有本地 agent
openclaw skills install git:yangclay/orion-research@main --global
```

### Hermes Agent

```bash
git clone https://github.com/yangclay/orion-research.git \
  ~/.hermes/profiles/<profile>/skills/orion-research
```

### OpenCode / Cursor / Windsurf 等

将 `SKILL.md` + `references/` 放入项目的 skill 指令目录（OpenCode: `.opencode/skills/`，Cursor: `.cursor/rules/`，Windsurf: `.windsurf/skills/`），或直接用 `npx skills add`。

### WorkBuddy（特殊说明）

WorkBuddy 的插件机制与标准 SKILL.md 生态不同——需要安装到插件市场目录并通过 `settings.json` 启用，不能直接复制到 skills 目录。适配方式：

1. 将本仓库放入插件市场目录：`~/.workbuddy/plugins/marketplaces/cb_teams_marketplace/plugins/orion-research/`
2. 在 `~/.workbuddy/settings.json` 中启用该插件
3. 或通过 WorkBuddy 的插件市场 UI 手动导入 GitHub 仓库

> 提示：WorkBuddy 生态优先支持其官方插件市场格式；如需完整 SaC 编排能力，建议在 Hermes / Claude Code / Codex 中使用本 skill。

## 各环境注意事项

- **Hermes**：完整支持，含 SaC 模板、限流控制、中文生态专项
- **Claude Code**：代码执行用 bash 替代；记忆记录用更新 CLAUDE.md 替代；其余方法论通用
- **OpenClaw**：直接支持 Git 安装；SKILL.md 根目录格式完全兼容
- **Codex**：直接支持 SKILL.md 标准；建议先跑 ReAct 模式（轻量），复杂调研再启用 CodeAct
- **通用**：API key 一律从环境变量读取，禁止硬编码进任何文件

## 降级策略

如果当前环境缺少某些工具（如无语义重排 API）：

1. ReAct 模式仍然可用（只需搜索 + 判断）
2. CodeAct 模式可降级为"搜索 → 规则 filter → dedupe → 报告"（跳过重排打分）
3. Gotcha 检测不依赖任何工具，永远可用——这是本 skill 的核心价值
