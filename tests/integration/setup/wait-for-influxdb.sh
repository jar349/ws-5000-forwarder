#!/bin/bash
# Shared utility script to wait for InfluxDB to be ready
# Usage: wait-for-influxdb.sh [timeout_seconds] [host_url]

set -e

TIMEOUT=${1:-30}
HOST_URL=${2:-"http://localhost:8086"}

echo "Waiting for InfluxDB to be ready at $HOST_URL (timeout: ${TIMEOUT}s)..."

ELAPSED=0
while true; do
    # Capture both output and return code of influx ping
    PING_OUTPUT=$(influx ping --host "$HOST_URL" 2>&1)
    PING_RESULT=$?
    
    if [ $PING_RESULT -eq 0 ]; then
        echo "InfluxDB ping successful!"
        break
    fi
    
    if [ $ELAPSED -ge $TIMEOUT ]; then
        echo "ERROR: InfluxDB did not become ready within $TIMEOUT seconds"
        echo "Last ping output: $PING_OUTPUT"
        echo "Last ping return code: $PING_RESULT"
        exit 1
    fi
    
    echo "InfluxDB not ready yet (attempt: ${ELAPSED}s/${TIMEOUT}s, return code: $PING_RESULT)"
    if [ $ELAPSED -eq 0 ] || [ $((ELAPSED % 5)) -eq 0 ]; then
        echo "Ping output: $PING_OUTPUT"
    fi
    sleep 1
    ELAPSED=$((ELAPSED + 1))
done

echo "InfluxDB is ready!"
