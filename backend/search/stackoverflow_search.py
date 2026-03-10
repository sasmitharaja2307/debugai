"""
SELFHEAL AI – StackOverflow Search
Queries the StackOverflow API for relevant questions and answers.
"""

import urllib.parse
import urllib.request
import json
from typing import List, Dict
from backend.utils.logger import get_logger

log = get_logger(__name__)

_SO_API = "https://api.stackexchange.com/2.3/search/advanced"


class StackOverflowSearch:
    """Search StackOverflow for error-related questions using the public API."""

    def search(self, query: str, language: str = "", max_results: int = 5) -> List[Dict]:
        """
        Returns a list of relevant SO questions with accepted answers.
        """
        tag = self._language_to_tag(language)
        params = {
            "order": "desc",
            "sort": "relevance",
            "q": query,
            "site": "stackoverflow",
            "pagesize": max_results,
            "filter": "withbody",
        }
        if tag:
            params["tagged"] = tag

        url = _SO_API + "?" + urllib.parse.urlencode(params)
        results: List[Dict] = []
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            for item in data.get("items", [])[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "score": item.get("score", 0),
                    "is_answered": item.get("is_answered", False),
                    "answer_count": item.get("answer_count", 0),
                    "tags": item.get("tags", []),
                    "excerpt": item.get("body", "")[:500],
                    "source": "stackoverflow",
                })
        except Exception as exc:  # noqa: BLE001
            log.warning("StackOverflow search failed: %s", exc)
        return results

    @staticmethod
    def _language_to_tag(language: str) -> str:
        mapping = {
            "python": "python",
            "java": "java",
            "javascript": "javascript",
            "node": "node.js",
            "go": "go",
            "c": "c",
            "cpp": "c++",
        }
        return mapping.get(language.lower(), "")
