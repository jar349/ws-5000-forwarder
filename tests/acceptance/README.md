# Acceptance Tests

This directory contains acceptance tests that verify the complete system meets business requirements from an end-user perspective.

Acceptance tests should:
- Test complete user workflows
- Use production-like environments
- Verify business requirements are met
- Test from the user's perspective

## Structure

Acceptance tests will be added as deployment environments mature. The typical structure would include:
- `test_weather_station_workflows.py` - Complete weather station scenarios
- `test_monitoring_workflows.py` - Health monitoring and alerting scenarios
- `conftest.py` - Shared acceptance test configuration

Currently, the comprehensive integration tests in `tests/integration/` provide end-to-end validation of the system.

## Running Acceptance Tests

```bash
# From project root
uv run python -m pytest tests/acceptance/ -v

# Against staging environment
INFLUX_URL=https://staging-influx.example.com \
APP_URL=https://staging-ws5000.example.com \
uv run python -m pytest tests/acceptance/ -v
```

## Examples

Acceptance tests typically verify:
- Complete weather data ingestion workflows
- Data appears correctly in monitoring dashboards
- Alert systems work with real data
- Performance under realistic load
- Multi-day data retention and querying
