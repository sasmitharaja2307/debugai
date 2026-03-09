"""POLYHEAL AI – Java Language Handler"""

import re
from backend.utils.logger import get_logger

log = get_logger(__name__)

_JAVA_HINTS = {
    "NullPointerException": {
        "hint": "A variable is null when an operation is attempted. Add null checks.",
        "fix_command": "",
        "tags": ["null", "runtime"],
    },
    "ClassNotFoundException": {
        "hint": "Class not on classpath. Add the dependency to pom.xml or build.gradle.",
        "fix_command": "mvn install",
        "tags": ["dependency", "classpath"],
    },
    "ArrayIndexOutOfBoundsException": {
        "hint": "Array access out of bounds. Verify index against array.length.",
        "fix_command": "",
        "tags": ["array", "runtime"],
    },
    "StackOverflowError": {
        "hint": "Infinite or excessive recursion. Add base case.",
        "fix_command": "",
        "tags": ["recursion", "stack"],
    },
    "OutOfMemoryError": {
        "hint": "Heap space exhausted. Increase JVM heap: java -Xmx512m",
        "fix_command": "",
        "tags": ["memory", "jvm"],
    },
    "NumberFormatException": {
        "hint": "Invalid string-to-number conversion. Validate input before parsing.",
        "fix_command": "",
        "tags": ["parsing", "runtime"],
    },
}


class JavaHandler:
    LANGUAGE = "java"
    COMMAND_PREFIX = "java"

    def get_hints(self, error_type: str, error_message: str) -> dict:
        short_type = error_type.split(".")[-1]
        base = _JAVA_HINTS.get(short_type, {
            "hint": "Review the Java stack trace and fix the identified exception.",
            "fix_command": "",
            "tags": ["java"],
        })
        return {
            "language": self.LANGUAGE,
            "error_type": error_type,
            **base,
        }

    def get_run_command(self, class_name: str) -> str:
        return f"java {class_name}"

    def get_compile_command(self, file_path: str) -> str:
        return f"javac {file_path}"

    def get_install_command(self, artifact: str) -> str:
        return f"mvn dependency:get -Dartifact={artifact}"
