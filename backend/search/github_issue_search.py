"""
POLYHEAL AI – GitHub Issue Search
Queries the GitHub Search API for relevant issues and discussions.
"""

import json
import os
import urllib.parse
import urllib.request
from typing import Dict, List

from backend.utils.logger import get_logger

log = get_logger(__name__)

_GH_API = "https://api.github.com/search/issues"


class GitHubIssueSearch:
    """Search GitHub Issues/PRs using the GitHub Search API."""

    def __init__(self):
        self._token = os.getenv("GITHUB_TOKEN", "")

    def search(self, query: str, language: str = "", max_results: int = 5) -> List[Dict]:
        qualifier = f"language:{language}" if language else ""
        full_query = f"{query} {qualifier} type:issue state:closed".strip()
        params = urllib.parse.urlencode({"q": full_query, "per_page": max_results, "sort": "reactions"})
        url = f"{_GH_API}?{params}"

        headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "PolyHeal-AI"}
        if self._token:
            headers["Authorization"] = f"token {self._token}"

        results: List[Dict] = []
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            for item in data.get("items", [])[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("html_url", ""),
                    "state": item.get("state", ""),
                    "comments": item.get("comments", 0),
                    "reactions": item.get("reactions", {}).get("total_count", 0),
                    "body": (item.get("body") or "")[:500],
                    "labels": [l["name"] for l in item.get("labels", [])],
                    "source": "github",
                })
        except Exception as exc:  # noqa: BLE001
            log.warning("GitHub Issue search failed: %s", exc)
        return results
