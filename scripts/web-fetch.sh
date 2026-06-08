#!/usr/bin/env bash
# web-fetch.sh — 替代 OpenClaw web_fetch 工具的 curl 封装
# Usage: bash web-fetch.sh <url> [max_chars]
# Output: markdown text, truncated to max_chars

URL="$1"
MAX_CHARS="${2:-8000}"

if [ -z "$URL" ]; then
  echo "Usage: web-fetch.sh <url> [max_chars]" >&2
  exit 1
fi

curl -s --max-time 15 \
  -H "User-Agent: Mozilla/5.0 (compatible; OpenClaw/1.0)" \
  -H "Accept: text/html,application/xhtml+xml" \
  "$URL" 2>/dev/null | \
  sed -e 's/<[^>]*>//g' | \
  sed -e 's/&nbsp;/ /g' -e 's/&amp;/\&/g' -e 's/&lt;/</g' -e 's/&gt;/>/g' -e 's/&quot;/"/g' | \
  tr -s ' \n' | \
  cut -c1-"$MAX_CHARS"
