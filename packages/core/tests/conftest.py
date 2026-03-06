"""Pytest configuration and fixtures for core tests."""
import os
import uuid
from typing import Generator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture(scope="session")
def database_url() -> str:
    """Get test database URL."""
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://nanobot:nanobot@localhost:5432/nanobot"
    )


@pytest.fixture(scope="session")
def engine(database_url):
    """Create database engine for tests."""
    return create_engine(database_url, pool_pre_ping=True)


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    """Create a database session for a test."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def test_thread_id() -> str:
    """Generate a unique thread ID for testing."""
    return str(uuid.uuid4())


@pytest.fixture
def test_run_id() -> str:
    """Generate a unique run ID for testing."""
    return str(uuid.uuid4())


@pytest.fixture
def test_document_id() -> str:
    """Generate a unique document ID for testing."""
    return str(uuid.uuid4())


@pytest.fixture
def sample_text() -> str:
    """Sample text for testing."""
    return """
    Artificial intelligence is transforming how we work and live. Machine learning algorithms 
    can now process vast amounts of data to identify patterns and make predictions. Deep learning, 
    a subset of machine learning, uses neural networks with multiple layers to learn complex 
    representations. Natural language processing enables computers to understand and generate 
    human language.
    """
