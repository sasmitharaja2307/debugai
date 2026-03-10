"""SELFHEAL AI – JavaScript / Node.js Language Handler"""

import re

_JS_HINTS = {
    "TypeError": {
        "hint": "Wrong type used. Check variable types and API usage.",
        "fix_command": "",
        "tags": ["type", "runtime"],
    },
    "ReferenceError": {
        "hint": "Variable not defined. Check scoping and spelling.",
        "fix_command": "",
        "tags": ["scope", "runtime"],
    },
    "SyntaxError": {
        "hint": "JavaScript syntax error. Check brackets, semicolons, and arrow functions.",
        "fix_command": "",
        "tags": ["syntax"],
    },
    "MODULE_NOT_FOUND": {
        "hint": "npm module not installed.",
        "fix_command": "npm install",
        "tags": ["dependency"],
    },
    "ECONNREFUSED": {
        "hint": "Connection refused. Ensure the target service is running.",
        "fix_command": "",
        "tags": ["network"],
    },
}


class JavaScriptHandler:
    LANGUAGE = "javascript"
    COMMAND_PREFIX = "node"

    def get_hints(self, error_type: str, error_message: str) -> dict:
        # Check for module not found pattern
        if "Cannot find module" in error_message or "MODULE_NOT_FOUND" in error_type:
            m = re.search(r"Cannot find module '([^']+)'", error_message)
            pkg = m.group(1) if m else ""
            return {
                "language": self.LANGUAGE,
                "error_type": "MODULE_NOT_FOUND",
                "hint": f"Package '{pkg}' not installed.",
                "fix_command": f"npm install {pkg}" if pkg else "npm install",
                "tags": ["dependency", "npm"],
            }
        base = _JS_HINTS.get(error_type, {
            "hint": "Review the Node.js stack trace.",
            "fix_command": "",
            "tags": ["javascript"],
        })
        return {"language": self.LANGUAGE, "error_type": error_type, **base}

    def get_run_command(self, file_path: str) -> str:
        return f"node {file_path}"

    def get_install_command(self, package: str) -> str:
        return f"npm install {package}"
