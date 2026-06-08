#!/usr/bin/env python3
"""tavily_search_v2.py — 带可信度评分和交叉验证的搜索脚本"""
import argparse
import json
import subprocess
import sys
from datetime import datetime
from typing import List, Dict, Any

# 可信度评分权重
SOURCE_WEIGHTS = {
    "docs.openclaw.ai": 1.0,
    "github.com": 0.9,
    "stackoverflow.com": 0.8,
    "medium.com": 0.7,
    "dev.to": 0.7,
    "zenn.dev": 0.7,
    "juejin.cn": 0.7,
    "cnblogs.com": 0.6,
    "blog": 0.6,
    "reddit.com": 0.5,
    "twitter.com": 0.5,
    "x.com": 0.5,
}

def get_source_score(url: str) -> float:
    """根据来源类型返回可信度分数"""
    url_lower = url.lower()
    for key, weight in SOURCE_WEIGHTS.items():
        if key in url_lower:
            return weight
    return 0.5  # 默认分数

def parse_date_freshness(date_str: str) -> float:
    """根据日期判断新鲜度分数"""
    if not date_str:
        return 0.5
    try:
        # Tavily 返回的日期格式
        date = datetime.strptime(date_str[:10], "%Y-%m-%d")
        days_old = (datetime.now() - date).days
        if days_old < 30:
            return 1.0
        elif days_old < 90:
            return 0.8
        elif days_old < 180:
            return 0.6
        elif days_old < 365:
            return 0.4
        else:
            return 0.2
    except:
        return 0.5

def calculate_credibility_score(result: Dict[str, Any]) -> float:
    """综合计算可信度分数"""
    url = result.get("url", "")
    score = get_source_score(url)
    
    # 新鲜度权重
    freshness = parse_date_freshness(result.get("published_date", ""))
    score = score * 0.7 + freshness * 0.3
    
    return round(score, 2)

def enrich_results(results: List[Dict]) -> List[Dict]:
    """为结果添加可信度分数和分类"""
    enriched = []
    for r in results:
        r["credibility_score"] = calculate_credibility_score(r)
        r["source_type"] = classify_source(r.get("url", ""))
        enriched.append(r)
    # 按可信度排序
    return sorted(enriched, key=lambda x: x["credibility_score"], reverse=True)

def classify_source(url: str) -> str:
    """分类来源类型"""
    url_lower = url.lower()
    if "docs" in url_lower or "documentation" in url_lower:
        return "official_docs"
    elif "github.com" in url_lower:
        return "code"
    elif "stackoverflow.com" in url_lower:
        return "qna"
    elif "medium.com" in url_lower or "blog" in url_lower:
        return "blog"
    elif "arxiv.org" in url_lower:
        return "academic"
    elif "reddit.com" in url_lower or "twitter.com" in url_lower or "x.com" in url_lower:
        return "social"
    else:
        return "other"

def search(query: str, max_results: int = 5, include_answer: bool = True) -> Dict[str, Any]:
    """执行搜索并返回带可信度的结果"""
    cmd = [
        # External dependency: openclaw-tavily-search was at /mnt/d/openclaw-wsl/workspace/skills/openclaw-tavily-search/scripts/tavily_search.py
        # Now uses built-in Tavily API directly
        "python3", "-c",
        "import urllib.request, json, os, sys; "
        "key = os.environ.get('TAVILY_API_KEY', ''); "
        "payload = json.dumps({'api_key': key, 'query': sys.argv[1], 'max_results': int(sys.argv[2]), 'search_depth': 'advanced', 'include_answer': True}).encode(); "
        "req = urllib.request.Request('https://api.tavily.com/search', data=payload, headers={'Content-Type': 'application/json'}, method='POST'); "
        "print(urllib.request.urlopen(req, timeout=15).read().decode())",
        query,
        str(max_results)
    ]
    if include_answer:
        cmd.append("--include-answer")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    try:
        data = json.loads(result.stdout)
        if "results" in data:
            data["results"] = enrich_results(data["results"])
        return data
    except:
        return {"error": "Failed to parse", "raw": result.stdout}

def verify_citation(result: Dict, max_chars: int = 2000) -> Dict[str, Any]:
    """验证引用：抓取原文对比摘要"""
    url = result.get("url")
    if not url:
        return {"verified": False, "reason": "no_url"}
    
    # 用 web-fetch.py 抓取
    # Uses built-in web_fetch or scrape-stealth.py from skill scripts
    cmd = ["python3", "/home/clay/.hermes/skills/deep-research/scripts/scrape-stealth.py", url, "--max-chars", str(max_chars)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    
    if proc.returncode != 0:
        return {"verified": False, "reason": "fetch_failed", "error": proc.stderr}
    
    content = proc.stdout
    title = result.get("title", "")
    snippet = result.get("content", "")[:200]  # 搜索摘要
    
    # 简单验证：标题是否在内容中，摘要关键词是否在内容中
    title_match = title.lower() in content.lower()
    
    # 检查摘要关键词
    snippet_words = set(snippet.lower().split()) - {"the", "a", "an", "and", "or", "but", "is", "are", "was", "were"}
    snippet_match = len(snippet_words & set(content.lower().split())) >= min(3, len(snippet_words))
    
    return {
        "verified": title_match or snippet_match,
        "title_match": title_match,
        "snippet_match": snippet_match,
        "content_length": len(content)
    }

def cross_verify(query: str, results: List[Dict], top_k: int = 3) -> Dict[str, Any]:
    """多角度交叉验证：用不同 query 验证同一问题"""
    # 构造不同角度的 query
    variations = [
        query,
        f"{query} official documentation",
        f"{query} tutorial guide"
    ]
    
    all_results = []
    for q in variations[:2]:  # 限制轮次
        try:
            r = search(q, max_results=3, include_answer=False)
            all_results.extend(r.get("results", []))
        except:
            pass
    
    # 提取所有唯一 URL
    unique_urls = set(r.get("url") for r in results)
    verification_urls = set(r.get("url") for r in all_results)
    
    # 交集比例
    overlap = len(unique_urls & verification_urls) / max(len(unique_urls), 1)
    
    return {
        "cross_verified": overlap > 0.3,
        "overlap_ratio": round(overlap, 2),
        "unique_sources": len(unique_urls),
        "additional_sources": len(verification_urls - unique_urls)
    }

def main():
    parser = argparse.ArgumentParser(description="Tavily Search V2 with credibility scoring")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--max-results", type=int, default=5, help="Max results")
    parser.add_argument("--include-answer", action="store_true", help="Include AI answer")
    parser.add_argument("--verify", action="store_true", help="Verify citations")
    parser.add_argument("--cross-verify", action="store_true", help="Cross-verify with multiple queries")
    parser.add_argument("--format", default="json", choices=["json", "md"], help="Output format")
    
    args = parser.parse_args()
    
    # 执行搜索
    data = search(args.query, args.max_results, args.include_answer)
    
    # 交叉验证
    if args.cross_verify and "results" in data:
        cv = cross_verify(args.query, data["results"])
        data["cross_verification"] = cv
    
    # 引用验证
    if args.verify and "results" in data:
        for r in data["results"][:3]:  # 只验证前3个
            r["citation_verification"] = verify_citation(r)
    
    # 输出
    if args.format == "md":
        print(f"# 搜索结果: {args.query}\n")
        for i, r in enumerate(data.get("results", []), 1):
            score = r.get("credibility_score", 0)
            score_emoji = "🟢" if score > 0.7 else "🟡" if score > 0.5 else "🔴"
            print(f"## {i}. {r.get('title', 'N/A')} {score_emoji} ({score})")
            print(f"**来源**: {r.get('url', 'N/A')} [{r.get('source_type', 'unknown')}]")
            print(f"**摘要**: {r.get('content', 'N/A')[:200]}...")
            if "citation_verification" in r:
                v = r["citation_verification"]
                v_emoji = "✅" if v.get("verified") else "❌"
                print(f"**引用验证**: {v_emoji}")
            print()
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
