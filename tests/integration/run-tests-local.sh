#!/bin/bash
set -e

echo "Running local integration tests..."

# Change to project root directory
cd "$(dirname "$0")/../.."

# Set test environment variables
export INFLUX_URL="${INFLUX_URL:-http://localhost:8086}"
export INFLUX_ORG="${INFLUX_ORG:-ws5000-test}"
export INFLUX_BUCKET="${INFLUX_BUCKET:-ws-5000}"
export INFLUX_TOKEN="${INFLUX_TOKEN:-ws5000-app-token}"
export APP_URL="${APP_URL:-http://localhost:8000}"

echo "Test configuration:"
echo "  INFLUX_URL: $INFLUX_URL"
echo "  INFLUX_ORG: $INFLUX_ORG"
echo "  INFLUX_BUCKET: $INFLUX_BUCKET"
echo "  APP_URL: $APP_URL"

# Check if services are running
echo "Checking if services are available..."

if ! curl -s "$INFLUX_URL/ping" > /dev/null; then
    echo "ERROR: InfluxDB is not available at $INFLUX_URL"
    echo "Please start InfluxDB or run the full Docker-based tests with:"
    echo "  ./run-integration-tests.sh"
    exit 1
fi

if ! curl -s "$APP_URL/health" > /dev/null; then
    echo "ERROR: Application is not available at $APP_URL"
    echo "Please start the application or run the full Docker-based tests with:"
    echo "  ./run-integration-tests.sh"
    exit 1
fi

echo "Services are available. Running tests..."

# Run the tests
uv run python -m pytest tests/integration/ -v "$@"

echo "Local integration tests completed!"
