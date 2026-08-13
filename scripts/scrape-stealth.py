#!/usr/bin/python3
"""scrape-stealth.py — Scrapling 反爬抓取 wrapper
用法：/usr/bin/python3 scrape-stealth.py <url> [--mode stealth|dynamic|http] [--max-chars N]

⚠️ 必须用 /usr/bin/python3（3.12）：Scrapling 装在 3.12 的 site-packages。
   如果 `python3` 指向其他版本（如 Hermes venv 3.11），lxml etree 会导入失败。
   环境变量：PYTHONPATH=$HOME/.local/lib/python3.12/site-packages

模式：
  http（默认）: 快速 HTTP + TLS 指纹伪装
  stealth:     绕过 Cloudflare/反爬
  dynamic:     完整浏览器 JS 渲染（SPA）

自动降级：http 模式遇到 403/429/空内容 → stealth → dynamic
"""
import sys
import argparse
import html
import re
from html.parser import HTMLParser


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return "".join(self.fed)


def strip_tags(html_text):
    s = MLStripper()
    s.feed(html_text)
    return s.get_data()


def clean_text(text):
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)
    return text.strip()


TIMEOUTS = {"http": 15000, "stealth": 30000, "dynamic": 45000}  # 毫秒，playwright 用 ms
MIN_CONTENT_LEN = 200  # 低于此长度视为无效，触发降级


def fetch_http(url, timeout):
    """快速 HTTP 抓取，TLS 指纹伪装"""
    from scrapling.fetchers import Fetcher

    page = Fetcher().get(url, timeout=timeout)
    return str(page.html_content) if page else ""


def fetch_stealth(url, timeout):
    """反检测抓取，绕过 Cloudflare"""
    from scrapling.fetchers import StealthyFetcher

    page = StealthyFetcher().fetch(url, timeout=timeout)
    return str(page.html_content) if page else ""


def fetch_dynamic(url, timeout):
    """完整浏览器 JS 渲染"""
    from scrapling.fetchers import DynamicFetcher

    page = DynamicFetcher().fetch(url, timeout=timeout)
    return str(page.html_content) if page else ""


FETCHERS = {
    "http": fetch_http,
    "stealth": fetch_stealth,
    "dynamic": fetch_dynamic,
}


def is_blocked(text):
    """检测是否被反爬拦截"""
    if not text:
        return True
    lower = text.lower()
    # Cloudflare challenge 页面特征
    cf_signals = [
        "checking your browser",
        "cloudflare",
        "attention required",
        "enable javascript and cookies",
        "ray id",
        "cf-browser-verification",
    ]
    return any(sig in lower for sig in cf_signals)


def main():
    parser = argparse.ArgumentParser(description="Scrapling 反爬抓取 wrapper")
    parser.add_argument("url", help="目标 URL")
    parser.add_argument(
        "--mode",
        choices=["http", "stealth", "dynamic"],
        default="http",
        help="抓取模式（默认 http）",
    )
    parser.add_argument(
        "--max-chars", type=int, default=8000, help="最大输出字符数（默认 8000）"
    )
    args = parser.parse_args()

    url = args.url
    mode = args.mode
    max_chars = args.max_chars

    # 按模式依次尝试，自动降级
    modes_order = {"http": ["http", "stealth", "dynamic"],
                   "stealth": ["stealth", "dynamic"],
                   "dynamic": ["dynamic"]}

    for try_mode in modes_order[mode]:
        timeout = TIMEOUTS[try_mode]
        try:
            raw = FETCHERS[try_mode](url, timeout)
            if not raw or is_blocked(raw):
                if try_mode != "dynamic":
                    print(f"[scrape-stealth] {try_mode} 模式内容无效或被拦截，降级...", file=sys.stderr)
                    continue
            text = strip_tags(raw)
            text = clean_text(text)
            if len(text) < MIN_CONTENT_LEN and try_mode != "dynamic":
                print(f"[scrape-stealth] {try_mode} 模式内容过短({len(text)}字符)，降级...", file=sys.stderr)
                continue
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            print(text)
            return
        except Exception as e:
            if try_mode != "dynamic":
                print(f"[scrape-stealth] {try_mode} 模式失败: {e}，降级...", file=sys.stderr)
                continue
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    print("Error: 所有模式均失败", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
