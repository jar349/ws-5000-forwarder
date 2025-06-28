import requests
import time
import json
from datetime import datetime, timezone
from tests.integration.conftest import TestConfig


class TestHealthEndpoint:
    """Integration tests for the /health endpoint"""
    
    def test_health_endpoint_responds(self, app_url, wait_for_services):
        """Test that health endpoint responds"""
        response = requests.get(f"{app_url}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "influxdb_connected" in data
        assert "started_on_rfc3339" in data
    
    def test_health_endpoint_timezone_header(self, app_url, wait_for_services):
        """Test timezone handling in health endpoint"""
        headers = {"X-REQUESTED-TZ": "America/New_York"}
        response = requests.get(f"{app_url}/health", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "timezone" in data
        # Should contain timezone info in the timestamp
        assert "started_on_rfc3339" in data
        assert data["started_on_rfc3339"] is not None
    
    def test_health_endpoint_invalid_timezone(self, app_url, wait_for_services):
        """Test that invalid timezone falls back to UTC"""
        headers = {"X-REQUESTED-TZ": "Invalid/Timezone"}
        response = requests.get(f"{app_url}/health", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should fall back to UTC
        assert "UTC" in str(data.get("timezone", ""))


class TestMeasurementsEndpoint:
    """Integration tests for the /measurements/ endpoint"""
    
    def test_post_measurements(self, app_url, sample_weather_data, wait_for_services):
        """Test posting weather measurements"""
        response = requests.post(f"{app_url}/measurements/", data=sample_weather_data)
        
        assert response.status_code == 200
        assert response.text == "OK"
    
    def test_measurements_appear_in_health_check(self, app_url, sample_weather_data, wait_for_services):
        """Test that posted measurements appear in health check"""
        # Post measurement
        response = requests.post(f"{app_url}/measurements/", data=sample_weather_data)
        assert response.status_code == 200
        
        # Wait a moment for data to be written
        time.sleep(2)
        
        # Check health endpoint for latest measurement
        health_response = requests.get(f"{app_url}/health")
        assert health_response.status_code == 200
        
        health_data = health_response.json()
        assert health_data["status"] == "healthy"
        assert health_data["influxdb_connected"] is True
        assert health_data["last_measurement_rfc3339"] is not None
    
    def test_multiple_measurements(self, app_url, wait_for_services):
        """Test posting multiple measurements"""
        measurements = [
            {"temperature": "20.1", "humidity": "60", "station": "A"},
            {"temperature": "21.2", "humidity": "58", "station": "B"},
            {"temperature": "22.3", "humidity": "62", "station": "C"},
        ]
        
        for measurement in measurements:
            response = requests.post(f"{app_url}/measurements/", data=measurement)
            assert response.status_code == 200
            time.sleep(0.5)  # Small delay between measurements
        
        # Verify latest measurement is captured
        time.sleep(2)
        health_response = requests.get(f"{app_url}/health")
        health_data = health_response.json()
        
        assert health_data["influxdb_connected"] is True
        assert health_data["last_measurement_rfc3339"] is not None
    
    def test_measurements_with_mixed_data_types(self, app_url, wait_for_services):
        """Test that numeric and string values are handled correctly"""
        mixed_data = {
            "temperature": "23.5",      # Should be a field (numeric)
            "humidity": "65",           # Should be a field (numeric)
            "station_id": "WS001",      # Should be a tag (string)
            "model": "WS-5000",         # Should be a tag (string)
            "invalid_num": "not_a_number",  # Should be a tag (string)
        }
        
        response = requests.post(f"{app_url}/measurements/", data=mixed_data)
        assert response.status_code == 200
        
        # Verify data was written
        time.sleep(2)
        health_response = requests.get(f"{app_url}/health")
        health_data = health_response.json()
        assert health_data["influxdb_connected"] is True


class TestEndToEndWorkflow:
    """End-to-end integration tests"""
    
    def test_complete_weather_station_workflow(self, app_url, wait_for_services):
        """Test complete workflow from data ingestion to health check"""
        # Simulate weather station data
        weather_data = {
            "dateutc": "2025-06-28 15:30:00",
            "tempf": "74.3",
            "humidity": "65",
            "windspeedmph": "7.8",
            "winddir": "180",
            "dailyrainin": "0.05",
            "baromin": "29.92",
            "model": "WS-5000",
            "PASSKEY": "test123"
        }
        
        # Step 1: Post data
        response = requests.post(f"{app_url}/measurements/", data=weather_data)
        assert response.status_code == 200
        
        # Step 2: Wait for processing
        time.sleep(3)
        
        # Step 3: Verify via health check
        health_response = requests.get(f"{app_url}/health")
        assert health_response.status_code == 200
        
        health_data = health_response.json()
        assert health_data["status"] == "healthy"
        assert health_data["influxdb_connected"] is True
        assert health_data["last_measurement_rfc3339"] is not None
        
        # Step 4: Test timezone conversion
        tz_response = requests.get(
            f"{app_url}/health", 
            headers={"X-REQUESTED-TZ": "America/Los_Angeles"}
        )
        assert tz_response.status_code == 200
        
        tz_data = tz_response.json()
        assert "America/Los_Angeles" in str(tz_data.get("timezone", ""))
    
    def test_app_resilience(self, app_url, wait_for_services):
        """Test app behavior under various conditions"""
        # Test empty data
        response = requests.post(f"{app_url}/measurements/", data={})
        assert response.status_code == 200  # Should handle gracefully
        
        # Test malformed data
        response = requests.post(f"{app_url}/measurements/", data={"": ""})
        assert response.status_code == 200  # Should handle gracefully
        
        # Health check should still work
        health_response = requests.get(f"{app_url}/health")
        assert health_response.status_code == 200
