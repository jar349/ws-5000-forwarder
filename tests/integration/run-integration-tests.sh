#!/bin/bash
set -e

echo "Starting integration tests..."

# Change to the integration test directory
cd "$(dirname "$0")"

# Build and start services
echo "Building Docker images..."
docker-compose -f docker-compose.test.yml build

echo "Starting test environment..."
# Start InfluxDB first and wait for it to be healthy
docker-compose -f docker-compose.test.yml up -d influxdb

echo "Waiting for InfluxDB to be healthy..."
while ! docker-compose -f docker-compose.test.yml exec -T influxdb influx ping --host http://localhost:8086 >/dev/null 2>&1; do
    echo "Waiting for InfluxDB..."
    sleep 2
done
echo "InfluxDB is healthy!"

echo "Creating limited InfluxDB token..."
# Copy setup script to container and execute it
docker cp setup/setup-limited-token.sh ws5000-test-influxdb:/tmp/setup-limited-token.sh
docker-compose -f docker-compose.test.yml exec -T influxdb chmod +x /tmp/setup-limited-token.sh
docker-compose -f docker-compose.test.yml exec -T influxdb /tmp/setup-limited-token.sh

echo "Extracting limited token..."
# Get the limited token from the container
LIMITED_TOKEN=$(docker-compose -f docker-compose.test.yml exec -T influxdb cat /tmp/ws5000-app-token.txt | tr -d '\r\n')

if [ -z "$LIMITED_TOKEN" ]; then
    echo "ERROR: Failed to retrieve limited token"
    exit 1
fi

echo "Using limited token: ${LIMITED_TOKEN:0:10}..."

# Export the token for use by services
export WS5000_LIMITED_TOKEN="$LIMITED_TOKEN"

echo "Starting app and test services with limited token..."

echo "Running integration tests..."
WS5000_LIMITED_TOKEN="$LIMITED_TOKEN" docker-compose -f docker-compose.test.yml up --exit-code-from test-runner app test-runner

echo "Collecting test results..."
mkdir -p test-results
docker cp ws5000-test-runner:/app/test-results/. test-results/ 2>/dev/null || echo "No test results to copy"

echo "Cleaning up..."
docker-compose -f docker-compose.test.yml down -v

echo "Integration tests completed!"
