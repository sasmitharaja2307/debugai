"""
SELFHEAL AI – Error Detector
Parses raw command output to identify errors across all supported languages.
Strategy Pattern: each language has its own detection strategy.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from backend.utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class DetectedError:
    language: str
    error_type: str
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    raw_output: str = ""
    traceback: str = ""

    def to_dict(self) -> dict:
        return {
            "language": self.language,
            "error_type": self.error_type,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "raw_output": self.raw_output,
            "traceback": self.traceback,
        }


# ---------------------------------------------------------------------------
# Per-language detection strategies
# ---------------------------------------------------------------------------

class _PythonStrategy:
    LANG = "python"

    def detect(self, stderr: str, stdout: str) -> Optional[DetectedError]:
        if "Traceback" not in stderr and "Error" not in stderr:
            return None
        error_type = "UnknownError"
        message = ""
        m = re.search(r"^(\w+(?:\.\w+)*Error|Exception): (.+)$", stderr, re.MULTILINE)
        if m:
            error_type, message = m.group(1), m.group(2)

        file_, line_ = None, None
        fm = re.search(r'File "(.+?)", line (\d+)', stderr)
        if fm:
            file_, line_ = fm.group(1), int(fm.group(2))

        return DetectedError(
            language=self.LANG,
            error_type=error_type,
            message=message or stderr.strip().splitlines()[-1],
            file=file_,
            line=line_,
            raw_output=stderr,
            traceback=stderr,
        )


class _JavaStrategy:
    LANG = "java"

    def detect(self, stderr: str, stdout: str) -> Optional[DetectedError]:
        if "Exception" not in stderr and "Error" not in stderr:
            return None
        m = re.search(r"([\w.]+(?:Exception|Error)): (.+)", stderr)
        error_type = m.group(1) if m else "JavaException"
        message = m.group(2) if m else stderr.strip().splitlines()[0]
        fm = re.search(r"at .+\((.+):(\d+)\)", stderr)
        file_, line_ = (fm.group(1), int(fm.group(2))) if fm else (None, None)
        return DetectedError(
            language=self.LANG,
            error_type=error_type,
            message=message,
            file=file_,
            line=line_,
            raw_output=stderr,
            traceback=stderr,
        )


class _JavaScriptStrategy:
    LANG = "javascript"

    def detect(self, stderr: str, stdout: str) -> Optional[DetectedError]:
        combined = stderr + stdout
        if "Error" not in combined and "TypeError" not in combined:
            return None
        m = re.search(r"(TypeError|ReferenceError|SyntaxError|Error): (.+)", combined)
        error_type = m.group(1) if m else "Error"
        message = m.group(2) if m else combined.strip().splitlines()[0]
        fm = re.search(r"at .+\((.+):(\d+):\d+\)", combined)
        file_, line_ = (fm.group(1), int(fm.group(2))) if fm else (None, None)
        return DetectedError(
            language=self.LANG,
            error_type=error_type,
            message=message,
            file=file_,
            line=line_,
            raw_output=combined,
            traceback=combined,
        )


class _GoStrategy:
    LANG = "go"

    def detect(self, stderr: str, stdout: str) -> Optional[DetectedError]:
        if not stderr and "goroutine" not in stdout:
            return None
        combined = stderr + stdout
        m = re.search(r"([\w/]+\.go):(\d+):", combined)
        file_, line_ = (m.group(1), int(m.group(2))) if m else (None, None)
        first_line = combined.strip().splitlines()[0] if combined.strip() else "Go error"
        return DetectedError(
            language=self.LANG,
            error_type="GoError",
            message=first_line,
            file=file_,
            line=line_,
            raw_output=combined,
            traceback=combined,
        )


class _CStrategy:
    LANG = "c"

    def detect(self, stderr: str, stdout: str) -> Optional[DetectedError]:
        if "error:" not in stderr and "warning:" not in stderr:
            return None
        m = re.search(r"(.+):(\d+):\d+: (error|warning): (.+)", stderr)
        if m:
            return DetectedError(
                language=self.LANG,
                error_type=f"GCC_{m.group(3).capitalize()}",
                message=m.group(4),
                file=m.group(1),
                line=int(m.group(2)),
                raw_output=stderr,
                traceback=stderr,
            )
        return DetectedError(
            language=self.LANG,
            error_type="CompilationError",
            message=stderr.strip().splitlines()[0],
            raw_output=stderr,
            traceback=stderr,
        )


class _CppStrategy(_CStrategy):
    LANG = "cpp"


# ---------------------------------------------------------------------------
# Factory + Dispatcher
# ---------------------------------------------------------------------------

_STRATEGIES = {
    "python": _PythonStrategy(),
    "java": _JavaStrategy(),
    "javascript": _JavaScriptStrategy(),
    "node": _JavaScriptStrategy(),
    "go": _GoStrategy(),
    "c": _CStrategy(),
    "cpp": _CppStrategy(),
    "gcc": _CStrategy(),
    "g++": _CppStrategy(),
}


class ErrorDetector:
    """
    Factory Pattern: returns the correct language detection strategy.
    Detects errors from RunResult output.
    """

    def detect(self, command: str, stdout: str, stderr: str, returncode: int) -> List[DetectedError]:
        """Return a list of detected errors (may be empty if no errors found)."""
        if returncode == 0 and not stderr:
            return []

        lang_key = command.strip().split()[0].lower() if command.strip() else "unknown"
        strategy = _STRATEGIES.get(lang_key)

        errors: List[DetectedError] = []
        if strategy:
            err = strategy.detect(stderr, stdout)
            if err:
                errors.append(err)
        else:
            # Generic fallback
            if stderr or returncode != 0:
                errors.append(
                    DetectedError(
                        language="unknown",
                        error_type="GenericError",
                        message=(stderr or stdout or "Unknown error").strip().splitlines()[0],
                        raw_output=stderr or stdout,
                        traceback=stderr,
                    )
                )

        log.info("Detected %d error(s) for command: %s", len(errors), command)
        return errors
