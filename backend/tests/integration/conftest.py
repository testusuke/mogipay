"""Integration test fixtures with real database and FastAPI app."""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from app.database import Base, get_db

# Import all models to register them with Base
from app.models.product import Product
from app.models.set_item import SetItem
from app.models.sales_history import SalesHistory
from app.models.sale_item import SaleItem


@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container for integration tests."""
    with PostgresContainer("postgres:16") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def app_with_db(postgres_container):
    """Create FastAPI app connected to test database."""
    # Set database URL environment variable
    db_url = postgres_container.get_connection_url()
    os.environ["DATABASE_URL"] = db_url

    # Create database engine and tables
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

    # Create session factory
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Override get_db dependency
    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Override authentication for testing
    def override_get_current_user():
        """Return a mock user payload for testing."""
        return {
            "sub": "test_user",
            "exp": 9999999999,  # Far future expiration
        }

    # Import app and override dependency
    from app.main import app
    from app.dependencies.auth import get_current_user

    # Clear any existing overrides from other tests
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield app

    # Cleanup
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()
    del os.environ["DATABASE_URL"]


@pytest.fixture
def client(app_with_db):
    """Create test client with real database."""
    return TestClient(app_with_db)


@pytest.fixture(autouse=True)
def cleanup_db(app_with_db, postgres_container):
    """Clean up database between tests."""
    yield

    # Clean all tables after each test
    engine = create_engine(postgres_container.get_connection_url())
    with engine.begin() as conn:
        # Delete in correct order to avoid foreign key constraints
        from app.models.sale_item import SaleItem
        from app.models.sales_history import SalesHistory
        from app.models.set_item import SetItem
        from app.models.product import Product

        conn.execute(SaleItem.__table__.delete())
        conn.execute(SalesHistory.__table__.delete())
        conn.execute(SetItem.__table__.delete())
        conn.execute(Product.__table__.delete())
    engine.dispose()
