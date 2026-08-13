#!/usr/bin/env python3
"""crawl_site.py — crawl4ai wrapper for orion-research
用法：
  python3 crawl_site.py <url> [options]

选项：
  --mode single|multi|sitemap   抓取模式（默认 single）
  --max-pages N                 multi 模式最多抓几页（默认 10）
  --max-chars N                 每页截断字符数（默认 12000）
  --same-domain                 只爬同域链接（默认开启）
  --js                          启用 JS 渲染（默认关闭，用简单 HTTP）
  --output <file>               输出到文件而非 stdout
  --json                        JSON 格式输出

模式说明：
  single    — 只抓目标 URL，返回 markdown
  multi     — 抓目标 URL + 页面内同域链接，最多 N 页
  sitemap   — 从 /sitemap.xml 发现 URL，抓取全部

依赖：crawl4ai（安装在 ~/.hermes/tools/crawl4ai-venv/）
"""

import sys
import os
import json
import asyncio
import argparse
import re
from urllib.parse import urlparse, urljoin

# Suppress crawl4ai's verbose stdout during imports
_devnull = open(os.devnull, 'w')
_old_stdout = sys.stdout
sys.stdout = _devnull
try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
finally:
    sys.stdout = _old_stdout
    _devnull.close()


def _run_quiet(coro):
    """Run async coroutine with crawl4ai stdout suppressed.
    crawl4ai uses rich console which writes directly to sys.stdout."""
    import subprocess
    # We'll use a wrapper approach: run the crawl in a subprocess
    # Actually, let's just redirect stdout at the fd level
    pass


async def crawl_single(url: str, js: bool = False, max_chars: int = 12000) -> dict:
    """抓取单个 URL，返回 {url, markdown, links, char_count}"""
    browser_config = BrowserConfig(headless=True)
    config = CrawlerRunConfig(
        page_timeout=30000,
        wait_until="domcontentloaded" if not js else "networkidle",
    )

    # Redirect stdout at file descriptor level to suppress crawl4ai's rich output
    saved_stdout_fd = os.dup(1)
    with open(os.devnull, 'w') as devnull:
        os.dup2(devnull.fileno(), 1)
        try:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url, config=config)
        finally:
            os.dup2(saved_stdout_fd, 1)
            os.close(saved_stdout_fd)

    md = result.markdown or ""
    if len(md) > max_chars:
        md = md[:max_chars] + f"\n\n[截断：原长 {len(result.markdown)} 字符]"

    links = []
    if result.links:
        for link in (result.links.get("internal", []) or []):
            href = link.get("href", "")
            if href and href.startswith(("http://", "https://")):
                links.append(href)

    return {
        "url": url,
        "markdown": md,
        "links": links[:50],
        "char_count": len(md),
        "success": result.success if hasattr(result, 'success') else True,
    }


async def crawl_multi(start_url: str, max_pages: int = 10, js: bool = False,
                      max_chars: int = 12000, same_domain: bool = True) -> list:
    """从 start_url 开始，跟踪同域链接，最多抓 max_pages 页"""
    parsed = urlparse(start_url)
    base_domain = parsed.netloc

    visited = set()
    queue = [start_url]
    results = []

    browser_config = BrowserConfig(headless=True)
    config = CrawlerRunConfig(
        page_timeout=30000,
        wait_until="domcontentloaded" if not js else "networkidle",
    )

    saved_stdout_fd = os.dup(1)
    devnull = open(os.devnull, 'w')
    os.dup2(devnull.fileno(), 1)

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            while queue and len(results) < max_pages:
                url = queue.pop(0)
                if url in visited:
                    continue
                visited.add(url)

                # Restore stdout for our progress messages
                os.dup2(saved_stdout_fd, 1)
                print(f"  [{len(results)+1}/{max_pages}] Crawling: {url}", file=sys.stderr)
                os.dup2(devnull.fileno(), 1)

                try:
                    result = await crawler.arun(url, config=config)
                    md = result.markdown or ""
                    if len(md) > max_chars:
                        md = md[:max_chars] + f"\n\n[截断：原长 {len(result.markdown)} 字符]"

                    links = []
                    if result.links:
                        for link in (result.links.get("internal", []) or []):
                            href = link.get("href", "")
                            if href and href.startswith(("http://", "https://")):
                                link_domain = urlparse(href).netloc
                                if not same_domain or link_domain == base_domain:
                                    if href not in visited:
                                        queue.append(href)
                                    links.append(href)

                    results.append({
                        "url": url,
                        "markdown": md,
                        "links": links[:20],
                        "char_count": len(md),
                        "success": result.success if hasattr(result, 'success') else True,
                    })
                except Exception as e:
                    results.append({
                        "url": url,
                        "markdown": f"[抓取失败: {e}]",
                        "links": [],
                        "char_count": 0,
                        "success": False,
                    })
    finally:
        os.dup2(saved_stdout_fd, 1)
        os.close(saved_stdout_fd)
        devnull.close()

    return results


async def crawl_sitemap(base_url: str, max_pages: int = 50, js: bool = False,
                        max_chars: int = 12000) -> list:
    """从 sitemap.xml 发现 URL 并抓取"""
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    sitemap_urls = [
        f"{base}/sitemap.xml",
        f"{base}/sitemap_index.xml",
        f"{base}/post-sitemap.xml",
    ]

    import urllib.request
    sitemap_content = None
    for surl in sitemap_urls:
        try:
            req = urllib.request.Request(surl, headers={"User-Agent": "Mozilla/5.0"})
            resp = urllib.request.urlopen(req, timeout=10)
            sitemap_content = resp.read().decode("utf-8", errors="replace")
            print(f"  Found sitemap: {surl}", file=sys.stderr)
            break
        except Exception:
            continue

    if not sitemap_content:
        print(f"  No sitemap found, falling back to multi mode", file=sys.stderr)
        return await crawl_multi(base_url, max_pages=max_pages, js=js, max_chars=max_chars)

    urls = re.findall(r'<loc>(.*?)</loc>', sitemap_content)
    if not urls:
        urls = re.findall(r'href=["\']([^"\']+)["\']', sitemap_content)

    page_urls = [u for u in urls if u.startswith("http") and not u.endswith(('.xml', '.xml.gz'))]
    page_urls = page_urls[:max_pages]

    print(f"  Found {len(page_urls)} URLs in sitemap", file=sys.stderr)

    browser_config = BrowserConfig(headless=True)
    config = CrawlerRunConfig(
        page_timeout=30000,
        wait_until="domcontentloaded" if not js else "networkidle",
    )

    saved_stdout_fd = os.dup(1)
    devnull = open(os.devnull, 'w')
    os.dup2(devnull.fileno(), 1)

    results = []
    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            for i, url in enumerate(page_urls):
                os.dup2(saved_stdout_fd, 1)
                print(f"  [{i+1}/{len(page_urls)}] {url}", file=sys.stderr)
                os.dup2(devnull.fileno(), 1)

                try:
                    result = await crawler.arun(url, config=config)
                    md = result.markdown or ""
                    if len(md) > max_chars:
                        md = md[:max_chars] + f"\n\n[截断：原长 {len(result.markdown)} 字符]"
                    results.append({
                        "url": url,
                        "markdown": md,
                        "char_count": len(md),
                        "success": result.success if hasattr(result, 'success') else True,
                    })
                except Exception as e:
                    results.append({
                        "url": url,
                        "markdown": f"[抓取失败: {e}]",
                        "char_count": 0,
                        "success": False,
                    })
    finally:
        os.dup2(saved_stdout_fd, 1)
        os.close(saved_stdout_fd)
        devnull.close()

    return results


def main():
    parser = argparse.ArgumentParser(description="crawl4ai wrapper for orion-research")
    parser.add_argument("url", help="Target URL")
    parser.add_argument("--mode", choices=["single", "multi", "sitemap"], default="single")
    parser.add_argument("--max-pages", type=int, default=10)
    parser.add_argument("--max-chars", type=int, default=12000)
    parser.add_argument("--same-domain", action="store_true", default=True)
    parser.add_argument("--js", action="store_true", help="Enable JS rendering")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--json", action="store_true", help="JSON output")

    args = parser.parse_args()

    print(f"🔍 Crawling: {args.url} (mode={args.mode}, js={args.js})", file=sys.stderr)

    if args.mode == "single":
        result = asyncio.run(crawl_single(args.url, js=args.js, max_chars=args.max_chars))
        output = result
    elif args.mode == "multi":
        output = asyncio.run(crawl_multi(
            args.url, max_pages=args.max_pages, js=args.js,
            max_chars=args.max_chars, same_domain=args.same_domain
        ))
    elif args.mode == "sitemap":
        output = asyncio.run(crawl_sitemap(
            args.url, max_pages=args.max_pages, js=args.js, max_chars=args.max_chars
        ))

    if args.json:
        text = json.dumps(output, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"✅ JSON saved to: {args.output}", file=sys.stderr)
        else:
            print(text)
    else:
        items = output if isinstance(output, list) else [output]
        for i, r in enumerate(items):
            if len(items) > 1:
                print(f"\n{'='*60}")
                print(f"📄 [{i+1}/{len(items)}] {r['url']}")
                print(f"   字符: {r.get('char_count', 0)}")
                print(f"{'='*60}")
            print(r.get("markdown", "[无内容]"))

    # Stats
    items = output if isinstance(output, list) else [output]
    total = sum(r.get("char_count", 0) for r in items)
    ok = sum(1 for r in items if r.get("success", False))
    print(f"\n📊 {ok}/{len(items)} 成功, {total} 字符", file=sys.stderr)


if __name__ == "__main__":
    main()
