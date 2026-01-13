# Tests for Notion KB Manager

Comprehensive test suite for Phase 5 background task processing and the entire Notion KB Manager application.

## Test Structure

```
tests/
├── unit/                                      # Unit tests
│   ├── test_workers.py                        # Worker function tests
│   └── test_background_task_service.py        # Background task service tests
├── integration/                               # Integration tests
│   └── test_async_workflow.py                 # Full async workflow tests
└── README.md                                  # This file
```

## Prerequisites

1. **Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Test dependencies** (already in requirements.txt):
   - `pytest` - Test framework
   - `fakeredis` - Mock Redis for testing without real Redis server

## Running Tests

### Run All Tests

```bash
# From project root
python3 -m pytest tests/ -v

# With coverage
python3 -m pytest tests/ -v --cov=app --cov-report=html
```

### Run Specific Test Suites

```bash
# Unit tests only
python3 -m pytest tests/unit/ -v

# Integration tests only
python3 -m pytest tests/integration/ -v

# Specific test file
python3 -m pytest tests/unit/test_workers.py -v

# Specific test class
python3 -m pytest tests/unit/test_workers.py::TestParsingWorker -v

# Specific test function
python3 -m pytest tests/unit/test_workers.py::TestParsingWorker::test_parse_content_job_success -v
```

### Run with Output

```bash
# Show print statements
python3 -m pytest tests/ -v -s

# Show detailed output
python3 -m pytest tests/ -v --tb=short

# Stop on first failure
python3 -m pytest tests/ -v -x
```

## Test Coverage

### Unit Tests (`tests/unit/`)

**test_workers.py** - 15 tests covering:
- ✅ Parsing worker job execution (success, failure, exception)
- ✅ Batch parsing job dispatching
- ✅ AI processing worker job execution
- ✅ Batch AI processing job dispatching
- ✅ Notion import worker job execution
- ✅ Worker configuration validation

**test_background_task_service.py** - 25 tests covering:
- ✅ Task creation (ProcessingTask, ImportNotionTask)
- ✅ Task item creation and management
- ✅ Item status updates (pending → running → completed/failed)
- ✅ Progress tracking and calculation
- ✅ Task status retrieval
- ✅ Task cancellation
- ✅ Failed item retry
- ✅ Job enqueuing

### Integration Tests (`tests/integration/`)

**test_async_workflow.py** - 30+ tests covering:
- ✅ Async parsing workflow (batch and single)
- ✅ Async AI processing workflow (batch and single)
- ✅ Async Notion import workflow (batch and single)
- ✅ Task status checking (with and without items)
- ✅ Task cancellation
- ✅ Failed item retry
- ✅ Monitoring endpoints (workers, queues, statistics, health)
- ✅ Input validation and error handling
- ✅ End-to-end workflows

**Total:** 70+ comprehensive tests

## Test Categories

### 1. Worker Tests

Test individual worker functions for parsing, AI processing, and Notion imports.

**Example:**
```python
def test_parse_content_job_success(self, app):
    """Test successful parsing job"""
    # Creates mock link, task, and task item
    # Mocks parsing service
    # Executes parse_content_job
    # Verifies result and task item status
```

### 2. Background Task Service Tests

Test the BackgroundTaskService methods for task lifecycle management.

**Example:**
```python
def test_update_task_progress_partial_complete(self, app, service):
    """Test progress with some items completed"""
    # Creates task with multiple items
    # Marks some as completed
    # Updates progress
    # Verifies progress calculation (50% = 2/4 items)
```

### 3. API Integration Tests

Test API endpoints end-to-end with database and mocked Redis.

**Example:**
```python
def test_parse_batch_async_creates_task(self, client, app, fake_redis, sample_links):
    """Test that batch parsing creates a task"""
    # POSTs to /api/parsing/async/batch
    # Verifies 202 response with task_id
    # Checks task was created in database
```

### 4. Monitoring Tests

Test monitoring endpoints for worker health, queue stats, and system health.

**Example:**
```python
def test_get_health(self, client, app, fake_redis):
    """Test getting system health"""
    # GETs /api/monitoring/health
    # Verifies health status includes Redis, workers, queues
```

## Fixtures

### Common Fixtures

- **`app`** - Test Flask app with in-memory SQLite database
- **`client`** - Test client for making HTTP requests
- **`fake_redis`** - FakeRedis instance (no real Redis needed)
- **`service`** - BackgroundTaskService instance with mocked Redis

### Data Fixtures

- **`sample_links`** - 5 sample Link objects
- **`sample_parsed_contents`** - 3 sample ParsedContent objects
- **`sample_ai_contents`** - 2 sample AIProcessedContent objects

## Mocking Strategy

### Why Mocking?

Tests run **without** requiring:
- ❌ Real Redis server
- ❌ External API calls (OpenAI, Notion)
- ❌ Network access
- ❌ Running workers

### What's Mocked

1. **Redis** - FakeRedis (in-memory)
2. **RQ Jobs** - MagicMock objects
3. **Service Methods** - Mocked to return predictable results
   - `ContentParsingService.fetch_and_parse()`
   - `AIProcessingService.process_content()`
   - `NotionImportService.import_to_notion()`

### Example Mock

```python
with patch('app.workers.parsing_worker.get_content_parsing_service') as mock_service:
    mock_parsing_service = MagicMock()
    mock_parsing_service.fetch_and_parse.return_value = {
        'success': True,
        'parsed_content_id': 1
    }
    mock_service.return_value = mock_parsing_service

    # Now parse_content_job will use mocked service
    result = parse_content_job(task_id, link_id)
```

## Writing New Tests

### Unit Test Template

```python
def test_my_new_feature(self, app):
    """Test description"""
    with app.app_context():
        # Setup
        # ... create test data

        # Execute
        result = my_function()

        # Verify
        assert result is not None
        assert result['success'] is True
```

### Integration Test Template

```python
def test_my_new_endpoint(self, client, app, fake_redis):
    """Test description"""
    with app.app_context():
        # Setup
        # ... create test data

        # Execute
        response = client.post('/api/my/endpoint', json={'data': 'test'})

        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
```

## Continuous Integration

### GitHub Actions (Example)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python3 -m pytest tests/ -v --cov=app
```

## Troubleshooting

### Tests Fail with "No module named 'app'"

```bash
# Run from project root
cd /path/to/notion-kb-manager
python3 -m pytest tests/ -v
```

### Tests Fail with Import Errors

```bash
# Ensure all dependencies are installed
pip install -r requirements.txt
```

### Tests Hang or Timeout

```bash
# Check for unmocked Redis/Queue calls
# Ensure all external services are mocked
```

### Database Lock Errors

```bash
# Tests use in-memory SQLite, but if issues persist:
# Add --forked to run tests in separate processes
python3 -m pytest tests/ -v --forked
```

## Performance

**Typical test run times:**
- Unit tests: ~2-3 seconds
- Integration tests: ~5-8 seconds
- Full suite: ~10-15 seconds

**Why so fast?**
- In-memory database (no disk I/O)
- FakeRedis (no network calls)
- Mocked external services (no HTTP requests)

## Test Quality Metrics

### Coverage Goals

- **Target:** 80%+ code coverage
- **Critical paths:** 100% coverage
  - Worker job functions
  - Task lifecycle (create, update, complete, fail, retry)
  - API endpoints

### Run Coverage Report

```bash
# Generate HTML coverage report
python3 -m pytest tests/ --cov=app --cov-report=html

# Open report
open htmlcov/index.html
```

## Best Practices

1. **One assertion per concept** - Test one thing at a time
2. **Clear test names** - Describe what is being tested
3. **AAA pattern** - Arrange, Act, Assert
4. **Mock external dependencies** - Keep tests fast and isolated
5. **Clean up after tests** - Use fixtures and teardown
6. **Test edge cases** - Empty inputs, max retries, not found, etc.

## Adding Tests for New Features

When adding new features:

1. **Write unit tests first** - Test individual functions
2. **Add integration tests** - Test API endpoints end-to-end
3. **Run full suite** - Ensure no regressions
4. **Check coverage** - Aim for 80%+ coverage of new code

## Summary

This test suite provides comprehensive coverage of Phase 5 background task processing:

✅ **70+ tests** covering all critical paths
✅ **Fast execution** (~10-15 seconds for full suite)
✅ **No external dependencies** (Redis, APIs mocked)
✅ **Easy to run** (`python3 -m pytest tests/ -v`)
✅ **High coverage** of workers, services, and API endpoints

All tests pass successfully and validate the correctness of the async workflow implementation.
