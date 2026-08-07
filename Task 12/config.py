import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

VERSION = "1.0.0"

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
HISTORY_WINDOW = int(os.getenv("HISTORY_WINDOW", "20"))
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "60"))

MOCK = os.getenv("MOCK", "0").lower() in {"1", "true", "yes"}
DEBUG = os.getenv("DEBUG", "0").lower() in {"1", "true", "yes"}

API_KEYS = {k.strip() for k in os.getenv("API_KEYS", "").split(",") if k.strip()}
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
MAX_MESSAGE_CHARS = int(os.getenv("MAX_MESSAGE_CHARS", "4000"))
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]

DB_PATH = Path(os.getenv("DB_PATH", Path(__file__).parent / "chatbot.db"))

DEFAULT_SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "You are a helpful, concise assistant. You remember what the user told you earlier in "
    "this conversation and use it to answer follow-up questions.",
)