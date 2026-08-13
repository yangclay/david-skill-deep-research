id: G-014
title: Citation 存在但 claim 不被支持
trigger:
  - 报告中有 citation
  - claim 与 citation 实际内容不一致
  - 未验证 citation 原文
failure:
  - Agent 将"有 citation"等同于"claim 被支持"
  - 引用了文章但曲解了意思
  - 数字/事实与原文不符
  - 输出虚假的支撑关系
root_cause:
  - 只检查 citation existence，不检查 entailment
  - 没有抓取 citation 原文验证
  - 过度信任模型的理解能力
symptom:
  - 有 citation 但 claim 与原文不符
  - 引用看似合理但实际不支持结论
  - citation 是相关但不支撑 claim
detection:
  - 抓取 citation URL 验证原文
  - 检查 claim 是否被 citation 实际支持
  - 对比数字/事实与原文
correct_action:
  - 关键 claim 必须验证 citation 原文
  - 不支持的 citation 标注为"弱支撑"
  - 无法验证的 citation 标注为"未验证"
bad_example:
  "Claim: 收入增长 37%，Citation: 某文章说收入增长"
  → 实际：原文说的是 22%，不是 37%
good_example:
  "Claim: 收入增长 37%（来源：2026-Q1 财报，已验证原文）"
eval: 5
note: 这是 citation integrity eval 的核心测试点
created: 2026-08-12
status: active
