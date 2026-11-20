import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db import get_db
from app.main import app

# Tests use a separate database (created by docker/postgres-init) so dev data is never touched.
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://autoguardian:autoguardian@localhost:5433/autoguardian_test",
)

BACKEND_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    """Build the test schema with the real migrations (so migrations are tested too)."""
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.downgrade(cfg, "base")  # start clean even if a previous run was interrupted
    command.upgrade(cfg, "head")

    test_engine = create_engine(TEST_DATABASE_URL)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    """A session whose changes are rolled back after each test."""
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        try:
            yield session
        finally:
            session.close()
            transaction.rollback()


def _client_for(db: Session) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    """API client using the rolled-back test session. Has its own cookie jar."""
    with _client_for(db) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def other_client(db: Session, client: TestClient) -> Iterator[TestClient]:
    """A second browser (separate cookies), for testing that users can't see each other's data."""
    with _client_for(db) as test_client:
        yield test_client
