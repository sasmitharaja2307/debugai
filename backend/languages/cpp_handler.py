"""POLYHEAL AI – C++ Language Handler (extends C Handler)"""

from backend.languages.c_handler import CHandler


class CppHandler(CHandler):
    LANGUAGE = "cpp"
    COMMAND_PREFIX = "g++"

    def get_hints(self, error_type: str, error_message: str) -> dict:
        hints = super().get_hints(error_type, error_message)
        hints["language"] = self.LANGUAGE
        msg_lower = error_message.lower()
        if "std::" in error_message or "no member named" in msg_lower:
            hints["hint"] = "C++ STL error. Check std namespace usage and include headers like <vector>, <string>."
            hints["tags"] = ["stl", "cpp", "template"]
        if "template" in msg_lower:
            hints["hint"] = "Template instantiation error. Verify template parameters and specializations."
            hints["tags"] = ["template", "cpp"]
        return hints

    def get_compile_command(self, file_path: str, output: str = "a.out") -> str:
        return f"g++ -std=c++17 -Wall -Wextra -o {output} {file_path}"
