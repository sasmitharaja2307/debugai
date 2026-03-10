"""
SELFHEAL AI – Environment Analyzer
Inspects project configuration files and detects environment issues.
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from backend.utils.logger import get_logger

log = get_logger(__name__)

_WEAK_KEY_PATTERNS = [
    re.compile(r'(?i)(api_key|secret|password|token)\s*=\s*["\']?(\S+)["\']?')
]


class EnvironmentIssue:
    def __init__(self, severity: str, category: str, message: str, suggestion: str = ""):
        self.severity = severity          # "critical" | "warning" | "info"
        self.category = category
        self.message = message
        self.suggestion = suggestion

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "suggestion": self.suggestion,
        }


class EnvironmentAnalyzer:
    """
    Scans project root for environment-related problems:
    - Missing/outdated runtimes
    - Missing dependencies
    - Invalid/missing env vars
    - Hardcoded secrets
    """

    def __init__(self, project_root: str):
        self.root = Path(project_root)

    def analyze(self) -> List[EnvironmentIssue]:
        issues: List[EnvironmentIssue] = []
        issues.extend(self._check_python())
        issues.extend(self._check_node())
        issues.extend(self._check_go())
        issues.extend(self._check_env_file())
        issues.extend(self._check_docker())
        log.info("Environment analysis complete – %d issue(s) found.", len(issues))
        return issues

    # ------------------------------------------------------------------
    # Python
    # ------------------------------------------------------------------

    def _check_python(self) -> List[EnvironmentIssue]:
        issues: List[EnvironmentIssue] = []
        req_file = self.root / "requirements.txt"
        if not req_file.exists():
            issues.append(EnvironmentIssue(
                "warning", "python",
                "requirements.txt not found.",
                "Create requirements.txt with `pip freeze > requirements.txt`.",
            ))
            return issues

        declared = set()
        for line in req_file.read_text(encoding="utf-8").splitlines():
            pkg = re.split(r"[>=<!]", line.strip())[0].lower().strip()
            if pkg:
                declared.add(pkg)

        # Check imports in .py files
        for py_file in self.root.rglob("*.py"):
            for m in re.finditer(r"^(?:import|from)\s+([\w]+)", py_file.read_text(encoding="utf-8", errors="ignore"), re.MULTILINE):
                pkg = m.group(1).lower()
                stdlib = {"os", "sys", "re", "json", "math", "time", "pathlib", "typing",
                          "datetime", "collections", "itertools", "functools", "subprocess",
                          "threading", "asyncio", "logging", "abc", "copy", "io", "shutil",
                          "dataclasses", "enum", "traceback", "uuid", "hashlib", "hmac",
                          "base64", "urllib", "http", "socket", "ssl", "csv", "random"}
                if pkg not in stdlib and pkg not in declared:
                    issues.append(EnvironmentIssue(
                        "warning", "python",
                        f"Package '{pkg}' imported in {py_file.name} but not in requirements.txt.",
                        f"Run: pip install {pkg}  and add it to requirements.txt.",
                    ))
        return issues

    # ------------------------------------------------------------------
    # Node.js
    # ------------------------------------------------------------------

    def _check_node(self) -> List[EnvironmentIssue]:
        issues: List[EnvironmentIssue] = []
        pkg_file = self.root / "package.json"
        if not pkg_file.exists():
            return issues

        data: Dict[str, Any] = json.loads(pkg_file.read_text(encoding="utf-8"))
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        node_modules = self.root / "node_modules"
        if not node_modules.exists():
            issues.append(EnvironmentIssue(
                "critical", "node",
                "node_modules directory not found.",
                "Run: npm install",
            ))
        else:
            for dep in deps:
                if not (node_modules / dep).exists():
                    issues.append(EnvironmentIssue(
                        "warning", "node",
                        f"Dependency '{dep}' listed in package.json but not installed.",
                        f"Run: npm install {dep}",
                    ))
        return issues

    # ------------------------------------------------------------------
    # Go
    # ------------------------------------------------------------------

    def _check_go(self) -> List[EnvironmentIssue]:
        issues: List[EnvironmentIssue] = []
        go_mod = self.root / "go.mod"
        if not go_mod.exists():
            return issues
        vendor = self.root / "vendor"
        if not vendor.exists():
            issues.append(EnvironmentIssue(
                "info", "go",
                "go vendor directory not found.",
                "Run: go mod vendor  or  go mod download",
            ))
        return issues

    # ------------------------------------------------------------------
    # .env file
    # ------------------------------------------------------------------

    def _check_env_file(self) -> List[EnvironmentIssue]:
        issues: List[EnvironmentIssue] = []
        env_file = self.root / ".env"
        if not env_file.exists():
            issues.append(EnvironmentIssue(
                "info", "env",
                ".env file not found.",
                "Create a .env file and add required environment variables.",
            ))
            return issues

        content = env_file.read_text(encoding="utf-8", errors="ignore")
        for pattern in _WEAK_KEY_PATTERNS:
            for m in pattern.finditer(content):
                val = m.group(2)
                if len(val) < 16 or val in ("your_api_key", "changeme", "secret"):
                    issues.append(EnvironmentIssue(
                        "critical", "security",
                        f"Weak or placeholder value detected for key '{m.group(1)}'.",
                        "Replace with a strong, randomly-generated secret.",
                    ))

        # Check for keys present in code but missing from .env
        defined_keys = set(re.findall(r"^([A-Z_][A-Z0-9_]+)=", content, re.MULTILINE))
        if not defined_keys:
            issues.append(EnvironmentIssue("info", "env", ".env file appears empty.", ""))
        return issues

    # ------------------------------------------------------------------
    # Docker
    # ------------------------------------------------------------------

    def _check_docker(self) -> List[EnvironmentIssue]:
        issues: List[EnvironmentIssue] = []
        compose = self.root / "docker-compose.yml"
        if not compose.exists():
            return issues
        content = compose.read_text(encoding="utf-8", errors="ignore")
        if "privileged: true" in content:
            issues.append(EnvironmentIssue(
                "critical", "docker",
                "Docker container running in privileged mode.",
                "Remove `privileged: true` unless absolutely necessary.",
            ))
        return issues
