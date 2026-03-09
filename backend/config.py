"""
Debug AI – Configuration
Reads settings from environment variables / .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Always load from the project root .env, overriding any system env vars
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

class Config:
    # Server
    HOST  = os.getenv("HOST", "0.0.0.0")
    PORT  = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    MODEL          = os.getenv("MODEL", "gpt-4o-mini")

    # CORS
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")

    # Supported languages
    SUPPORTED_LANGUAGES = [
        "python", "javascript", "java",
        "c", "cpp", "go", "typescript",
        "rust", "ruby", "php",
    ]
