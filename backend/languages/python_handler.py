"""
SELFHEAL AI – Python Language Handler
Factory Pattern: encapsulates Python-specific debug strategies.
"""

import re
from typing import List

from backend.utils.logger import get_logger

log = get_logger(__name__)

# Map of common Python errors to diagnostic hints
_PYTHON_ERROR_HINTS = {
    "ModuleNotFoundError": {
        "hint": "Install the missing module.",
        "fix_template": "pip install {module}",
        "tags": ["dependency", "import"],
    },
    "ImportError": {
        "hint": "Module exists but cannot be imported. Check version compatibility.",
        "fix_template": "pip install --upgrade {module}",
        "tags": ["dependency", "version"],
    },
    "SyntaxError": {
        "hint": "Python syntax is invalid. Check indentation, brackets, and quotes.",
        "fix_template": "",
        "tags": ["syntax"],
    },
    "IndentationError": {
        "hint": "Inconsistent indentation. Use 4 spaces per level.",
        "fix_template": "",
        "tags": ["syntax", "indentation"],
    },
    "TypeError": {
        "hint": "Wrong type passed to a function or operator.",
        "fix_template": "",
        "tags": ["type", "runtime"],
    },
    "AttributeError": {
        "hint": "Object does not have the accessed attribute. Check the type and spelling.",
        "fix_template": "",
        "tags": ["attribute", "runtime"],
    },
    "KeyError": {
        "hint": "Dictionary key does not exist. Use .get() with a default.",
        "fix_template": "",
        "tags": ["dict", "runtime"],
    },
    "IndexError": {
        "hint": "List index out of range. Add bounds check before accessing.",
        "fix_template": "",
        "tags": ["list", "runtime"],
    },
    "FileNotFoundError": {
        "hint": "The specified file does not exist. Verify the path.",
        "fix_template": "",
        "tags": ["file", "io"],
    },
    "PermissionError": {
        "hint": "Insufficient permissions to access the file or directory.",
        "fix_template": "chmod 644 {file}",
        "tags": ["permissions", "io"],
    },
    "RecursionError": {
        "hint": "Maximum recursion depth exceeded. Add a base case or increase sys.setrecursionlimit.",
        "fix_template": "import sys; sys.setrecursionlimit(2000)",
        "tags": ["recursion", "performance"],
    },
    "MemoryError": {
        "hint": "Out of memory. Optimize data structures or process data in chunks.",
        "fix_template": "",
        "tags": ["memory", "performance"],
    },
    "ZeroDivisionError": {
        "hint": "Division by zero. Add a guard: `if denominator != 0`.",
        "fix_template": "",
        "tags": ["arithmetic", "runtime"],
    },
}


class PythonHandler:
    """Strategy Pattern: Python-specific debug and fix logic."""

    LANGUAGE = "python"
    COMMAND_PREFIX = "python"

    def get_hints(self, error_type: str, error_message: str) -> dict:
        """Return diagnostic hints for a Python error."""
        base = _PYTHON_ERROR_HINTS.get(error_type, {
            "hint": "Review the traceback and fix the identified issue.",
            "fix_template": "",
            "tags": ["python"],
        })

        # Try to extract module name from ModuleNotFoundError
        module = ""
        if error_type in ("ModuleNotFoundError", "ImportError"):
            m = re.search(r"No module named '([^']+)'", error_message)
            if m:
                module = m.group(1).split(".")[0]

        fix_command = base["fix_template"].format(module=module, file="<file>") if module else base["fix_template"]
        return {
            "language": self.LANGUAGE,
            "error_type": error_type,
            "hint": base["hint"],
            "fix_command": fix_command,
            "tags": base["tags"],
        }

    def get_run_command(self, file_path: str) -> str:
        return f"python {file_path}"

    def get_dependency_check_command(self) -> str:
        return "pip check"

    def get_install_command(self, package: str) -> str:
        return f"pip install {package}"
