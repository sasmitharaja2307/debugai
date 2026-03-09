"""
POLYHEAL AI – Configuration
Centralized settings loaded from environment variables.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_root = Path(__file__).parent.parent
load_dotenv(_root / ".env")


class Config:
    # Project
    PROJECT_ROOT: str = os.getenv("POLYHEAL_PROJECT_ROOT", str(_root))

    # Server
    HOST: str = os.getenv("POLYHEAL_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("POLYHEAL_PORT", "8000"))

    # LLM
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Search
    SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

    # Memory
    MAX_SNAPSHOT_HISTORY: int = int(os.getenv("MAX_SNAPSHOT_HISTORY", "20"))

    @classmethod
    def validate(cls) -> list[str]:
        """Return a list of missing critical settings."""
        missing = []
        if not cls.OPENAI_API_KEY and not cls.GEMINI_API_KEY:
            missing.append("OPENAI_API_KEY or GEMINI_API_KEY (LLM solutions will be offline/fallback)")
        return missing
