"""
SELFHEAL AI – Patch Applier Utility
Safely applies code patches and command fixes to the developer's project.
Uses the Command Pattern for safe, reversible operations.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from backend.utils.logger import get_logger

log = get_logger(__name__)


class PatchApplier:
    """Command Pattern: encapsulates a patch operation for safe execution and rollback."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self._backup_dir = self.project_root / ".selfheal_backups"
        self._backup_dir.mkdir(exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def apply_file_patch(
        self,
        relative_path: str,
        new_content: str,
        *,
        create_backup: bool = True,
    ) -> dict:
        """
        Overwrite a file with patched content.

        Returns a result dict with status, backup_path, and message.
        """
        target = self.project_root / relative_path
        backup_path: Optional[Path] = None

        try:
            if create_backup and target.exists():
                backup_path = self._backup(target)
                log.debug("Backup created: %s", backup_path)

            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(new_content, encoding="utf-8")
            log.info("Patch applied to %s", relative_path)
            return {
                "status": "success",
                "file": str(relative_path),
                "backup_path": str(backup_path) if backup_path else None,
                "message": f"File {relative_path} patched successfully.",
            }
        except Exception as exc:  # noqa: BLE001
            log.error("Failed to patch %s: %s", relative_path, exc)
            return {"status": "error", "file": str(relative_path), "message": str(exc)}

    def apply_shell_command(self, command: str, cwd: Optional[str] = None) -> dict:
        """
        Execute a shell fix command (e.g., pip install, npm install).

        Returns stdout, stderr, and exit code.
        """
        work_dir = cwd or str(self.project_root)
        log.info("Running fix command: %s", command)
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return {
                "status": "success" if result.returncode == 0 else "error",
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "command": command, "message": "Command timed out after 120s."}
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "command": command, "message": str(exc)}

    def rollback(self, relative_path: str) -> dict:
        """Restore the most recent backup of a file."""
        target = self.project_root / relative_path
        candidates = sorted(
            self._backup_dir.glob(f"{Path(relative_path).name}_*"),
            reverse=True,
        )
        if not candidates:
            return {"status": "error", "message": "No backup found."}
        shutil.copy2(candidates[0], target)
        log.info("Rolled back %s from %s", relative_path, candidates[0])
        return {"status": "success", "restored_from": str(candidates[0])}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _backup(self, target: Path) -> Path:
        from datetime import datetime

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = self._backup_dir / f"{target.name}_{ts}"
        shutil.copy2(target, dest)
        return dest
