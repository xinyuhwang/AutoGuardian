import os

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

# Session cookie. SESSION_COOKIE_SECURE must be "true" in production (HTTPS only).
SESSION_COOKIE_NAME = "ag_session"
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
SESSION_LIFETIME_DAYS = int(os.getenv("SESSION_LIFETIME_DAYS", "30"))
