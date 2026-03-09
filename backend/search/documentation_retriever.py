"""
POLYHEAL AI – Documentation Retriever & Search Aggregator
Combines results from all search sources into a unified context summary.
"""

import urllib.parse
import urllib.request
from typing import Dict, List

from backend.search.github_issue_search import GitHubIssueSearch
from backend.search.google_search import GoogleSearch
from backend.search.stackoverflow_search import StackOverflowSearch
from backend.utils.logger import get_logger

log = get_logger(__name__)

_OFFICIAL_DOCS = {
    "python": "https://docs.python.org/3/search.html?q=",
    "java": "https://docs.oracle.com/en/java/javase/21/docs/api/search.html?q=",
    "javascript": "https://developer.mozilla.org/en-US/search?q=",
    "node": "https://nodejs.org/en/search/?q=",
    "go": "https://pkg.go.dev/search?q=",
    "c": "https://en.cppreference.com/mwiki/index.php?title=Special:Search&search=",
    "cpp": "https://en.cppreference.com/mwiki/index.php?title=Special:Search&search=",
}


class DocumentationRetriever:
    """Returns official documentation links for error terms."""

    def get_doc_links(self, language: str, query: str) -> List[Dict]:
        base_url = _OFFICIAL_DOCS.get(language.lower(), "")
        if not base_url:
            return []
        encoded = urllib.parse.quote_plus(query[:100])
        return [{
            "title": f"Official {language.capitalize()} Documentation – {query[:50]}",
            "link": base_url + encoded,
            "snippet": f"Search official {language} documentation for: {query}",
            "source": "official_docs",
        }]


class SearchAggregator:
    """
    Multi-source intelligent search aggregator.
    Combines Google, StackOverflow, GitHub, and official docs.
    """

    def __init__(self):
        self._google = GoogleSearch()
        self._so = StackOverflowSearch()
        self._gh = GitHubIssueSearch()
        self._docs = DocumentationRetriever()

    def search(self, error_message: str, language: str = "", max_per_source: int = 3) -> dict:
        """
        Run all searches in sequence and return a structured result + summary string.
        """
        query = f"{language} {error_message}".strip()
        log.info("Searching all sources for: %s", query[:80])

        google_results = self._google.search(query, max_results=max_per_source)
        so_results = self._so.search(query, language=language, max_results=max_per_source)
        gh_results = self._gh.search(query, language=language, max_results=max_per_source)
        doc_links = self._docs.get_doc_links(language, error_message[:80])

        all_results = google_results + so_results + gh_results + doc_links
        summary = self._build_summary(all_results)

        return {
            "google": google_results,
            "stackoverflow": so_results,
            "github": gh_results,
            "docs": doc_links,
            "summary": summary,
        }

    def _build_summary(self, results: List[Dict]) -> str:
        lines: List[str] = []
        for r in results[:8]:
            title = r.get("title", "")
            snippet = r.get("snippet", r.get("body", r.get("excerpt", ""))).strip()[:200]
            source = r.get("source", "")
            if title or snippet:
                lines.append(f"[{source}] {title}: {snippet}")
        return "\n".join(lines)
