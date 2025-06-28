# Unit Tests

This directory contains unit tests for individual functions and classes in the WS-5000 forwarder application.

Unit tests should:
- Test individual functions/methods in isolation
- Use mocks for external dependencies (InfluxDB, network calls)
- Be fast to execute (milliseconds)
- Have no external dependencies

## Structure

Unit tests will be added as the application grows. The typical structure would include:
- `test_app_units.py` - Unit tests for app.py functions
- `test_data_parsing.py` - Unit tests for data parsing logic
- `conftest.py` - Shared unit test configuration and fixtures

Currently, the main testing focus is on integration tests that verify the complete workflow.

## Running Unit Tests

```bash
# From project root
uv run python -m pytest tests/unit/ -v

# With coverage
uv run python -m pytest tests/unit/ --cov=app --cov-report=html
```

## Examples

Unit tests typically test things like:
- Data validation and parsing
- Error handling
- Configuration loading
- Individual endpoint logic (mocked)
