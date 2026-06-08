#!/usr/bin/env python3
"""web-fetch.py — 改进版网页抓取，用 html.parser 做干净解析"""
import sys
import urllib.request
import html
import re
from html.parser import HTMLParser

URL = sys.argv[1] if len(sys.argv) > 1 else None
MAX_CHARS = int(sys.argv[2]) if len(sys.argv) > 2 else 8000

if not URL:
    print("Usage: python3 web-fetch.py <url> [max_chars]", file=sys.stderr)
    sys.exit(1)

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html_text):
    s = MLStripper()
    s.feed(html_text)
    return s.get_data()

def clean_text(text):
    # 解码 HTML 实体
    text = html.unescape(text)
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text)
    # 移除特殊字符
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
    return text.strip()

try:
    req = urllib.request.Request(
        URL,
        headers={
            'User-Agent': 'Mozilla/5.0 (compatible; OpenClaw/1.0; ResearchBot)',
            'Accept': 'text/html,application/xhtml+xml',
        }
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        html_content = response.read().decode('utf-8', errors='ignore')
    
    # 提取 body 或 main content
    body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
    if body_match:
        html_content = body_match.group(1)
    
    # 移除 script 和 style
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # 解析并提取文本
    text = strip_tags(html_content)
    text = clean_text(text)
    
    # 截断
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "..."
    
    print(text)
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
