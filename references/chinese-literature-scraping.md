# 中文文学/文章原文抓取策略

## 可用来源

| 来源 | 类型 | 可靠性 | 备注 |
|------|------|--------|------|
| **可阅文学网** (kepub.net) | 中文经典文学 | ⭐⭐⭐⭐ | 完整原文，browser 抓取最可靠 |
| **豆瓣读书** | 书摘/笔记 | ⭐⭐⭐ | 通常只有片段，非全文 |
| **微信读书** (weread.qq.com) | 电子书 | ⭐⭐⭐ | 部分内容可抓取，需登录 |
| **Archive.org** | PDF | ⭐⭐⭐⭐ | 完整书籍，需 pymupdf 提取文本 |
| **天涯书库** (tianyabooks.com) | 在线阅读 | ⭐⭐ | 编码问题（gb2312），curl 乱码 |
| **九九藏书网** (99csw.com) | 在线阅读 | ⭐⭐ | Cloudflare 保护，需 browser |

## 抓取工具优先级

1. **browser_navigate + browser_snapshot** — 最可靠，处理 JS 渲染和编码
2. **curl** — 简单页面，注意编码问题
3. **scrape-stealth.py** — 反爬页面（需安装 scrapling）

## 实战经验

### 王小波杂文（2026-05-14）

成功从可阅文学网抓取《沉默的大多数》序言：
- URL: `https://www.kepub.net/book/11185`
- 目录页 → 点击章节链接 → 获取完整原文
- 约 2000 字/篇，内容完整

### PDF 提取

Archive.org 有王小波《沉默的大多数》PDF（2.2MB）：
- URL: `https://archive.org/download/HarborLibrary-Political-Science/...`
- 需要 pymupdf 提取文本：`pip install pymupdf`
- 或用 pdftotext：`sudo apt install poppler-utils`

## 注意事项

1. **版权问题** — 只用于个人学习和知识库建设，不做商业用途
2. **内容完整性** — 抓取后检查是否完整，特别注意章节边界
3. **编码问题** — 中文网站常用 gb2312，browser 自动处理，curl 需手动转码
