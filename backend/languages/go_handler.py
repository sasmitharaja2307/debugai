"""SELFHEAL AI – Go Language Handler"""

import re

_GO_HINTS = {
    "undefined": {
        "hint": "Variable or function not defined. Check imports and spelling.",
        "fix_command": "go get ./...",
        "tags": ["undefined", "compile"],
    },
    "cannot find package": {
        "hint": "Go package not found. Run go get to install.",
        "fix_command": "go get ./...",
        "tags": ["dependency", "module"],
    },
    "index out of range": {
        "hint": "Slice or array index out of bounds. Add length check.",
        "fix_command": "",
        "tags": ["runtime", "bounds"],
    },
    "nil pointer dereference": {
        "hint": "Nil pointer accessed. Add nil guard before dereferencing.",
        "fix_command": "",
        "tags": ["nil", "runtime"],
    },
    "goroutine": {
        "hint": "Goroutine panic detected. Review panic message and add recover().",
        "fix_command": "",
        "tags": ["goroutine", "panic"],
    },
}


class GoHandler:
    LANGUAGE = "go"
    COMMAND_PREFIX = "go"

    def get_hints(self, error_type: str, error_message: str) -> dict:
        for key, hint_data in _GO_HINTS.items():
            if key in error_message.lower():
                return {"language": self.LANGUAGE, "error_type": error_type, **hint_data}
        return {
            "language": self.LANGUAGE,
            "error_type": error_type,
            "hint": "Review the Go panic trace and fix the identified issue.",
            "fix_command": "go mod tidy",
            "tags": ["go"],
        }

    def get_run_command(self, file_path: str) -> str:
        return f"go run {file_path}"

    def get_install_command(self, package: str) -> str:
        return f"go get {package}"
