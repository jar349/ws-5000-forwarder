import io
import logging
import os
import pytz
import sys
import threading
import time
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from influxdb_client import InfluxDBClient, Point, WriteOptions


# Configure logging
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, write_through=True)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
level = getattr(logging, LOG_LEVEL, logging.INFO)

logging.basicConfig(
    level=level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

logger = logging.getLogger(__name__)

# Configure from environment variables
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "ws-5000")

# control some influxdb tag usage
ALLOWED_TAGS = {"stationtype", "mac"}

# Validate required environment variables
if not INFLUX_TOKEN:
    logger.error("INFLUX_TOKEN environment variable is required")
    raise ValueError("INFLUX_TOKEN environment variable is required")
if not INFLUX_ORG:
    logger.error("INFLUX_ORG environment variable is required")
    raise ValueError("INFLUX_ORG environment variable is required")

logger.info(f"Starting WS-5000 forwarder with InfluxDB at {INFLUX_URL}, org: {INFLUX_ORG}, bucket: {INFLUX_BUCKET}")

# Record app start time
APP_START_TIME = datetime.now(timezone.utc)
logger.info(f"Application started at {APP_START_TIME.isoformat()}")

app = Flask(__name__)
try:
    SYNCH = WriteOptions(batch_size=1, flush_interval=1_000, jitter_interval=0, retry_interval=5_000, write_type="synchronous")
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    query_api = client.query_api()
    write_api = client.write_api(write_options=SYNCH)
    logger.info("Successfully connected to InfluxDB")
except Exception as e:
    logger.error(f"Failed to connect to InfluxDB: {e}")
    raise

@app.route("/measurements", methods=["GET"])
def receive_data():
    logger.info(f"Received measurement data from {request.remote_addr}")
    
    try:
        data = request.args.to_dict()
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Measurement data: {data}")
        
        if not data:
            logger.warning("Received empty measurement data")
            return "OK"  # Still return OK to avoid weather station retries
        
        point = Point("weather")
        field_count = 0
        tag_count = 0

        for key, value in data.items():
            logger.debug(f"Processing {key}={value} (type: {type(value)})")
            try:
                float_value = float(value)
                point.field(key, float_value)
                field_count += 1
                logger.debug(f"Added field: {key}={float_value}")
            except ValueError:
                if key in ALLOWED_TAGS:
                  point.tag(key, value)
                  tag_count += 1
                  logger.debug(f"Added tag: {key}={value}")

        logger.debug(f"Created InfluxDB point with {field_count} fields and {tag_count} tags")
        
        try:
            write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
            logger.info("Successfully wrote measurement to InfluxDB")
        except Exception as write_error:
            logger.error(f"Failed to write to InfluxDB: {write_error}", exc_info=True)
            raise
        
        del data
        del point
        return "OK"
    
    except Exception as e:
        logger.error(f"Error processing measurement data: {e}", exc_info=True)
        # Still return OK to avoid weather station retry loops
        return "OK"

@app.route("/health", methods=["GET"])
def health_check():
    try:
        h = client.health()  # REST JSON call, no Flux CSV parsing
        if getattr(h, "status", "").lower() == "pass":
            return jsonify({"status": "ok"}), 200
        else:
            return jsonify({
                "status": "unhealthy",
                "influxdb_status": getattr(h, "status", None),
                "message": getattr(h, "message", None)
            }), 503
    except Exception as e:
        return jsonify({
            "status": "unreachable",
            "error": str(e)
        }), 503

if __name__ == "__main__":
    logger.info("Starting Flask development server on 0.0.0.0:8000")
    app.run(host="0.0.0.0", port=8000)
