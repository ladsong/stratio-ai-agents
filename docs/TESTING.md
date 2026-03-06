# Testing Guide

Comprehensive guide for testing the nanobot backend.

## Quick Start

```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run integration tests only
make test-integration

# Run tests with coverage
make test-cov
```

## Test Structure

```
packages/core/tests/
├── conftest.py           # Pytest fixtures and configuration
├── repositories/         # Repository unit tests
│   ├── test_thread_repo.py
│   ├── test_run_repo.py
│   └── test_knowledge_document_repo.py
├── tools/               # Tool unit tests
│   ├── test_executor.py
│   └── test_logger.py
├── knowledge/           # Knowledge component tests
│   ├── test_chunker.py
│   └── test_embeddings.py
└── integration/         # Integration tests
    ├── test_conversation_flow.py
    └── test_approval_flow.py
```

## Writing Tests

### Unit Tests

Unit tests should be fast, isolated, and test a single component.

**Example: Repository Test**
```python
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
```

**Example: Tool Test**
```python
import pytest
from core.knowledge.chunker import TextChunker

@pytest.mark.unit
def test_chunker_basic(sample_text):
    """Test basic text chunking."""
    chunker = TextChunker(chunk_size=200, overlap=50)
    
    chunks = chunker.chunk(sample_text)
    
    assert len(chunks) > 0
    assert all('content' in chunk for chunk in chunks)
```

### Integration Tests

Integration tests verify complete workflows end-to-end.

**Example: Conversation Flow**
```python
import pytest
from core.repositories.thread_repo import ThreadRepository
from core.repositories.run_repo import RunRepository

@pytest.mark.integration
def test_conversation_flow(db_session):
    """Test complete conversation workflow."""
    # Create thread
    thread_repo = ThreadRepository(db_session)
    thread = thread_repo.create(str(uuid.uuid4()), {})
    
    # Create run
    run_repo = RunRepository(db_session)
    run = run_repo.create(
        str(uuid.uuid4()),
        thread.id,
        "conversation_router",
        {"messages": [{"role": "user", "content": "Hello"}]}
    )
    
    # Verify run created
    assert run.status == "queued"
```

## Fixtures

Common fixtures are defined in `conftest.py`:

- `db_session` - Database session for tests
- `test_thread_id` - Unique thread ID
- `test_run_id` - Unique run ID
- `test_document_id` - Unique document ID
- `sample_text` - Sample text for testing

**Using fixtures:**
```python
def test_example(db_session, test_thread_id, sample_text):
    # Use fixtures in your test
    pass
```

## Running Tests

### All Tests
```bash
make test
```

### Unit Tests Only
```bash
make test-unit
```

### Integration Tests Only
```bash
make test-integration
```

### Specific Test File
```bash
docker compose run --rm migrate pytest packages/core/tests/repositories/test_thread_repo.py
```

### Specific Test Function
```bash
docker compose run --rm migrate pytest packages/core/tests/repositories/test_thread_repo.py::test_create_thread
```

### With Coverage
```bash
make test-cov
```

Coverage report will be generated in `htmlcov/index.html`.

### Watch Mode
```bash
make test-watch
```

Tests will re-run automatically when files change.

## Test Markers

Tests can be marked for selective execution:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow running tests

**Run only unit tests:**
```bash
pytest -m unit
```

**Run everything except slow tests:**
```bash
pytest -m "not slow"
```

## Best Practices

### 1. Test Isolation

Each test should be independent and not rely on other tests.

```python
# Good - isolated test
def test_create_thread(db_session, test_thread_id):
    repo = ThreadRepository(db_session)
    thread = repo.create(test_thread_id, {})
    assert thread.id == test_thread_id

# Bad - depends on previous test
def test_get_thread(db_session):
    # Assumes thread was created in previous test
    thread = repo.get_by_id("some-id")
```

### 2. Descriptive Names

Test names should clearly describe what is being tested.

```python
# Good
def test_create_thread_with_metadata()
def test_get_nonexistent_thread_returns_none()

# Bad
def test_thread()
def test_1()
```

### 3. Arrange-Act-Assert

Structure tests with clear sections:

```python
def test_create_thread(db_session, test_thread_id):
    # Arrange
    repo = ThreadRepository(db_session)
    meta = {"user_id": "test123"}
    
    # Act
    thread = repo.create(test_thread_id, meta)
    
    # Assert
    assert thread.id == test_thread_id
    assert thread.meta["user_id"] == "test123"
```

### 4. Test Both Success and Failure

```python
def test_create_thread_success(db_session, test_thread_id):
    # Test successful creation
    pass

def test_create_thread_with_invalid_data(db_session):
    # Test error handling
    pass
```

### 5. Use Fixtures for Common Setup

```python
@pytest.fixture
def thread_with_runs(db_session):
    """Create a thread with multiple runs."""
    thread = create_thread()
    run1 = create_run(thread.id)
    run2 = create_run(thread.id)
    return thread, [run1, run2]

def test_get_runs_for_thread(thread_with_runs):
    thread, runs = thread_with_runs
    # Test using the fixture
```

## Debugging Tests

### Verbose Output
```bash
pytest -vv
```

### Show Print Statements
```bash
pytest -s
```

### Stop on First Failure
```bash
pytest -x
```

### Drop into Debugger on Failure
```bash
pytest --pdb
```

### Run Last Failed Tests
```bash
pytest --lf
```

## Coverage

### Generate Coverage Report
```bash
make test-cov
```

### View HTML Report
```bash
open htmlcov/index.html
```

### Coverage Goals
- Overall coverage: >80%
- Critical paths: >90%
- New code: 100%

## Continuous Integration

Tests run automatically on:
- Every push to main
- Every pull request
- Scheduled nightly builds

**CI Requirements:**
- All tests must pass
- Coverage must be >80%
- No linting errors
- Code must be formatted

## Troubleshooting

### Database Connection Issues

**Problem:** Tests fail with database connection errors

**Solution:**
```bash
# Ensure database is running
docker compose up -d postgres

# Check database is accessible
docker compose exec postgres psql -U nanobot -d nanobot -c "SELECT 1"
```

### Import Errors

**Problem:** Tests fail with import errors

**Solution:**
```bash
# Ensure core package is installed
docker compose run --rm migrate pip install -e /tmp/core
```

### Slow Tests

**Problem:** Tests take too long to run

**Solution:**
- Mark slow tests with `@pytest.mark.slow`
- Run fast tests during development: `pytest -m "not slow"`
- Optimize database fixtures
- Use mocks for external dependencies

### Flaky Tests

**Problem:** Tests pass sometimes and fail other times

**Solution:**
- Check for race conditions
- Ensure proper test isolation
- Use fixed seeds for random data
- Add retries for network operations

## Examples

### Testing a Repository

```python
import pytest
from core.repositories.knowledge_document_repo import KnowledgeDocumentRepository

@pytest.mark.unit
class TestKnowledgeDocumentRepository:
    def test_create_document(self, db_session, test_document_id):
        repo = KnowledgeDocumentRepository(db_session)
        
        doc = repo.create(
            test_document_id,
            "Test Document",
            "Content here",
            {"source": "test"}
        )
        
        assert doc.id == test_document_id
        assert doc.title == "Test Document"
    
    def test_get_by_id(self, db_session, test_document_id):
        repo = KnowledgeDocumentRepository(db_session)
        repo.create(test_document_id, "Test", "Content", {})
        
        doc = repo.get_by_id(test_document_id)
        
        assert doc is not None
        assert doc.id == test_document_id
```

### Testing a Tool

```python
import pytest
from core.knowledge.chunker import TextChunker

@pytest.mark.unit
class TestTextChunker:
    def test_chunk_long_text(self):
        chunker = TextChunker(chunk_size=100, overlap=20)
        text = "A" * 250
        
        chunks = chunker.chunk(text)
        
        assert len(chunks) > 1
        assert all(len(c['content']) <= 100 for c in chunks)
    
    def test_chunk_empty_text(self):
        chunker = TextChunker()
        
        chunks = chunker.chunk("")
        
        assert len(chunks) == 0
```

### Testing Integration

```python
import pytest
from core.jobs.chunk_document import chunk_document_job

@pytest.mark.integration
def test_document_chunking_workflow(db_session, test_document_id):
    # Create document
    doc_repo = KnowledgeDocumentRepository(db_session)
    doc_repo.create(test_document_id, "Test", "Long content...", {})
    
    # Run chunking job
    result = chunk_document_job(test_document_id, generate_embeddings=True)
    
    # Verify chunks created
    chunk_repo = KnowledgeChunkRepository(db_session)
    chunks = chunk_repo.list_by_document(test_document_id)
    
    assert result['chunks_created'] > 0
    assert len(chunks) > 0
    assert all(c.has_embedding for c in chunks)
```

## Next Steps

1. Write tests for new features
2. Maintain >80% coverage
3. Run tests before committing
4. Review test failures in CI
5. Update tests when refactoring

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [pytest markers](https://docs.pytest.org/en/stable/mark.html)
- [Coverage.py](https://coverage.readthedocs.io/)
