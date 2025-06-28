import os
import logging
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from influxdb_client import InfluxDBClient, Point, WriteOptions
import pytz

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure from environment variables
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "ws-5000")

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
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = client.write_api(write_options=WriteOptions(batch_size=1))
    logger.info("Successfully connected to InfluxDB")
except Exception as e:
    logger.error(f"Failed to connect to InfluxDB: {e}")
    raise

@app.route("/measurements/", methods=["POST"])
def receive_data():
    logger.info(f"Received measurement data from {request.remote_addr}")
    
    try:
        data = request.form.to_dict()
        logger.info(f"Measurement data: {data}")
        
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
                point.tag(key, value)
                tag_count += 1
                logger.debug(f"Added tag: {key}={value}")

        logger.info(f"Created InfluxDB point with {field_count} fields and {tag_count} tags")
        
        try:
            write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
            write_api.flush()  # Force immediate write
            logger.info("Successfully wrote measurement to InfluxDB")
        except Exception as write_error:
            logger.error(f"Failed to write to InfluxDB: {write_error}", exc_info=True)
            raise
        
        return "OK"
    
    except Exception as e:
        logger.error(f"Error processing measurement data: {e}", exc_info=True)
        # Still return OK to avoid weather station retry loops
        return "OK"

@app.route("/health", methods=["GET"])
def health_check():
    logger.debug(f"Health check requested from {request.remote_addr}")
    
    # Get requested timezone from header, default to UTC
    requested_tz_str = request.headers.get("X-REQUESTED-TZ", "UTC")
    logger.debug(f"Requested timezone: {requested_tz_str}")
    
    try:
        # Parse the requested timezone
        if requested_tz_str.upper() == "UTC":
            requested_tz = timezone.utc
        else:
            requested_tz = pytz.timezone(requested_tz_str)
        logger.debug(f"Successfully parsed timezone: {requested_tz}")
    except Exception as tz_error:
        logger.warning(f"Invalid timezone '{requested_tz_str}', falling back to UTC: {tz_error}")
        # Fall back to UTC if timezone is invalid
        requested_tz = timezone.utc
    
    # Format app start time in requested timezone
    app_start_local = APP_START_TIME.astimezone(requested_tz)
    started_on_rfc3339 = app_start_local.isoformat()
    
    try:
        logger.debug("Querying InfluxDB for latest measurement")
        # Query InfluxDB for the latest measurement
        query_api = client.query_api()
        query = f'''
        from(bucket: "{INFLUX_BUCKET}")
        |> range(start: -30d)
        |> filter(fn: (r) => r._measurement == "weather")
        |> last()
        '''
        
        result = query_api.query(query=query, org=INFLUX_ORG)
        
        last_measurement_rfc3339 = None
        if result and len(result) > 0 and len(result[0].records) > 0:
            # Get the timestamp from the latest record
            latest_record = result[0].records[0]
            timestamp = latest_record.get_time()
            
            # Convert to requested timezone
            timestamp_local = timestamp.astimezone(requested_tz)
            last_measurement_rfc3339 = timestamp_local.isoformat()
            logger.debug(f"Found latest measurement at {last_measurement_rfc3339}")
        else:
            logger.warning("No recent measurements found in InfluxDB")
        
        response_data = {
            "status": "healthy",
            "influxdb_connected": True,
            "last_measurement_rfc3339": last_measurement_rfc3339,
            "started_on_rfc3339": started_on_rfc3339,
            "timezone": str(requested_tz)
        }
        
        logger.debug(f"Health check successful, returning status: {response_data['status']}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Health check failed due to InfluxDB error: {e}", exc_info=True)
        
        response_data = {
            "status": "unhealthy",
            "influxdb_connected": False,
            "error": str(e),
            "last_measurement_rfc3339": None,
            "started_on_rfc3339": started_on_rfc3339,
            "timezone": str(requested_tz)
        }
        
        logger.warning(f"Health check returning unhealthy status due to: {e}")
        return jsonify(response_data), 500

if __name__ == "__main__":
    logger.info("Starting Flask development server on 0.0.0.0:8000")
    app.run(host="0.0.0.0", port=8000)
