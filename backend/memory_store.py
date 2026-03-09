"""
POLYHEAL AI – Debug Memory Store
Persists debugging cases (error → solution mappings) with vector-based similarity.
Self-learning: suggests previously successful fixes for similar errors.
"""

import json
import math
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional

from backend.utils.logger import get_logger

log = get_logger(__name__)

_STORE_FILE = ".polyheal_memory.json"


@dataclass
class DebugCase:
    case_id: str
    timestamp: float
    language: str
    error_type: str
    error_message: str
    solution_title: str
    solution_code: str
    fix_command: str
    was_successful: bool
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _simple_tfidf_vector(text: str) -> dict:
    """Very lightweight bag-of-words vector (no external deps)."""
    words = re.findall(r"[a-z]+", text.lower())
    vec: dict = {}
    for w in words:
        vec[w] = vec.get(w, 0) + 1
    total = sum(vec.values()) or 1
    return {k: v / total for k, v in vec.items()}


def _cosine_sim(a: dict, b: dict) -> float:
    keys = set(a) & set(b)
    if not keys:
        return 0.0
    dot = sum(a[k] * b[k] for k in keys)
    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))
    return dot / (mag_a * mag_b + 1e-9)


class MemoryStore:
    """
    Singleton-style in-memory + file-backed debug case store.
    Supports fuzzy similarity search via cosine similarity on TF-IDF vectors.
    """

    _instance: Optional["MemoryStore"] = None

    def __new__(cls, project_root: str = "."):
        if cls._instance is None:
            obj = super().__new__(cls)
            obj._initialized = False
            cls._instance = obj
        return cls._instance

    def __init__(self, project_root: str = "."):
        if self._initialized:
            return
        self.root = Path(project_root)
        self._cases: List[DebugCase] = []
        self._load()
        self._initialized = True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store(self, case: DebugCase) -> None:
        self._cases.append(case)
        self._save()
        log.info("Stored debug case: %s", case.case_id)

    def find_similar(self, error_message: str, language: str, top_k: int = 3) -> List[DebugCase]:
        """Return top_k most similar past cases using cosine similarity."""
        query_vec = _simple_tfidf_vector(error_message + " " + language)
        scored: List[tuple] = []
        for case in self._cases:
            if not case.was_successful:
                continue
            case_vec = _simple_tfidf_vector(
                case.error_message + " " + case.language + " " + " ".join(case.tags)
            )
            sim = _cosine_sim(query_vec, case_vec)
            if case.language == language:
                sim *= 1.3   # Boost same-language matches
            scored.append((sim, case))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k] if _ > 0.1]

    def mark_successful(self, case_id: str) -> None:
        for c in self._cases:
            if c.case_id == case_id:
                c.was_successful = True
        self._save()

    def all_cases(self) -> List[dict]:
        return [c.to_dict() for c in self._cases]

    def recent_cases(self, n: int = 10) -> List[dict]:
        return [c.to_dict() for c in sorted(self._cases, key=lambda x: x.timestamp, reverse=True)[:n]]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save(self) -> None:
        store_path = self.root / _STORE_FILE
        try:
            store_path.write_text(
                json.dumps([c.to_dict() for c in self._cases], indent=2),
                encoding="utf-8",
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("Could not save memory store: %s", exc)

    def _load(self) -> None:
        store_path = self.root / _STORE_FILE
        if not store_path.exists():
            return
        try:
            data = json.loads(store_path.read_text(encoding="utf-8"))
            self._cases = [DebugCase(**item) for item in data]
            log.info("Loaded %d debug case(s) from memory.", len(self._cases))
        except Exception as exc:  # noqa: BLE001
            log.warning("Could not load memory store: %s", exc)
