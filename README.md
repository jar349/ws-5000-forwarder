# WS-5000 Weather Station to InfluxDB Forwarder

A Flask application that receives weather data from WS-5000 weather stations (in Ecowitt format) and forwards it to InfluxDB with robust error handling and comprehensive testing.

## Key Features

- **Flexible Data Handling**: Automatically distinguishes between numeric fields (stored as measurements) and string values (stored as tags)
- **Timezone Support**: Health endpoint supports timezone conversion via `X-REQUESTED-TZ` header
- **Robust Error Handling**: Graceful handling of invalid data, network issues, and service failures
- **Production-Ready**: Multi-stage Docker build with separate production and testing configurations
- **Comprehensive Testing**: 13 integration tests covering all workflows with least-privileged security model
- **Health Monitoring**: Built-in health endpoint with InfluxDB connectivity and data freshness checks
- **Security-First**: Uses minimal-privilege InfluxDB tokens for production and testing

## Setup

1. Install dependencies using uv:
```bash
uv sync
```

2. Set required environment variables:
```bash
export INFLUX_TOKEN="your_influxdb_token"
export INFLUX_ORG="your_influxdb_organization"
```

3. Optional environment variables (with defaults):
```bash
export INFLUX_URL="http://localhost:8086"  # Default
export INFLUX_BUCKET="ws-5000"     # Default
```

**Security Note**: The `INFLUX_TOKEN` should have only read/write access to the specified bucket. Avoid using admin tokens in production. See the integration tests setup for an example of creating least-privileged tokens.

## Running

Start the Flask application:
```bash
uv run python app.py
```

The server will start on `http://0.0.0.0:8000` and accept POST requests with weather data.

## Docker

The project uses a **unified multi-stage Dockerfile** that supports both production and testing environments, ensuring consistent configurations and eliminating environment drift.

### Building the Docker Image

**For Production:**
```bash
docker build --target production -t ws-5000-forwarder .
```

**For Testing:**
```bash
docker build --target testing -t ws-5000-forwarder-test .
```

**Default (Production):**
```bash
docker build -t ws-5000-forwarder .  # Defaults to production stage
```

### Running with Docker

```bash
docker run -p 8000:8000 \
  -e INFLUX_TOKEN="your_token" \
  -e INFLUX_ORG="your_org" \
  -e INFLUX_URL="http://your-influxdb:8086" \
  ws-5000-forwarder
```

## Usage

The application provides two endpoints:

### POST /measurements/
Accepts POST requests with form data containing weather measurements. Numeric values are stored as fields, while non-numeric values are stored as tags in InfluxDB.

### GET /health
Returns a JSON health check response that includes:
- InfluxDB connectivity status
- Timestamp of the latest weather measurement (if available)
- Application start time
- Both timestamps are formatted in RFC 3339 format

**Timezone Support:**
You can specify a timezone by including the `X-REQUESTED-TZ` header in your request to `/health`. The timestamps will be converted to the requested timezone. If no timezone is specified or an invalid timezone is provided, UTC will be used.

Example:
```bash
curl -H "X-REQUESTED-TZ: America/New_York" http://localhost:8000/health
```

## Testing

The project includes comprehensive tests organized by type:

- `tests/unit/` - Unit tests for individual functions/classes
- `tests/integration/` - Integration tests with real services  
- `tests/acceptance/` - End-to-end acceptance tests

### Integration Tests

Integration tests verify the complete workflow from data ingestion to InfluxDB storage using real services.

#### Docker-based Integration Tests
```bash
cd tests/integration
./run-integration-tests.sh
```

This will:
1. Build both production and testing images from the unified Dockerfile
2. Start InfluxDB with proper configuration and health checks
3. Create a least-privileged API token for the app (read/write access to ws-5000 bucket only)
4. Start the application (using production stage)
5. Run all integration tests (using testing stage)
6. Clean up test environment and remove all containers/volumes

#### Local Integration Testing
If you have InfluxDB and the app running locally:
```bash
cd tests/integration
./run-tests-local.sh
```

#### Test Categories
- **Health endpoint tests** - Timezone handling, error responses
- **Measurements endpoint tests** - Data ingestion, type handling
- **InfluxDB integration tests** - Direct database connectivity and persistence
- **End-to-end workflow tests** - Complete weather station simulation

See `tests/integration/README.md` for detailed integration test documentation.
