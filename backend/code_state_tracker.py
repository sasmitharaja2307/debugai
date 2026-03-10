"""
SELFHEAL AI – Code State Tracker (Time-Travel Debugging)
Snapshots entire project state before/after each run for diff-based analysis.
"""

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from backend.utils.logger import get_logger

log = get_logger(__name__)

_IGNORE = {".git", "__pycache__", "node_modules", ".selfheal_backups", "logs", ".venv", "venv"}
_TRACKED_EXTENSIONS = {
    ".py", ".js", ".ts", ".java", ".go", ".c", ".cpp", ".h",
    ".json", ".toml", ".txt", ".yml", ".yaml", ".env", ".mod", ".sum",
}


@dataclass
class FileSnapshot:
    path: str
    size: int
    checksum: str
    content: str


@dataclass
class ProjectSnapshot:
    timestamp: float
    run_id: str
    command: str
    success: bool
    files: Dict[str, FileSnapshot] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "run_id": self.run_id,
            "command": self.command,
            "success": self.success,
            "files": {k: asdict(v) for k, v in self.files.items()},
        }


@dataclass
class StateDiff:
    added: List[str]
    removed: List[str]
    modified: List[str]
    unchanged: List[str]

    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.modified)

    def to_dict(self) -> dict:
        return {
            "added": self.added,
            "removed": self.removed,
            "modified": self.modified,
            "unchanged": self.unchanged,
            "has_changes": self.has_changes(),
        }


class CodeStateTracker:
    """
    Maintains an ordered history of project snapshots.
    Allows diffing any two snapshots to identify what changed between runs.
    """

    _STORE_FILE = ".SELFHEAL_state.json"

    def __init__(self, project_root: str, max_history: int = 20):
        self.root = Path(project_root)
        self.max_history = max_history
        self._history: List[ProjectSnapshot] = []
        self._load()

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------

    def take_snapshot(self, run_id: str, command: str, success: bool) -> ProjectSnapshot:
        snap = ProjectSnapshot(
            timestamp=time.time(),
            run_id=run_id,
            command=command,
            success=success,
        )
        for file_path in self._iter_tracked_files():
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                rel = str(file_path.relative_to(self.root))
                checksum = hashlib.md5(content.encode()).hexdigest()
                snap.files[rel] = FileSnapshot(
                    path=rel,
                    size=file_path.stat().st_size,
                    checksum=checksum,
                    content=content[:4096],  # Store first 4 KB for diffing
                )
            except Exception:  # noqa: BLE001
                pass

        self._history.append(snap)
        if len(self._history) > self.max_history:
            self._history.pop(0)
        self._save()
        log.debug("Snapshot taken: run_id=%s files=%d", run_id, len(snap.files))
        return snap

    # ------------------------------------------------------------------
    # Diff
    # ------------------------------------------------------------------

    def diff(self, snap_a: ProjectSnapshot, snap_b: ProjectSnapshot) -> StateDiff:
        keys_a, keys_b = set(snap_a.files), set(snap_b.files)
        added = sorted(keys_b - keys_a)
        removed = sorted(keys_a - keys_b)
        common = keys_a & keys_b
        modified = [k for k in common if snap_a.files[k].checksum != snap_b.files[k].checksum]
        unchanged = [k for k in common if snap_a.files[k].checksum == snap_b.files[k].checksum]
        return StateDiff(added=added, removed=removed, modified=sorted(modified), unchanged=unchanged)

    def last_successful_snapshot(self) -> Optional[ProjectSnapshot]:
        for snap in reversed(self._history):
            if snap.success:
                return snap
        return None

    def latest_snapshot(self) -> Optional[ProjectSnapshot]:
        return self._history[-1] if self._history else None

    def get_history(self) -> List[dict]:
        return [
            {
                "run_id": s.run_id,
                "timestamp": s.timestamp,
                "command": s.command,
                "success": s.success,
                "file_count": len(s.files),
            }
            for s in self._history
        ]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save(self) -> None:
        store = self.root / self._STORE_FILE
        try:
            data = [s.to_dict() for s in self._history]
            store.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            log.warning("Could not persist state: %s", exc)

    def _load(self) -> None:
        store = self.root / self._STORE_FILE
        if not store.exists():
            return
        try:
            data = json.loads(store.read_text(encoding="utf-8"))
            for item in data:
                files = {
                    k: FileSnapshot(**v)
                    for k, v in item.get("files", {}).items()
                }
                snap = ProjectSnapshot(
                    timestamp=item["timestamp"],
                    run_id=item["run_id"],
                    command=item["command"],
                    success=item["success"],
                    files=files,
                )
                self._history.append(snap)
        except Exception as exc:  # noqa: BLE001
            log.warning("Could not load state history: %s", exc)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _iter_tracked_files(self):
        for p in self.root.rglob("*"):
            if p.is_file() and p.suffix in _TRACKED_EXTENSIONS:
                if not any(part in _IGNORE for part in p.parts):
                    yield p
