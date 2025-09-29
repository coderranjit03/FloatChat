"""
Basic tests for ARGO platform components
"""

import pytest
import asyncio
import json
from datetime import datetime


class TestARGOPlatform:
    """Test suite for ARGO platform"""
    
    def test_sample_data_generation(self):
        """Test sample data generation"""
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data'))
        
        from generate_sample_data import ARGODataGenerator
        
        generator = ARGODataGenerator()
        
        # Test ARGO profile generation
        profiles = generator.generate_argo_profiles(5)
        assert len(profiles) == 5
        assert all('float_id' in p for p in profiles)
        assert all('measurements' in p for p in profiles)
        
        # Test measurements
        for profile in profiles:
            measurements = profile['measurements']
            assert len(measurements) > 0
            assert all('depth' in m for m in measurements)
            assert all('temperature' in m for m in measurements)
            assert all('salinity' in m for m in measurements)
    
    def test_satellite_data_generation(self):
        """Test satellite data generation"""
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data'))
        
        from generate_sample_data import ARGODataGenerator
        
        generator = ARGODataGenerator()
        records = generator.generate_satellite_data(10)
        
        assert len(records) == 10
        assert all('satellite_name' in r for r in records)
        assert all('latitude' in r for r in records)
        assert all('longitude' in r for r in records)
        assert all('value' in r for r in records)
    
    def test_buoy_data_generation(self):
        """Test buoy data generation"""
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data'))
        
        from generate_sample_data import ARGODataGenerator
        
        generator = ARGODataGenerator()
        records = generator.generate_buoy_data(10)
        
        assert len(records) == 10
        assert all('buoy_id' in r for r in records)
        assert all('sea_surface_temperature' in r for r in records)
        assert all('wind_speed' in r for r in records)
    
    def test_configuration_loading(self):
        """Test configuration loading"""
        import os
        
        # Check if .env.example exists
        env_example_path = os.path.join(os.path.dirname(__file__), '..', '.env.example')
        assert os.path.exists(env_example_path), ".env.example file should exist"
        
        # Check if key configuration variables are in the example
        with open(env_example_path, 'r') as f:
            content = f.read()
            required_vars = [
                'DATABASE_URL',
                'REDIS_URL',
                'CHROMA_URL',
                'SECRET_KEY'
            ]
            
            for var in required_vars:
                assert var in content, f"Required variable {var} should be in .env.example"
    
    def test_docker_compose_configuration(self):
        """Test Docker Compose configuration"""
        import os
        import yaml
        
        compose_path = os.path.join(os.path.dirname(__file__), '..', 'docker-compose.yml')
        assert os.path.exists(compose_path), "docker-compose.yml should exist"
        
        with open(compose_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check required services
        required_services = ['postgres', 'redis', 'chroma', 'backend', 'frontend']
        assert 'services' in config
        
        for service in required_services:
            assert service in config['services'], f"Service {service} should be in docker-compose.yml"
    
    def test_readme_completeness(self):
        """Test README completeness"""
        import os
        
        readme_path = os.path.join(os.path.dirname(__file__), '..', 'README.md')
        assert os.path.exists(readme_path), "README.md should exist"
        
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for key sections
        required_sections = [
            'Features',
            'Architecture',
            'Quick Start',
            'API Documentation',
            'Usage Examples'
        ]
        
        for section in required_sections:
            assert section in content, f"README should contain {section} section"


def test_basic_imports():
    """Test that basic imports work without errors"""
    try:
        import pandas
        import numpy
        import json
        import datetime
        import os
        assert True
    except ImportError as e:
        pytest.fail(f"Basic import failed: {e}")


def test_sample_data_structure():
    """Test sample data has correct structure"""
    sample_profile = {
        "float_id": "ARGO_1001",
        "profile_date": "2024-01-15T12:00:00",
        "latitude": -25.5,
        "longitude": 155.3,
        "measurements": [
            {
                "depth": 0,
                "temperature": 28.5,
                "salinity": 35.2,
                "pressure": 0.0,
                "oxygen": 250.0
            }
        ]
    }
    
    # Validate structure
    assert "float_id" in sample_profile
    assert "profile_date" in sample_profile
    assert "latitude" in sample_profile
    assert "longitude" in sample_profile
    assert "measurements" in sample_profile
    assert isinstance(sample_profile["measurements"], list)
    assert len(sample_profile["measurements"]) > 0
    
    measurement = sample_profile["measurements"][0]
    assert "depth" in measurement
    assert "temperature" in measurement
    assert "salinity" in measurement


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])