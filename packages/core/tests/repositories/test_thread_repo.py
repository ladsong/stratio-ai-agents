"""Tests for ThreadRepository."""
import pytest
from core.repositories.thread_repo import ThreadRepository


@pytest.mark.unit
def test_create_thread(db_session, test_thread_id):
    """Test creating a thread."""
    repo = ThreadRepository(db_session)
    
    thread = repo.create(test_thread_id, {"user_id": "test123"})
    
    assert thread.id == test_thread_id
    assert thread.meta["user_id"] == "test123"
    assert thread.created_at is not None
    assert thread.updated_at is not None


@pytest.mark.unit
def test_get_thread_by_id(db_session, test_thread_id):
    """Test retrieving a thread by ID."""
    repo = ThreadRepository(db_session)
    
    # Create thread
    repo.create(test_thread_id, {"user_id": "test123"})
    
    # Retrieve thread
    thread = repo.get_by_id(test_thread_id)
    
    assert thread is not None
    assert thread.id == test_thread_id
    assert thread.meta["user_id"] == "test123"


@pytest.mark.unit
def test_get_nonexistent_thread(db_session):
    """Test retrieving a thread that doesn't exist."""
    repo = ThreadRepository(db_session)
    
    thread = repo.get_by_id("nonexistent-id")
    
    assert thread is None
