"""
Sample data generator for ARGO platform
Generates realistic oceanographic data for testing and demonstration
"""

import json
import random
from datetime import datetime, timedelta
import numpy as np


class ARGODataGenerator:
    """Generate sample ARGO oceanographic data"""
    
    def __init__(self):
        self.float_ids = [f"ARGO_{1000 + i}" for i in range(20)]
        self.regions = {
            "north_atlantic": {"lat": (40, 60), "lon": (-60, -10)},
            "south_atlantic": {"lat": (-40, -10), "lon": (-50, 10)},
            "north_pacific": {"lat": (20, 50), "lon": (120, 180)},
            "south_pacific": {"lat": (-50, -20), "lon": (120, 180)},
            "indian_ocean": {"lat": (-40, 20), "lon": (40, 120)},
            "southern_ocean": {"lat": (-70, -40), "lon": (-180, 180)}
        }
    
    def generate_argo_profiles(self, num_profiles: int = 100) -> list:
        """Generate ARGO profile data"""
        profiles = []
        
        for _ in range(num_profiles):
            # Random region
            region_name = random.choice(list(self.regions.keys()))
            region = self.regions[region_name]
            
            # Random float
            float_id = random.choice(self.float_ids)
            
            # Random date in the last year
            profile_date = datetime.now() - timedelta(days=random.randint(0, 365))
            
            # Random location within region
            latitude = random.uniform(region["lat"][0], region["lat"][1])
            longitude = random.uniform(region["lon"][0], region["lon"][1])
            
            # Generate measurements for this profile
            measurements = self.generate_measurements()
            
            profile = {
                "float_id": float_id,
                "platform_number": float_id.split("_")[1],
                "profile_date": profile_date.isoformat(),
                "latitude": round(latitude, 4),
                "longitude": round(longitude, 4),
                "cycle_number": random.randint(1, 200),
                "profile_type": "primary",
                "data_mode": random.choice(["R", "D"]),
                "project_name": f"{region_name.replace('_', ' ').title()} Study",
                "measurements": measurements
            }
            
            profiles.append(profile)
        
        return profiles
    
    def generate_measurements(self) -> list:
        """Generate depth measurements for a profile"""
        measurements = []
        depths = [0, 10, 20, 30, 50, 75, 100, 125, 150, 200, 250, 300, 400, 500, 600, 750, 1000, 1250, 1500, 1750, 2000]
        
        for depth in depths:
            # Realistic temperature profile
            if depth <= 50:
                temperature = random.uniform(20, 30)  # Warm surface water
            elif depth <= 200:
                temperature = random.uniform(10, 20)  # Thermocline
            elif depth <= 1000:
                temperature = random.uniform(4, 12)   # Intermediate water
            else:
                temperature = random.uniform(1, 5)    # Deep water
            
            # Realistic salinity
            if depth <= 100:
                salinity = random.uniform(34.5, 36.5)  # Surface salinity
            else:
                salinity = random.uniform(34.0, 35.0)  # Deep salinity
            
            # Oxygen (decreases with depth generally)
            if depth <= 100:
                oxygen = random.uniform(200, 300)  # High surface oxygen
            elif depth <= 500:
                oxygen = random.uniform(100, 200)  # Oxygen minimum zone
            else:
                oxygen = random.uniform(150, 250)  # Deep water oxygen
            
            measurement = {
                "depth": depth,
                "pressure": depth * 1.02,  # Approximate pressure
                "temperature": round(temperature, 2),
                "salinity": round(salinity, 2),
                "oxygen": round(oxygen, 1),
                "quality_flag": random.choice(["1", "1", "1", "2", "3"])  # Mostly good quality
            }
            
            measurements.append(measurement)
        
        return measurements
    
    def generate_satellite_data(self, num_records: int = 500) -> list:
        """Generate satellite oceanographic data"""
        satellites = ["MODIS-Aqua", "MODIS-Terra", "VIIRS-SNPP", "Sentinel-3A", "Sentinel-3B"]
        data_types = ["SST", "chlorophyll", "sea_level_anomaly"]
        
        records = []
        
        for _ in range(num_records):
            # Random global location
            latitude = random.uniform(-70, 70)
            longitude = random.uniform(-180, 180)
            
            # Random recent date
            measurement_date = datetime.now() - timedelta(days=random.randint(0, 30))
            
            satellite = random.choice(satellites)
            data_type = random.choice(data_types)
            
            # Generate realistic values based on data type
            if data_type == "SST":
                value = random.uniform(-2, 35)  # Sea surface temperature
                unit = "Celsius"
            elif data_type == "chlorophyll":
                value = random.uniform(0.1, 10.0)  # Chlorophyll concentration
                unit = "mg/m^3"
            else:  # sea_level_anomaly
                value = random.uniform(-0.5, 0.5)  # Sea level anomaly
                unit = "meters"
            
            record = {
                "satellite_name": satellite,
                "instrument": satellite.split("-")[0],
                "data_type": data_type,
                "measurement_date": measurement_date.isoformat(),
                "latitude": round(latitude, 4),
                "longitude": round(longitude, 4),
                "value": round(value, 2),
                "unit": unit,
                "quality_level": random.choice(["L2", "L3"])
            }
            
            records.append(record)
        
        return records
    
    def generate_buoy_data(self, num_records: int = 200) -> list:
        """Generate buoy oceanographic data"""
        records = []
        
        for _ in range(num_records):
            # Random ocean location
            latitude = random.uniform(-60, 60)
            longitude = random.uniform(-180, 180)
            
            # Random recent date
            measurement_date = datetime.now() - timedelta(hours=random.randint(0, 24*7))
            
            record = {
                "buoy_id": f"BUOY_{random.randint(10000, 99999)}",
                "buoy_type": random.choice(["moored", "drifting"]),
                "measurement_date": measurement_date.isoformat(),
                "latitude": round(latitude, 4),
                "longitude": round(longitude, 4),
                "sea_surface_temperature": round(random.uniform(0, 35), 2),
                "air_temperature": round(random.uniform(-10, 40), 2),
                "wind_speed": round(random.uniform(0, 25), 1),
                "wind_direction": random.randint(0, 360),
                "wave_height": round(random.uniform(0, 8), 1),
                "atmospheric_pressure": round(random.uniform(980, 1030), 1)
            }
            
            records.append(record)
        
        return records
    
    def save_sample_data(self, output_dir: str = "sample_data"):
        """Generate and save sample data files"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate ARGO data
        print("Generating ARGO profile data...")
        argo_data = self.generate_argo_profiles(100)
        with open(f"{output_dir}/argo_profiles.json", "w") as f:
            json.dump(argo_data, f, indent=2)
        
        # Generate satellite data
        print("Generating satellite data...")
        satellite_data = self.generate_satellite_data(500)
        with open(f"{output_dir}/satellite_data.json", "w") as f:
            json.dump(satellite_data, f, indent=2)
        
        # Generate buoy data
        print("Generating buoy data...")
        buoy_data = self.generate_buoy_data(200)
        with open(f"{output_dir}/buoy_data.json", "w") as f:
            json.dump(buoy_data, f, indent=2)
        
        print(f"Sample data saved to {output_dir}/")
        print(f"- ARGO profiles: {len(argo_data)} records")
        print(f"- Satellite data: {len(satellite_data)} records")
        print(f"- Buoy data: {len(buoy_data)} records")


def main():
    """Generate sample data"""
    generator = ARGODataGenerator()
    generator.save_sample_data()


if __name__ == "__main__":
    main()