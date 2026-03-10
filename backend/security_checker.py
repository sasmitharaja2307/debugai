"""
SELFHEAL AI – Security Checker
Evaluates proposed fixes for security vulnerabilities.
"""

import re
from dataclasses import dataclass, field
from typing import List

from backend.utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class SecurityAlert:
    severity: str        # "critical" | "high" | "medium" | "low"
    category: str
    description: str
    recommendation: str
    line_match: str = ""

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "category": self.category,
            "description": self.description,
            "recommendation": self.recommendation,
            "line_match": self.line_match,
        }


@dataclass
class SecurityReport:
    is_safe: bool
    security_score: int          # 0-100
    alerts: List[SecurityAlert] = field(default_factory=list)
    password_strength: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "is_safe": self.is_safe,
            "security_score": self.security_score,
            "alerts": [a.to_dict() for a in self.alerts],
            "password_strength": self.password_strength,
        }


_RULES = [
    # Permissions
    (r"chmod\s+777", "critical", "permissions",
     "chmod 777 grants full read/write/execute to everyone.",
     "Use least-privilege permissions (e.g., chmod 644 or 755)."),
    # SSL
    (r"verify\s*=\s*False|VERIFY_SSL\s*=\s*False|ssl_verify\s*=\s*False",
     "critical", "ssl",
     "SSL verification is disabled, exposing connections to MITM attacks.",
     "Always keep SSL verification enabled."),
    # Hardcoded secrets
    (r'(?i)(api_key|secret|password|token)\s*=\s*["\'][^"\']{4,}["\']',
     "high", "secrets",
     "Hardcoded secret value detected in code.",
     "Use environment variables or a secrets manager instead."),
    # SQL injection
    (r'(?i)(execute|cursor\.execute)\s*\(\s*["\'].*%s.*["\']',
     "high", "sql_injection",
     "Potential SQL injection via string formatting.",
     "Use parameterized queries / ORM."),
    # eval / exec
    (r"\beval\s*\(|\bexec\s*\(",
     "high", "code_injection",
     "Use of eval/exec can lead to arbitrary code execution.",
     "Avoid eval/exec; use safe alternatives."),
    # Weak hash
    (r"\bmd5\b|\bsha1\b",
     "medium", "weak_hash",
     "MD5/SHA1 are considered cryptographically weak.",
     "Use SHA-256 or stronger algorithms."),
    # Debug mode
    (r"DEBUG\s*=\s*True|debug\s*=\s*true",
     "medium", "debug_mode",
     "Debug mode enabled in production code.",
     "Disable debug mode before deploying."),
    # Open redirect / CORS wildcard
    (r'Access-Control-Allow-Origin.*\*',
     "medium", "cors",
     "CORS wildcard origin allows any domain.",
     "Restrict CORS to specific trusted origins."),
]


class SecurityChecker:
    """
    Scans a code snippet or shell command for security vulnerabilities.
    Also validates password strength.
    """

    def check(self, code: str) -> SecurityReport:
        alerts: List[SecurityAlert] = []
        for pattern, severity, category, desc, rec in _RULES:
            for m in re.finditer(pattern, code, re.IGNORECASE):
                alerts.append(SecurityAlert(
                    severity=severity,
                    category=category,
                    description=desc,
                    recommendation=rec,
                    line_match=m.group(0)[:120],
                ))

        # Deduplicate by category
        seen: set = set()
        unique: List[SecurityAlert] = []
        for a in alerts:
            if a.category not in seen:
                seen.add(a.category)
                unique.append(a)

        score = 100
        for a in unique:
            deductions = {"critical": 30, "high": 20, "medium": 10, "low": 5}
            score -= deductions.get(a.severity, 0)
        score = max(0, score)

        return SecurityReport(
            is_safe=score >= 70,
            security_score=score,
            alerts=unique,
        )

    # ------------------------------------------------------------------
    # Password Strength Validator
    # ------------------------------------------------------------------

    def validate_password(self, password: str) -> dict:
        result = {
            "score": 0,
            "length": len(password),
            "has_uppercase": bool(re.search(r"[A-Z]", password)),
            "has_lowercase": bool(re.search(r"[a-z]", password)),
            "has_digits": bool(re.search(r"\d", password)),
            "has_special": bool(re.search(r"[^a-zA-Z0-9]", password)),
            "strength": "weak",
        }
        score = sum([
            result["has_uppercase"],
            result["has_lowercase"],
            result["has_digits"],
            result["has_special"],
            len(password) >= 12,
            len(password) >= 16,
        ])
        result["score"] = score
        result["strength"] = (
            "very_strong" if score >= 5
            else "strong" if score == 4
            else "moderate" if score == 3
            else "weak"
        )
        return result
