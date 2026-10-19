#!/usr/bin/env python3
"""Print a human title for a URL. Empty output = no title found (fallback to WebFetch / URL).

GitLab issues/work items/MRs and GitHub issues/PRs go through `glab` / `gh`
(works for private repos on any logged-in host); everything else via og:title / <title>.
"""
import html, pathlib, re, sys, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import forge

url = sys.argv[1]

item = forge.lookup(url)
if item:
    print(f"{item[0]}: {item[1]}")
    sys.exit(0)

try:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    page = urllib.request.urlopen(req, timeout=10).read(500_000).decode("utf-8", "replace")
except Exception:
    sys.exit(0)

for pattern in (r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title',
                r"<title[^>]*>(.*?)</title>"):
    found = re.search(pattern, page, re.I | re.S)
    if found and found.group(1).strip():
        print(html.unescape(" ".join(found.group(1).split())))
        break
