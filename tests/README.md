# Tests

This directory contains tests for the WS-5000 forwarder application, organized by test type.

## Directory Structure

- `unit/` - Unit tests for individual functions and classes
- `integration/` - Integration tests with real external services
- `acceptance/` - End-to-end acceptance tests from user perspective

## Test Types

### Unit Tests (`unit/`)
- Test individual functions/methods in isolation
- Use mocks for external dependencies
- Fast execution (milliseconds)
- **Status**: Framework in place, tests to be added as application grows
- Run with: `uv run python -m pytest tests/unit/ -v`

### Integration Tests (`integration/`)
- Test interactions between components and real services
- Use real InfluxDB instance via Docker with least-privileged tokens
- Comprehensive end-to-end validation
- Moderate execution time (seconds to minutes)
- **Status**: Complete with 13 tests covering all workflows
- Run with: `cd tests/integration && ./run-integration-tests.sh`

### Acceptance Tests (`acceptance/`)
- Test complete user workflows and business requirements
- Use production-like environments
- Slower execution (minutes)
- **Status**: Framework in place, tests to be added as deployment environments mature
- Run with: `uv run python -m pytest tests/acceptance/ -v`

## Running All Tests

```bash
# Integration tests (recommended - comprehensive coverage)
cd tests/integration && ./run-integration-tests.sh

# Unit tests only (when available)
uv run python -m pytest tests/unit/ -v

# Acceptance tests (when available)
uv run python -m pytest tests/acceptance/ -v

# All tests (requires external services for integration)
uv run python -m pytest tests/ -v
```

**Note**: Currently, the integration tests provide comprehensive coverage of the entire system. Unit and acceptance tests can be added as the application and deployment environments evolve.

See individual README files in each subdirectory for specific test documentation.
