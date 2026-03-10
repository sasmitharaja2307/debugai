"""
SELFHEAL AI – Solution Generator
Uses an LLM (OpenAI/Gemini) to generate multiple ranked solutions for a detected error.
Each solution includes code, time/space complexity, and security evaluation.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.complexity_analyzer import ComplexityAnalyzer, ComplexityReport
from backend.security_checker import SecurityChecker, SecurityReport
from backend.utils.logger import get_logger

log = get_logger(__name__)

_PROMPT_TEMPLATE = """
You are SELFHEAL AI, an expert multi-language debugging assistant.

## Error Context
- Language: {language}
- Error Type: {error_type}
- Error Message: {error_message}
- File: {file}
- Line: {line}

## Code Snippet
```
{code_snippet}
```

## Environment Context
{env_context}

## Search Results Summary
{search_summary}

## Task
Generate exactly 3 distinct solutions for this error.
For EACH solution produce a JSON object with these keys:
- "title": short label (e.g., "Quick Fix", "Best Practice", "Performance Optimized")
- "explanation": clear explanation of what caused the error and how this solution fixes it
- "code_patch": the corrected code or shell command (use ```language ... ``` fences)
- "fix_command": optional shell command to run (e.g., "pip install requests")
- "time_complexity": Big-O time complexity (e.g., "O(n log n)")
- "space_complexity": Big-O space complexity (e.g., "O(n)")
- "security_notes": any security considerations for this fix
- "difficulty": "easy" | "medium" | "hard"
- "tags": array of relevant tags

Respond ONLY with a JSON array of 3 solution objects. No extra text.
"""


@dataclass
class Solution:
    index: int
    title: str
    explanation: str
    code_patch: str
    fix_command: str
    time_complexity: str
    space_complexity: str
    security_notes: str
    difficulty: str
    tags: List[str]
    performance_score: int = 5
    security_score: int = 100
    security_alerts: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "title": self.title,
            "explanation": self.explanation,
            "code_patch": self.code_patch,
            "fix_command": self.fix_command,
            "time_complexity": self.time_complexity,
            "space_complexity": self.space_complexity,
            "security_notes": self.security_notes,
            "difficulty": self.difficulty,
            "tags": self.tags,
            "performance_score": self.performance_score,
            "security_score": self.security_score,
            "security_alerts": self.security_alerts,
        }


class SolutionGenerator:
    """
    Calls the configured LLM API and post-processes results:
    - Enriches each solution with complexity analysis
    - Runs security checks on each solution
    """

    def __init__(self):
        self._complexity = ComplexityAnalyzer()
        self._security = SecurityChecker()
        self._provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self._api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY", "")
        self._model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate(
        self,
        error: Dict[str, Any],
        code_snippet: str = "",
        env_context: str = "",
        search_summary: str = "",
    ) -> List[Solution]:
        prompt = _PROMPT_TEMPLATE.format(
            language=error.get("language", "unknown"),
            error_type=error.get("error_type", "Error"),
            error_message=error.get("message", ""),
            file=error.get("file", "N/A"),
            line=error.get("line", "N/A"),
            code_snippet=code_snippet[:1500] or "(not provided)",
            env_context=env_context[:500] or "(not provided)",
            search_summary=search_summary[:1000] or "(not provided)",
        )

        raw_solutions = self._call_llm(prompt)
        solutions: List[Solution] = []

        for i, s in enumerate(raw_solutions[:3]):
            # Complexity enrichment
            complexity: ComplexityReport = self._complexity.from_description(
                f"time {s.get('time_complexity', '')} space {s.get('space_complexity', '')}"
            )
            # Security check on code patch
            sec_report: SecurityReport = self._security.check(s.get("code_patch", ""))

            solutions.append(Solution(
                index=i + 1,
                title=s.get("title", f"Solution {i+1}"),
                explanation=s.get("explanation", ""),
                code_patch=s.get("code_patch", ""),
                fix_command=s.get("fix_command", ""),
                time_complexity=complexity.time_complexity,
                space_complexity=complexity.space_complexity,
                security_notes=s.get("security_notes", ""),
                difficulty=s.get("difficulty", "medium"),
                tags=s.get("tags", []),
                performance_score=complexity.performance_score,
                security_score=sec_report.security_score,
                security_alerts=[a.to_dict() for a in sec_report.alerts],
            ))

        if not solutions:
            solutions = self._fallback_solutions(error)

        log.info("Generated %d solution(s) for error: %s", len(solutions), error.get("error_type"))
        return solutions

    # ------------------------------------------------------------------
    # LLM back-ends
    # ------------------------------------------------------------------

    def _call_llm(self, prompt: str) -> List[dict]:
        if self._provider == "openai":
            return self._call_openai(prompt)
        elif self._provider == "gemini":
            return self._call_gemini(prompt)
        else:
            log.warning("Unknown LLM provider '%s'. Using fallback.", self._provider)
            return []

    def _call_openai(self, prompt: str) -> List[dict]:
        try:
            import openai  # type: ignore

            client = openai.OpenAI(api_key=self._api_key)
            resp = client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2048,
            )
            content = resp.choices[0].message.content or "[]"
            return self._parse_json(content)
        except Exception as exc:  # noqa: BLE001
            log.error("OpenAI call failed: %s", exc)
            return []

    def _call_gemini(self, prompt: str) -> List[dict]:
        try:
            import google.generativeai as genai  # type: ignore

            genai.configure(api_key=self._api_key)
            model = genai.GenerativeModel(self._model or "gemini-pro")
            resp = model.generate_content(prompt)
            return self._parse_json(resp.text)
        except Exception as exc:  # noqa: BLE001
            log.error("Gemini call failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_json(self, text: str) -> List[dict]:
        """Extract JSON array from LLM response (handles markdown fences)."""
        import re

        text = re.sub(r"```(?:json)?\n?", "", text).strip()
        try:
            result = json.loads(text)
            return result if isinstance(result, list) else []
        except json.JSONDecodeError:
            # Try to find JSON array anywhere in the text
            m = re.search(r"\[.*\]", text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:  # noqa: BLE001
                    pass
        return []

    def _fallback_solutions(self, error: Dict[str, Any]) -> List[Solution]:
        """Return template solutions when LLM is unavailable."""
        lang = error.get("language", "unknown")
        msg = error.get("message", "Unknown error")
        return [
            Solution(
                index=1,
                title="Quick Fix (Offline)",
                explanation=f"Detected {lang} error: {msg}. Review the stack trace and verify imports/syntax.",
                code_patch="# Review the error above and fix the identified line.",
                fix_command="",
                time_complexity="N/A",
                space_complexity="N/A",
                security_notes="No automated security analysis performed.",
                difficulty="easy",
                tags=[lang, "manual"],
                performance_score=5,
                security_score=80,
            )
        ]
