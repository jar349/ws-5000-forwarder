# Integration Tests

This directory contains integration tests for the WS-5000 forwarder application.

## Test Structure

- `conftest.py` - Shared test configuration and fixtures
- `test_integration.py` - Main integration tests for API endpoints
- `test_influxdb_integration.py` - Direct InfluxDB integration tests
- `setup/` - Setup scripts for test environment:
  - `setup-limited-token.sh` - Creates least-privileged InfluxDB token for app
  - `wait-for-influxdb.sh` - Waits for InfluxDB to be ready
- `docker-compose.test.yml` - Docker Compose configuration for test environment
- `run-integration-tests.sh` - Main test runner script

## Running Tests

### Quick Start
```bash
cd tests/integration
./run-integration-tests.sh
```

### Local Testing
If you have InfluxDB and the app running locally:
```bash
cd tests/integration  
./run-tests-local.sh
```

### Manual Steps
```bash
cd tests/integration

# Build and start test environment
docker-compose -f docker-compose.test.yml up -d influxdb app

# Run tests
docker-compose -f docker-compose.test.yml up test-runner

# Cleanup
docker-compose -f docker-compose.test.yml down -v
```

## Test Environment

The integration tests use Docker Compose with a **unified multi-stage Dockerfile** to create:

1. **InfluxDB 2.7** - Configured with:
   - Organization: `ws5000-test`
   - Bucket: `ws-5000`
   - Admin token: `admin-token-for-setup-only` (setup only, not used by app)
   - Limited app token: Created dynamically with minimal permissions
   - Health checks: Ensures InfluxDB is ready before tests start

2. **WS-5000 App** - Your Flask application (built using `production` stage) configured to use the test InfluxDB

3. **Test Runner** - Python container (built using `testing` stage) with pytest and test dependencies

Both the app and test runner use the same unified Dockerfile (`../../Dockerfile`) with different build targets, ensuring **identical environments** and eliminating the risk of configuration drift between production and testing.

## Security

The test setup uses a **least-privileged security model**:

1. **Admin Token** (`admin-token-for-setup-only`):
   - Used only during setup to create buckets and limited tokens
   - **Never used by the application itself**
   - Could be rotated/disabled after setup

2. **Limited App Token** (created by `setup/setup-limited-token.sh`):
   - ✅ Read access to the `ws-5000` bucket only (needed for /health endpoint)
   - ✅ Write access to the `ws-5000` bucket only (needed for /measurements/ endpoint)
   - ❌ No admin privileges
   - ❌ No access to other buckets or organizations
   - ❌ Cannot create/delete buckets or manage users

3. **Token Validation**:
   - Setup script validates the token by writing and reading a test measurement
   - Test measurement is cleaned up, ensuring tests start with an empty bucket
   - Token is saved securely and passed to the application via environment variables

## Test Categories

### Health Endpoint Tests (`test_integration.py`)
- Basic health check functionality
- Timezone handling
- Error handling

### Measurements Endpoint Tests (`test_integration.py`)
- Data ingestion
- Data type handling (numeric vs string)
- Multiple measurements
- End-to-end workflow

### InfluxDB Integration Tests (`test_influxdb_integration.py`)
- Direct InfluxDB connectivity
- Data persistence
- Query functionality
- App-to-database integration

## Test Data

Tests use realistic weather station data including:
- Temperature, humidity, pressure
- Wind speed and direction
- Station identification
- Mixed data types (numeric fields, string tags)

## Troubleshooting

If tests fail:

### Container Issues
1. Check Docker containers are running: `docker-compose -f docker-compose.test.yml ps`
2. Check InfluxDB health: `docker-compose -f docker-compose.test.yml exec influxdb influx ping`
3. Check InfluxDB logs: `docker-compose -f docker-compose.test.yml logs influxdb`
4. Check app logs: `docker-compose -f docker-compose.test.yml logs app`

### InfluxDB Setup Issues
1. Verify InfluxDB initialization: `docker-compose -f docker-compose.test.yml exec influxdb influx auth list`
2. Check bucket exists: `docker-compose -f docker-compose.test.yml exec influxdb influx bucket list`
3. Verify limited token creation: `docker-compose -f docker-compose.test.yml exec influxdb cat /tmp/ws5000-app-token.txt`

### Token Issues
If token creation fails, you can manually run the setup script:
```bash
docker-compose -f docker-compose.test.yml exec influxdb /tmp/setup-limited-token.sh
```

### Clean Start
For a completely clean test environment:
```bash
docker-compose -f docker-compose.test.yml down -v  # Remove volumes
docker system prune -f  # Clean up containers/images
./run-integration-tests.sh  # Start fresh
```
