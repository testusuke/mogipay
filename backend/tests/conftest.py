"""Test configuration and fixtures for MogiPay backend tests."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from app.database import Base


@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container for tests."""
    with PostgresContainer("postgres:16") as postgres:
        yield postgres


@pytest.fixture
def db_session(postgres_container):
    """Create a fresh database session for each test."""
    engine = create_engine(postgres_container.get_connection_url())
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def mock_current_user():
    """Create a mock authenticated user for testing.

    Returns a function that can be used to override the get_current_user dependency.
    """

    def override_get_current_user() -> dict:
        """Return a mock user payload for testing."""
        return {
            "sub": "test_user",
            "exp": 9999999999,  # Far future expiration
        }

    return override_get_current_user
