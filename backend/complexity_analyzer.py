"""
SELFHEAL AI – Complexity Analyzer
Evaluates time and space complexity of generated code solutions.
"""

import re
from dataclasses import dataclass
from typing import Optional

from backend.utils.logger import get_logger

log = get_logger(__name__)

# Map of known algorithm patterns to their Big-O complexities
_KNOWN_PATTERNS = {
    # Sorting
    r"\bbubble[_\s]?sort\b": ("O(n²)", "O(1)", "low"),
    r"\bselection[_\s]?sort\b": ("O(n²)", "O(1)", "low"),
    r"\binsertion[_\s]?sort\b": ("O(n²)", "O(1)", "low"),
    r"\bmerge[_\s]?sort\b": ("O(n log n)", "O(n)", "medium"),
    r"\bquick[_\s]?sort\b": ("O(n log n) avg", "O(log n)", "medium"),
    r"\bheap[_\s]?sort\b": ("O(n log n)", "O(1)", "medium"),
    r"\btimsort\b|\.sort\(\)|sorted\(": ("O(n log n)", "O(n)", "medium"),
    # Search
    r"\bbinary[_\s]?search\b": ("O(log n)", "O(1)", "high"),
    r"\blinear[_\s]?search\b|for .+ in .+:": ("O(n)", "O(1)", "high"),
    # Hashing
    r"\bdict\b|\bHashMap\b|\bmap\[": ("O(1) avg", "O(n)", "high"),
    # Graph
    r"\bbfs\b|breadth[_\s]?first": ("O(V+E)", "O(V)", "medium"),
    r"\bdfs\b|depth[_\s]?first": ("O(V+E)", "O(V)", "medium"),
    r"\bdijkstra\b": ("O((V+E) log V)", "O(V)", "medium"),
    # DP
    r"\bdynamic[_\s]?programming\b|\bdp\[": ("O(n²)", "O(n)", "medium"),
    # Simple loops
    r"for .+ in range\(.+\):\s*\n(?:\s+.+\n)*\s+for .+ in range": ("O(n²)", "O(1)", "medium"),
    r"for .+ in range\(.+\):": ("O(n)", "O(1)", "high"),
}


@dataclass
class ComplexityReport:
    time_complexity: str
    space_complexity: str
    performance_score: int     # 1-10 (10 = best)
    explanation: str

    def to_dict(self) -> dict:
        return {
            "time_complexity": self.time_complexity,
            "space_complexity": self.space_complexity,
            "performance_score": self.performance_score,
            "explanation": self.explanation,
        }


_PERF_SCORES = {
    "O(1)": 10,
    "O(log n)": 9,
    "O(1) avg": 9,
    "O(n)": 7,
    "O(n log n)": 6,
    "O(n log n) avg": 6,
    "O((V+E) log V)": 5,
    "O(V+E)": 5,
    "O(n²)": 3,
    "O(2^n)": 1,
    "O(n!)": 1,
}


class ComplexityAnalyzer:
    """
    Estimates Big-O time and space complexity from code or description.
    Returns a performance score (1-10) suitable for UI ranking.
    """

    def analyze_code(self, code: str, description: str = "") -> ComplexityReport:
        text = (code + " " + description).lower()
        best_time = "O(n)"        # default assumption
        best_space = "O(1)"
        best_readability = "medium"

        for pattern, (tc, sc, readability) in _KNOWN_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                best_time = tc
                best_space = sc
                best_readability = readability
                break

        score = _PERF_SCORES.get(best_time, 5)
        explanation = (
            f"Estimated complexity based on code patterns. "
            f"Time: {best_time}, Space: {best_space}. "
            f"Readability: {best_readability}."
        )
        return ComplexityReport(
            time_complexity=best_time,
            space_complexity=best_space,
            performance_score=score,
            explanation=explanation,
        )

    def from_description(self, description: str) -> ComplexityReport:
        """Parse explicit O(...) notation from an LLM solution description."""
        tc_match = re.search(r"time[^O]*?(O\([^)]+\))", description, re.IGNORECASE)
        sc_match = re.search(r"space[^O]*?(O\([^)]+\))", description, re.IGNORECASE)
        tc = tc_match.group(1) if tc_match else "O(n)"
        sc = sc_match.group(1) if sc_match else "O(1)"
        score = _PERF_SCORES.get(tc, 5)
        return ComplexityReport(
            time_complexity=tc,
            space_complexity=sc,
            performance_score=score,
            explanation=f"Extracted from solution description. Time: {tc}, Space: {sc}.",
        )
