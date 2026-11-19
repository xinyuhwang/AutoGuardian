from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.config import CORS_ORIGINS
from app.routers.vehicles import router as vehicles_router

app = FastAPI(title="AutoGuardian API", version="0.1.0")

# Frontend origins allowed to call the API (comma-separated CORS_ORIGINS env var).
# allow_credentials lets the browser send the session cookie on cross-origin requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(vehicles_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
