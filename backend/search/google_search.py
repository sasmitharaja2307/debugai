"""
SELFHEAL AI – Google Search (via SerpAPI or DuckDuckGo fallback)
Fetches web search results for debugging context.
"""

import json
import os
import urllib.parse
import urllib.request
from typing import Dict, List

from backend.utils.logger import get_logger

log = get_logger(__name__)


class GoogleSearch:
    """
    Searches the web for error context.
    Priority: SerpAPI (if SERPAPI_KEY set) → DuckDuckGo Instant Answer API (free).
    """

    def __init__(self):
        self._serpapi_key = os.getenv("SERPAPI_KEY", "")

    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        if self._serpapi_key:
            return self._search_serpapi(query, max_results)
        return self._search_duckduckgo(query, max_results)

    # ------------------------------------------------------------------

    def _search_serpapi(self, query: str, max_results: int) -> List[Dict]:
        params = urllib.parse.urlencode({
            "q": query,
            "api_key": self._serpapi_key,
            "num": max_results,
            "engine": "google",
        })
        url = f"https://serpapi.com/search?{params}"
        results: List[Dict] = []
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            for item in data.get("organic_results", [])[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "google",
                })
        except Exception as exc:  # noqa: BLE001
            log.warning("SerpAPI search failed: %s", exc)
        return results

    def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict]:
        params = urllib.parse.urlencode({"q": query, "format": "json", "no_html": 1, "skip_disambig": 1})
        url = f"https://api.duckduckgo.com/?{params}"
        results: List[Dict] = []
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", query),
                    "link": data.get("AbstractURL", ""),
                    "snippet": data.get("AbstractText", "")[:500],
                    "source": "duckduckgo",
                })

            for related in data.get("RelatedTopics", [])[:max_results - 1]:
                if "Text" in related:
                    results.append({
                        "title": related.get("Text", "")[:80],
                        "link": related.get("FirstURL", ""),
                        "snippet": related.get("Text", ""),
                        "source": "duckduckgo",
                    })
        except Exception as exc:  # noqa: BLE001
            log.warning("DuckDuckGo search failed: %s", exc)
        return results
