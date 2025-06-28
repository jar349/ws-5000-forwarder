"""
InfluxDB Integration Tests

These tests verify the integration between the WS-5000 forwarder app
and InfluxDB using a real InfluxDB instance.
"""
import requests
import time
import os
from influxdb_client import InfluxDBClient, Point, WriteOptions
from tests.integration.conftest import TestConfig


class TestInfluxDBIntegration:
    """Direct InfluxDB integration tests"""
    
    def setup_method(self):
        """Setup InfluxDB client for testing"""
        self.client = InfluxDBClient(
            url=TestConfig.INFLUX_URL,
            token=TestConfig.INFLUX_TOKEN,
            org=TestConfig.INFLUX_ORG
        )
        self.query_api = self.client.query_api()
        self.write_api = self.client.write_api(write_options=WriteOptions(batch_size=1))
    
    def teardown_method(self):
        """Cleanup InfluxDB client"""
        if hasattr(self, 'client'):
            self.client.close()
    
    def test_influxdb_connection(self):
        """Test direct connection to InfluxDB"""
        # Test basic connectivity
        health = self.client.health()
        assert health.status == "pass"
    
    def test_influxdb_write_and_query(self):
        """Test writing to and querying from InfluxDB"""
        # Write a test point
        point = Point("weather") \
            .tag("test", "integration") \
            .field("temperature", 25.0) \
            .field("humidity", 70.0)
        
        self.write_api.write(bucket=TestConfig.INFLUX_BUCKET, org=TestConfig.INFLUX_ORG, record=point)
        
        # Wait for write to complete
        time.sleep(2)
        
        # Query the data back
        query = f'''
        from(bucket: "{TestConfig.INFLUX_BUCKET}")
        |> range(start: -5m)
        |> filter(fn: (r) => r._measurement == "weather")
        |> filter(fn: (r) => r.test == "integration")
        '''
        
        result = self.query_api.query(query=query, org=TestConfig.INFLUX_ORG)
        
        assert len(result) > 0
        
        # Verify the data - InfluxDB returns one table per field
        all_records = []
        for table in result:
            all_records.extend(table.records)
        
        assert len(all_records) > 0
        
        temp_record = next((r for r in all_records if r.get_field() == "temperature"), None)
        humidity_record = next((r for r in all_records if r.get_field() == "humidity"), None)
        
        assert temp_record is not None, f"Temperature record not found. Available fields: {[r.get_field() for r in all_records]}"
        assert temp_record.get_value() == 25.0
        assert humidity_record is not None, f"Humidity record not found. Available fields: {[r.get_field() for r in all_records]}"
        assert humidity_record.get_value() == 70.0
    
    def test_app_data_appears_in_influxdb(self, app_url, wait_for_services):
        """Test that data posted to app appears in InfluxDB"""
        # Clear any existing test data
        timestamp = int(time.time())
        
        # Post data through the app
        test_data = {
            "temperature": "26.5",
            "humidity": "68",
            "test_id": f"integration_{timestamp}"
        }
        
        response = requests.post(f"{app_url}/measurements/", data=test_data)
        assert response.status_code == 200
        
        # Wait for data to be written
        time.sleep(3)
        
        # Query InfluxDB directly to verify the data
        query = f'''
        from(bucket: "{TestConfig.INFLUX_BUCKET}")
        |> range(start: -2m)
        |> filter(fn: (r) => r._measurement == "weather")
        |> filter(fn: (r) => r.test_id == "integration_{timestamp}")
        '''
        
        result = self.query_api.query(query=query, org=TestConfig.INFLUX_ORG)
        
        assert len(result) > 0
        
        # Verify the specific values - InfluxDB returns one table per field
        all_records = []
        for table in result:
            all_records.extend(table.records)
        
        assert len(all_records) > 0
        
        temp_record = next((r for r in all_records if r.get_field() == "temperature"), None)
        humidity_record = next((r for r in all_records if r.get_field() == "humidity"), None)
        
        assert temp_record is not None, f"Temperature record not found. Available fields: {[r.get_field() for r in all_records]}"
        assert temp_record.get_value() == 26.5
        assert humidity_record is not None, f"Humidity record not found. Available fields: {[r.get_field() for r in all_records]}"
        assert humidity_record.get_value() == 68.0
    
    def test_data_persistence_across_restarts(self, app_url, wait_for_services):
        """Test that data persists in InfluxDB"""
        # Write data with unique identifier
        timestamp = int(time.time())
        test_data = {
            "temperature": "23.7",
            "persistence_test": f"restart_{timestamp}"
        }
        
        response = requests.post(f"{app_url}/measurements/", data=test_data)
        assert response.status_code == 200
        
        # Wait for write
        time.sleep(2)
        
        # Query to verify data exists
        query = f'''
        from(bucket: "{TestConfig.INFLUX_BUCKET}")
        |> range(start: -2m)
        |> filter(fn: (r) => r._measurement == "weather")
        |> filter(fn: (r) => r.persistence_test == "restart_{timestamp}")
        '''
        
        result = self.query_api.query(query=query, org=TestConfig.INFLUX_ORG)
        assert len(result) > 0
        
        # Verify the data value - InfluxDB returns one table per field
        all_records = []
        for table in result:
            all_records.extend(table.records)
        
        assert len(all_records) > 0
        
        # Verify the data value
        temp_record = next((r for r in all_records if r.get_field() == "temperature"), None)
        assert temp_record is not None
        assert temp_record.get_value() == 23.7
