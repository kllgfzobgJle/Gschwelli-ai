"""Browser & Web Research tools: direct URL opening, DuckDuckGo search, and YouTube search (ported from Mark-LVI browser_control.py & web_search.py)."""

from __future__ import annotations

import os
import urllib.parse
import webbrowser
from typing import List, Optional

from tools.registry import action


def _normalize_url(raw: str) -> str:
    url = (raw or "").strip()
    if not url:
        return "https://www.google.com"
    if "://" in url:
        return url
    if "." not in url:
        return f"https://www.{url}.com"
    return f"https://{url}"


@action(
    name="open_url",
    description="Open a website URL or domain in the default browser on the interactive desktop.",
    parameters={"url": "str"},
)
def open_url(url: str = "") -> str:
    target = _normalize_url(url)
    try:
        os.startfile(target)  # noqa: S606
    except Exception:
        webbrowser.open(target)
    return f"status=done action=open_url url=\"{target}\""


@action(
    name="web_search",
    description="Search the web via DuckDuckGo (ddgs) and return top results, or open the search in the browser.",
    parameters={"query": "str", "open_in_browser": "Optional[bool]", "max_results": "Optional[int]"},
)
def web_search(query: str = "", open_in_browser: bool = False, max_results: int = 5) -> str:
    q = (query or "").strip()
    if not q:
        return "status=failed action=web_search reason=\"Empty search query\""

    if open_in_browser:
        encoded = urllib.parse.quote_plus(q)
        search_url = f"https://www.google.com/search?q={encoded}"
        return open_url(search_url)

    try:
        from ddgs import DDGS

        results: List[str] = []
        with DDGS() as ddgs:
            for r in ddgs.text(q, max_results=int(max_results or 5)):
                title = (r.get("title") or "").strip()
                href = (r.get("href") or "").strip()
                body = (r.get("body") or "").strip()[:160]
                results.append(f"{title} ({href}): {body}")
        if results:
            return f"status=done action=web_search query=\"{q}\" count={len(results)} results=\"{' || '.join(results)}\""
    except Exception:
        pass

    encoded = urllib.parse.quote_plus(q)
    search_url = f"https://www.google.com/search?q={encoded}"
    open_url(search_url)
    return f"status=done action=web_search query=\"{q}\" opened_browser=\"{search_url}\""


@action(
    name="youtube_search",
    description="Open a YouTube search or video query in the browser.",
    parameters={"query": "str"},
)
def youtube_search(query: str = "") -> str:
    q = (query or "").strip()
    if not q:
        return open_url("https://www.youtube.com")
    encoded = urllib.parse.quote_plus(q)
    return open_url(f"https://www.youtube.com/results?search_query={encoded}")
