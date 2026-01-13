import os
from typing import Final

API_BASE_URL: Final[str] = os.getenv("MODEL_TESTER_API_URL", "http://localhost:8317/v1")
TIMEOUT_SECONDS: Final[int] = int(os.getenv("MODEL_TESTER_TIMEOUT", "30"))
MAX_WORKERS: Final[int] = int(os.getenv("MODEL_TESTER_MAX_WORKERS", "5"))
MAX_RETRIES: Final[int] = 2
RETRY_DELAY: Final[float] = 1.0

DB_HOST: Final[str] = os.getenv("MODEL_TESTER_DB_HOST", "localhost")
DB_PORT: Final[int] = int(os.getenv("MODEL_TESTER_DB_PORT", "5432"))
DB_NAME: Final[str] = os.getenv("MODEL_TESTER_DB_NAME", "agentzero")
DB_USER: Final[str] = os.getenv("MODEL_TESTER_DB_USER", "agentzero")
DB_PASSWORD: Final[str] = os.getenv("MODEL_TESTER_DB_PASSWORD", "")

DELAY_BETWEEN_TESTS: Final[float] = 0.0
STREAM_CHUNK_SIZE: Final[int] = 512

OUTPUT_DIR: Final[str] = "output"

RECOMMENDATION_THRESHOLDS: Final[dict[str, int]] = {
    "recommended": 90,
    "partial": 50,
    "no_tool_calling": 0,
}

AUTONOMOUS_AGENT_WEIGHTS: Final[dict[str, float]] = {
    "basic_tool_calling": 0.25,
    "tool_output_reasoning": 0.35,
    "multi_tool_calling": 0.25,
    "json_mode": 0.10,
    "streaming_tool_calls": 0.05,
}
