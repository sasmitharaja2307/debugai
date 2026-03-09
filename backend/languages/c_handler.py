"""POLYHEAL AI – C Language Handler"""


class CHandler:
    LANGUAGE = "c"
    COMMAND_PREFIX = "gcc"

    def get_hints(self, error_type: str, error_message: str) -> dict:
        msg_lower = error_message.lower()
        if "undeclared" in msg_lower or "implicit" in msg_lower:
            return {
                "language": self.LANGUAGE, "error_type": error_type,
                "hint": "Symbol not declared. Add the correct header file #include.",
                "fix_command": "", "tags": ["declaration", "header"],
            }
        if "undefined reference" in msg_lower:
            return {
                "language": self.LANGUAGE, "error_type": error_type,
                "hint": "Linker error: symbol not found. Add the library with -l flag.",
                "fix_command": "", "tags": ["linker", "library"],
            }
        if "segmentation fault" in msg_lower:
            return {
                "language": self.LANGUAGE, "error_type": error_type,
                "hint": "Segmentation fault: illegal memory access. Check pointers and array bounds.",
                "fix_command": "", "tags": ["memory", "pointer"],
            }
        return {
            "language": self.LANGUAGE, "error_type": error_type,
            "hint": "Review GCC error output. Fix syntax or include missing headers.",
            "fix_command": "", "tags": ["c", "compile"],
        }

    def get_compile_command(self, file_path: str, output: str = "a.out") -> str:
        return f"gcc -Wall -Wextra -o {output} {file_path}"

    def get_run_command(self, binary: str = "./a.out") -> str:
        return binary
