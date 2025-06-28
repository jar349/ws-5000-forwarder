import pytest
import requests
import time
import os
from datetime import datetime, timezone


class TestConfig:
    """Test configuration"""
    INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
    INFLUX_ORG = os.getenv("INFLUX_ORG", "ws5000-test")
    INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "ws-5000")
    INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "ws5000-app-token")
    APP_URL = os.getenv("APP_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def app_url():
    """Base URL for the application"""
    return TestConfig.APP_URL


@pytest.fixture(scope="session")
def wait_for_services():
    """Wait for all services to be ready"""
    max_retries = 30
    retry_delay = 2
    
    # Wait for app health endpoint
    for i in range(max_retries):
        try:
            response = requests.get(f"{TestConfig.APP_URL}/health", timeout=5)
            if response.status_code == 200:
                print("App is ready!")
                break
        except requests.exceptions.RequestException:
            pass
        
        if i == max_retries - 1:
            raise RuntimeError("App did not become ready in time")
        
        print(f"Waiting for app... (attempt {i+1}/{max_retries})")
        time.sleep(retry_delay)
    
    # Wait a bit more for everything to stabilize
    time.sleep(2)


@pytest.fixture
def sample_weather_data():
    """Sample weather data for testing"""
    return {
        "temperature": "23.5",
        "humidity": "65",
        "pressure": "1013.25",
        "wind_speed": "12.5",
        "wind_direction": "180",
        "station_id": "WS001",
        "model": "WS-5000"
    }
