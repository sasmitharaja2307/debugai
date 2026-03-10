"""
SELFHEAL AI – Command Runner
Uses Python subprocess to execute developer commands and capture all output.
Observer Pattern: notifies subscribers on each run event.
"""

import subprocess
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from backend.utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class RunResult:
    command: str
    stdout: str
    stderr: str
    returncode: int
    duration_ms: float
    timestamp: float = field(default_factory=time.time)

    @property
    def success(self) -> bool:
        return self.returncode == 0

    def to_dict(self) -> dict:
        return {
            "command": self.command,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "returncode": self.returncode,
            "duration_ms": round(self.duration_ms, 2),
            "timestamp": self.timestamp,
            "success": self.success,
        }


class CommandRunner:
    """
    Executes developer commands and notifies registered observers.

    Supports: python, java, node, go, gcc, g++
    """

    SUPPORTED_PREFIXES = ("python", "java", "node", "go", "gcc", "g++", "npm", "mvn", "cargo")

    def __init__(self, cwd: Optional[str] = None, timeout: int = 60):
        self.cwd = cwd
        self.timeout = timeout
        self._observers: List[Callable[[RunResult], None]] = []

    # ------------------------------------------------------------------
    # Observer Pattern
    # ------------------------------------------------------------------

    def subscribe(self, callback: Callable[[RunResult], None]) -> None:
        """Register an observer to be called after every command run."""
        self._observers.append(callback)

    def _notify(self, result: RunResult) -> None:
        for cb in self._observers:
            try:
                cb(result)
            except Exception as exc:  # noqa: BLE001
                log.warning("Observer raised an exception: %s", exc)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run(self, command: str) -> RunResult:
        """
        Execute *command* in a subprocess and return a RunResult.

        Both stdout and stderr are captured separately.
        """
        log.info("Running command: %s", command)
        start = time.perf_counter()
        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            duration = (time.perf_counter() - start) * 1000
            result = RunResult(
                command=command,
                stdout=proc.stdout,
                stderr=proc.stderr,
                returncode=proc.returncode,
                duration_ms=duration,
            )
        except subprocess.TimeoutExpired:
            duration = (time.perf_counter() - start) * 1000
            result = RunResult(
                command=command,
                stdout="",
                stderr=f"Command timed out after {self.timeout}s",
                returncode=-1,
                duration_ms=duration,
            )
        except Exception as exc:  # noqa: BLE001
            duration = (time.perf_counter() - start) * 1000
            result = RunResult(
                command=command,
                stdout="",
                stderr=str(exc),
                returncode=-2,
                duration_ms=duration,
            )

        log.debug("Command finished | rc=%d | %.0fms", result.returncode, result.duration_ms)
        self._notify(result)
        return result
