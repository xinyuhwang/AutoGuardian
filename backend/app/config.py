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
