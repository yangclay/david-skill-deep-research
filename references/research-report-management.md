# 调研报告文件管理规范

## 统一存放位置

所有调研报告统一存放在 Obsidian vault 的 `sources/调研/` 目录：

```
/mnt/d/OneDrive/obsidian-david-knowledge/sources/调研/
```

**不要散落在以下位置：**
- `~/.hermes/research-output/` — 旧结构，已废弃
- `~/.hermes/profiles/researcher/workspace/research-output/` — 旧结构，已废弃
- `~/.hermes/knowledge/research/` — 旧结构，已废弃

## 命名规范

格式：`主题关键词-YYYY-MM-DD.md`（日期放末尾）

示例：
- `AI-Agent框架对比-2026-05-14.md`
- `Claude-Code-Skill-Creator-2026-05-14.md`
- `LLM-Wiki知识库最佳实践-2026-05-05.md`
- `知识库分类方法-2026-05-04.md`

**禁止：**
- `调研报告.md`（默认名称，无主题）
- `2026-05-14-主题.md`（日期在前）

## 迁移旧文件

如果发现散落在旧位置的调研报告，统一迁移到 `sources/调研/` 并重命名：

```bash
# 检查旧位置
ls ~/.hermes/research-output/
ls ~/.hermes/profiles/researcher/workspace/research-output/
ls ~/.hermes/knowledge/research/

# 迁移示例
mv ~/.hermes/research-output/旧文件.md /mnt/d/OneDrive/obsidian-david-knowledge/sources/调研/主题-YYYY-MM-DD.md
```
