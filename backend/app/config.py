import os
from pathlib import Path

# Defaults match docker-compose.yml for local development.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://autoguardian:autoguardian@localhost:5433/autoguardian",
)

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

# Uploaded documents (git-ignored). Relative paths are relative to the backend/ folder.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = (_BACKEND_DIR / os.getenv("UPLOAD_DIR", "uploads")).resolve()
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "20")) * 1024 * 1024  # per file
MAX_FILES_PER_DOCUMENT = 20

# Session cookie. SESSION_COOKIE_SECURE must be "true" in production (HTTPS only).
SESSION_COOKIE_NAME = "ag_session"
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
SESSION_LIFETIME_DAYS = int(os.getenv("SESSION_LIFETIME_DAYS", "30"))
