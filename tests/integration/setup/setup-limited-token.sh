#!/bin/bash
set -e

echo "Creating limited InfluxDB token for WS-5000 app..."

# First, get the bucket ID for the ws-5000 bucket
BUCKET_ID=$(influx bucket list --org ws5000-test --token admin-token-for-setup-only | grep ws-5000 | awk '{print $1}')

if [ -z "$BUCKET_ID" ]; then
    echo "ERROR: Could not find ws-5000 bucket ID"
    exit 1
fi

echo "Found ws-5000 bucket ID: $BUCKET_ID"

# Check if a limited token already exists for this bucket
INFLUX_TOKEN=$(influx auth list --org ws5000-test --token admin-token-for-setup-only | grep "read:orgs/.*/buckets/$BUCKET_ID" | head -1 | cut -f3)

# If no existing token, create a new one
if [ -z "$INFLUX_TOKEN" ]; then
    echo "Creating new limited token..."
    # Create a token with read-write access only to the ws-5000 bucket using bucket ID
    DESCRIPTION="WS-5000 App Token - $(date +%s)"
    influx auth create \
        --org ws5000-test \
        --description "$DESCRIPTION" \
        --read-bucket "$BUCKET_ID" \
        --write-bucket "$BUCKET_ID" \
        --token admin-token-for-setup-only > /dev/null 2>&1

    # Get the token using the description we just created
    INFLUX_TOKEN=$(influx auth list --org ws5000-test --token admin-token-for-setup-only | grep "$DESCRIPTION" | cut -f3)
else
    echo "Using existing limited token..."
fi

# Validate token was created
if [ -z "$INFLUX_TOKEN" ]; then
    echo "ERROR: Failed to create limited token"
    exit 1
fi

echo "Created limited token: ${INFLUX_TOKEN:0:10}..."

# Test the token by writing a test measurement
echo "Testing limited token by writing a measurement..."
influx write \
    --org ws5000-test \
    --bucket ws-5000 \
    --token "$INFLUX_TOKEN" \
    --precision s \
    'weather,test=setup temperature=20.0,humidity=50.0'

# Verify we can read it back
echo "Testing limited token by reading measurement..."
influx query \
    --org ws5000-test \
    --token "$INFLUX_TOKEN" \
    'from(bucket:"ws-5000") |> range(start:-1h) |> filter(fn:(r) => r["test"] == "setup") |> last()' > /dev/null

echo "Limited token validation successful!"

# Clean up the test measurement so integration tests start with an empty bucket
echo "Cleaning up test measurement..."
influx delete \
    --org ws5000-test \
    --bucket ws-5000 \
    --token "$INFLUX_TOKEN" \
    --start 1970-01-01T00:00:00Z \
    --stop $(date -u +%Y-%m-%dT%H:%M:%SZ) \
    --predicate 'test="setup"' > /dev/null 2>&1 || echo "No test measurements to clean up"

# Output the token to a file that can be read by other services
echo "$INFLUX_TOKEN" > /tmp/ws5000-app-token.txt

echo "Setup complete! Limited token saved to /tmp/ws5000-app-token.txt"
echo "Bucket is now clean and ready for integration tests"
