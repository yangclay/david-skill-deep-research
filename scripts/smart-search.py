#!/usr/bin/env python3
"""
smart-search.py — 带缓存的逐层升级搜索

核心机制：
1. SQLite 缓存（查询 → 结果，7天 TTL）
2. 逐层升级（DuckDuckGo → Searlo → SerpAPI → Tavily）
3. 覆盖率 ≥85% 提前停止
4. 子问题共享结果池

用法：
  python3 smart-search.py "查询词"                         # 单查询
  python3 smart-search.py --queries "问题1" "问题2" "问题3" # 多子问题共享结果池
  python3 smart-search.py --cache-stats                    # 查看缓存统计
  python3 smart-search.py --cache-clear                    # 清理过期缓存
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ─── 配置 ───────────────────────────────────────────────
COVERAGE_THRESHOLD = 0.85  # 85% 覆盖率即停止

def _set_coverage(val):
    global COVERAGE_THRESHOLD
    COVERAGE_THRESHOLD = val
CACHE_TTL_DAYS = 7         # 缓存有效期
MAX_RESULTS_PER_LAYER = 10 # 每层最多返回条数
REQUEST_TIMEOUT = 15       # API 请求超时秒数

# 缓存数据库路径
CACHE_DIR = Path.home() / ".hermes" / "cache" / "search-cache"
CACHE_DB = CACHE_DIR / "search-cache.db"

# API Keys（从环境变量或 ~/.hermes/.env 读取）
def _load_env_key(name: str) -> str:
    val = os.environ.get(name, "")
    if val:
        return val.strip()
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        for line in env_path.read_text(errors="ignore").splitlines():
            if line.strip().startswith(name + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""

SEARLO_API_KEY = _load_env_key("SEARLO_API_KEY")
SERPAPI_API_KEY = _load_env_key("SERPAPI_API_KEY")
TAVILY_API_KEY = _load_env_key("TAVILY_API_KEY")
TINYFISH_API_KEY = _load_env_key("TINYFISH_API_KEY")

# ─── 缓存层 ─────────────────────────────────────────────
def init_cache():
    """初始化缓存数据库"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CACHE_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS search_cache (
            query_hash TEXT PRIMARY KEY,
            query TEXT NOT NULL,
            layer TEXT NOT NULL,
            results TEXT NOT NULL,
            created_at REAL NOT NULL,
            expires_at REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_expires ON search_cache(expires_at)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_query ON search_cache(query)
    """)
    conn.commit()
    return conn

def cache_get(conn, query: str) -> Optional[List[Dict]]:
    """从缓存获取结果"""
    query_hash = hashlib.md5(query.lower().strip().encode()).hexdigest()
    now = time.time()
    row = conn.execute(
        "SELECT results, layer FROM search_cache WHERE query_hash = ? AND expires_at > ?",
        (query_hash, now)
    ).fetchone()
    if row:
        results = json.loads(row[0])
        layer = row[1]
        print(f"  [缓存命中] {query[:50]}... (来自 {layer}, {len(results)} 条)", file=sys.stderr)
        return results
    return None

def cache_put(conn, query: str, layer: str, results: List[Dict]):
    """写入缓存"""
    query_hash = hashlib.md5(query.lower().strip().encode()).hexdigest()
    now = time.time()
    expires = now + CACHE_TTL_DAYS * 86400
    conn.execute(
        "INSERT OR REPLACE INTO search_cache (query_hash, query, layer, results, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
        (query_hash, query, layer, json.dumps(results, ensure_ascii=False), now, expires)
    )
    conn.commit()

def cache_stats(conn):
    """打印缓存统计"""
    total = conn.execute("SELECT COUNT(*) FROM search_cache").fetchone()[0]
    active = conn.execute("SELECT COUNT(*) FROM search_cache WHERE expires_at > ?", (time.time(),)).fetchone()[0]
    expired = total - active
    by_layer = conn.execute(
        "SELECT layer, COUNT(*) FROM search_cache WHERE expires_at > ? GROUP BY layer",
        (time.time(),)
    ).fetchall()
    print(f"缓存统计: 总计 {total} 条, 有效 {active} 条, 过期 {expired} 条")
    for layer, count in by_layer:
        print(f"  {layer}: {count} 条")

def cache_clear(conn):
    """清理过期缓存"""
    deleted = conn.execute("DELETE FROM search_cache WHERE expires_at < ?", (time.time(),)).rowcount
    conn.commit()
    print(f"清理了 {deleted} 条过期缓存")

# ─── 覆盖率评估 ──────────────────────────────────────────
def calc_coverage(results: List[Dict]) -> float:
    """计算搜索结果覆盖率（基于去重后的独立域名数）"""
    if not results:
        return 0.0
    domains = set()
    for r in results:
        url = r.get("url", r.get("link", ""))
        if url:
            try:
                domain = urllib.parse.urlparse(url).netloc.lower()
                domains.add(domain)
            except:
                pass
    # 基于独立域名数估算：5个不同域名 = 良好覆盖，10+ = 充分
    min_domains = 5
    max_domains = 12
    coverage = min(1.0, len(domains) / max_domains)
    return coverage

def dedup_results(results: List[Dict]) -> List[Dict]:
    """去重：URL exact + Domain 去重"""
    seen_urls = set()
    seen_domains = set()
    deduped = []
    for r in results:
        url = r.get("url", r.get("link", ""))
        if not url or url in seen_urls:
            continue
        try:
            domain = urllib.parse.urlparse(url).netloc.lower()
        except:
            domain = ""
        if domain and domain in seen_domains:
            # 同域名保留最相关的一条（靠前的）
            continue
        seen_urls.add(url)
        if domain:
            seen_domains.add(domain)
        deduped.append(r)
    return deduped

# ─── 搜索层 ─────────────────────────────────────────────

def layer_tinyfish(query: str) -> List[Dict]:
    """Layer 0: TinyFish Search（免费，真浏览器渲染，结构化 JSON）"""
    if not TINYFISH_API_KEY:
        print("  [TinyFish] 跳过（无 API key）", file=sys.stderr)
        return []
    results = []
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://api.search.tinyfish.ai?query={encoded}&limit={MAX_RESULTS_PER_LAYER}"
        req = urllib.request.Request(url, headers={
            "X-API-Key": TINYFISH_API_KEY,
        })
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
            if "error" in data:
                print(f"  [TinyFish] API 错误: {data['error']}", file=sys.stderr)
                return []
            for item in data.get("results", [])[:MAX_RESULTS_PER_LAYER]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "tinyfish"
                })
    except Exception as e:
        print(f"  [TinyFish] 错误: {e}", file=sys.stderr)
    return results

def layer_duckduckgo(query: str) -> List[Dict]:
    """Layer 1: DuckDuckGo（免费，无限）"""
    results = []
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; smart-search/1.0)"
        })
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
            # Abstract (直接答案)
            if data.get("Abstract"):
                results.append({
                    "title": data.get("Heading", ""),
                    "url": data.get("AbstractURL", ""),
                    "snippet": data.get("Abstract", ""),
                    "source": "duckduckgo"
                })
            # Related topics
            for topic in data.get("RelatedTopics", [])[:MAX_RESULTS_PER_LAYER]:
                if "FirstURL" in topic:
                    results.append({
                        "title": topic.get("Text", "")[:100],
                        "url": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", ""),
                        "source": "duckduckgo"
                    })
        # 如果 DDG Instant Answer 结果太少，用 HTML 搜索补充
        if len(results) < 3:
            results.extend(_ddg_html_search(query))
    except Exception as e:
        print(f"  [DuckDuckGo] 错误: {e}", file=sys.stderr)
    return results[:MAX_RESULTS_PER_LAYER]

def _ddg_html_search(query: str) -> List[Dict]:
    """DuckDuckGo HTML 搜索（补充 Instant Answer 不足的情况）"""
    results = []
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        })
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            # 简单解析结果
            for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL):
                raw_url = m.group(1)
                title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
                # DDG HTML 返回的 URL 是编码过的，需要解码
                if 'uddg=' in raw_url:
                    m2 = re.search(r'uddg=([^&]+)', raw_url)
                    if m2:
                        raw_url = urllib.parse.unquote(m2.group(1))
                if raw_url and title and not raw_url.startswith('https://html.duckduckgo.com'):
                    results.append({
                        "title": title,
                        "url": raw_url,
                        "snippet": "",
                        "source": "duckduckgo"
                    })
            # 提取摘要
            snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
            for i, snippet in enumerate(snippets):
                if i < len(results):
                    results[i]["snippet"] = re.sub(r'<[^>]+>', '', snippet).strip()
    except Exception as e:
        print(f"  [DDG HTML] 错误: {e}", file=sys.stderr)
    return results[:MAX_RESULTS_PER_LAYER]

def layer_searlo(query: str) -> List[Dict]:
    """Layer 2: Searlo（$0.30/千次，Google SERP）"""
    if not SEARLO_API_KEY:
        print("  [Searlo] 跳过（无 API key）", file=sys.stderr)
        return []
    results = []
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://api.searlo.tech/api/v1/search/web?q={encoded}&limit={MAX_RESULTS_PER_LAYER}&gl=us"
        req = urllib.request.Request(url, headers={
            "x-api-key": SEARLO_API_KEY,
            "User-Agent": "Mozilla/5.0 (compatible; smart-search/1.0)"
        })
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
            for item in data.get("organic", [])[:MAX_RESULTS_PER_LAYER]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "searlo"
                })
    except Exception as e:
        print(f"  [Searlo] 错误: {e}", file=sys.stderr)
    return results

def layer_serpapi_baidu(query: str) -> List[Dict]:
    """Layer 3: SerpAPI 百度引擎（中文内容专项）"""
    if not SERPAPI_API_KEY:
        print("  [SerpAPI] 跳过（无 API key）", file=sys.stderr)
        return []
    results = []
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://serpapi.com/search?q={encoded}&api_key={SERPAPI_API_KEY}&engine=baidu&num={MAX_RESULTS_PER_LAYER}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
            for item in data.get("organic_results", [])[:MAX_RESULTS_PER_LAYER]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "serpapi_baidu"
                })
    except Exception as e:
        print(f"  [SerpAPI] 错误: {e}", file=sys.stderr)
    return results

def layer_tavily_search(query: str) -> List[Dict]:
    """Layer 4: Tavily search（~$0.01/次，高质量）"""
    if not TAVILY_API_KEY:
        print("  [Tavily] 跳过（无 API key）", file=sys.stderr)
        return []
    results = []
    try:
        payload = json.dumps({
            "api_key": TAVILY_API_KEY,
            "query": query,
            "max_results": MAX_RESULTS_PER_LAYER,
            "search_depth": "basic",
            "include_answer": True,
            "include_images": False,
            "include_raw_content": False,
        }).encode()
        req = urllib.request.Request(
            "https://api.tavily.com/search",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
            # AI 摘要
            if data.get("answer"):
                results.append({
                    "title": "[Tavily AI 摘要]",
                    "url": "",
                    "snippet": data["answer"],
                    "source": "tavily_answer"
                })
            for item in data.get("results", [])[:MAX_RESULTS_PER_LAYER]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                    "source": "tavily"
                })
    except Exception as e:
        print(f"  [Tavily] 错误: {e}", file=sys.stderr)
    return results

# ─── 逐层升级搜索 ─────────────────────────────────────────

LAYERS = [
    ("tinyfish",       layer_tinyfish,       "免费"),
    ("duckduckgo",     layer_duckduckgo,     "免费"),
    ("searlo",         layer_searlo,         "$0.30/千次"),
    ("serpapi_baidu",  layer_serpapi_baidu,  "100次/月"),
    ("tavily",         layer_tavily_search,  "$0.01/次"),
]

def search_single(conn, query: str) -> Tuple[List[Dict], str]:
    """单查询逐层升级搜索"""
    # 先查缓存
    cached = cache_get(conn, query)
    if cached:
        return cached, "cache"

    all_results = []
    final_layer = "none"

    for layer_name, layer_func, layer_cost in LAYERS:
        print(f"  [{layer_name}] 搜索中...", file=sys.stderr)
        new_results = layer_func(query)

        if new_results:
            all_results.extend(new_results)
            all_results = dedup_results(all_results)
            coverage = calc_coverage(all_results)
            final_layer = layer_name
            print(f"  [{layer_name}] +{len(new_results)} 条, 去重后 {len(all_results)} 条, 覆盖率 {coverage:.0%}", file=sys.stderr)

            # 覆盖率达标，提前停止
            if coverage >= COVERAGE_THRESHOLD:
                print(f"  ✅ 覆盖率 {coverage:.0%} ≥ {COVERAGE_THRESHOLD:.0%}, 停止搜索", file=sys.stderr)
                break
        else:
            print(f"  [{layer_name}] 无结果", file=sys.stderr)

    # 写缓存
    if all_results:
        cache_put(conn, query, final_layer, all_results)

    return all_results, final_layer

def search_multi(conn, queries: List[str]) -> List[Dict]:
    """多子问题共享结果池"""
    print(f"多查询搜索：{len(queries)} 个子问题", file=sys.stderr)

    all_results = []
    domain_pool = set()

    for i, query in enumerate(queries):
        print(f"\n子问题 {i+1}/{len(queries)}: {query[:60]}...", file=sys.stderr)
        results, layer = search_single(conn, query)

        # 共享结果池：新结果加入，但不重复搜已覆盖的域名
        new_count = 0
        for r in results:
            url = r.get("url", r.get("link", ""))
            if url:
                try:
                    domain = urllib.parse.urlparse(url).netloc.lower()
                    if domain not in domain_pool:
                        domain_pool.add(domain)
                        all_results.append(r)
                        new_count += 1
                except:
                    pass

        print(f"  新增 {new_count} 条（共 {len(all_results)} 条, {len(domain_pool)} 个域名）", file=sys.stderr)

        # 共享结果池已充分覆盖，后续子问题跳过
        shared_coverage = calc_coverage(all_results)
        if shared_coverage >= COVERAGE_THRESHOLD and i < len(queries) - 1:
            remaining = len(queries) - i - 1
            print(f"  ✅ 共享池覆盖率 {shared_coverage:.0%} ≥ {COVERAGE_THRESHOLD:.0%}, 跳过剩余 {remaining} 个子问题", file=sys.stderr)
            break

    return all_results

# ─── 输出 ───────────────────────────────────────────────

def format_results(results: List[Dict], fmt: str = "json") -> str:
    """格式化输出"""
    if fmt == "json":
        return json.dumps(results, indent=2, ensure_ascii=False)
    elif fmt == "md":
        lines = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "无标题")
            url = r.get("url", r.get("link", ""))
            snippet = r.get("snippet", "")
            source = r.get("source", "unknown")
            lines.append(f"### {i}. {title}")
            if url:
                lines.append(f"来源: {url}")
            lines.append(f"搜索源: {source}")
            if snippet:
                lines.append(f"> {snippet[:300]}")
            lines.append("")
        return "\n".join(lines)
    else:
        return json.dumps(results, indent=2, ensure_ascii=False)

# ─── Main ───────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="带缓存的逐层升级搜索")
    parser.add_argument("query", nargs="?", help="搜索查询词")
    parser.add_argument("--queries", nargs="+", help="多子问题搜索（共享结果池）")
    parser.add_argument("--format", choices=["json", "md"], default="json", help="输出格式")
    parser.add_argument("--cache-stats", action="store_true", help="显示缓存统计")
    parser.add_argument("--cache-clear", action="store_true", help="清理过期缓存")
    parser.add_argument("--coverage", type=float, default=COVERAGE_THRESHOLD, help="覆盖率阈值（默认 0.85）")
    args = parser.parse_args()

    if args.coverage:
        _set_coverage(args.coverage)

    conn = init_cache()

    if args.cache_stats:
        cache_stats(conn)
        return

    if args.cache_clear:
        cache_clear(conn)
        return

    if args.queries:
        results = search_multi(conn, args.queries)
    elif args.query:
        results, layer = search_single(conn, args.query)
    else:
        parser.error("请提供搜索查询词")

    print(format_results(results, args.format))

if __name__ == "__main__":
    main()
