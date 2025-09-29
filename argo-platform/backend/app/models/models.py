from sqlalchemy import Column, String, Float, DateTime, Integer, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from datetime import datetime
import uuid
from ..core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    firebase_uid = Column(String, unique=True, index=True)
    full_name = Column(String)
    role = Column(String, default="student")  # scientist, policymaker, student, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    queries = relationship("UserQuery", back_populates="user")
    alerts = relationship("UserAlert", back_populates="user")

class ArgoFloat(Base):
    __tablename__ = "argo_floats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    float_id = Column(String, unique=True, index=True, nullable=False)
    platform_number = Column(String)
    project_name = Column(String)
    pi_name = Column(String)
    data_center = Column(String)
    deployment_date = Column(DateTime)
    status = Column(String)  # active, inactive, recovered
    location = Column(Geometry('POINT'))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    profiles = relationship("ArgoProfile", back_populates="float")

class ArgoProfile(Base):
    __tablename__ = "argo_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    float_id = Column(UUID(as_uuid=True), ForeignKey("argo_floats.id"))
    cycle_number = Column(Integer)
    profile_date = Column(DateTime, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geometry('POINT'), nullable=False)
    profile_type = Column(String)  # primary, delayed, real-time
    data_mode = Column(String)  # R (real-time), D (delayed), A (adjusted)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    float = relationship("ArgoFloat", back_populates="profiles")
    measurements = relationship("ArgoMeasurement", back_populates="profile")

class ArgoMeasurement(Base):
    __tablename__ = "argo_measurements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("argo_profiles.id"))
    pressure = Column(Float)  # dbar
    depth = Column(Float)     # meters
    temperature = Column(Float)  # Celsius
    salinity = Column(Float)     # PSU
    oxygen = Column(Float)       # μmol/kg
    ph = Column(Float)
    nitrate = Column(Float)      # μmol/kg
    quality_flag = Column(String)  # Quality control flag
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    profile = relationship("ArgoProfile", back_populates="measurements")

class SatelliteData(Base):
    __tablename__ = "satellite_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    satellite_name = Column(String, nullable=False)
    instrument = Column(String)
    data_type = Column(String)  # SST, SSH, chlorophyll, etc.
    measurement_date = Column(DateTime, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geometry('POINT'), nullable=False)
    value = Column(Float)
    unit = Column(String)
    quality_level = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class BuoyData(Base):
    __tablename__ = "buoy_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buoy_id = Column(String, nullable=False, index=True)
    buoy_type = Column(String)  # moored, drifting
    measurement_date = Column(DateTime, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geometry('POINT'), nullable=False)
    sea_surface_temperature = Column(Float)
    air_temperature = Column(Float)
    wind_speed = Column(Float)
    wind_direction = Column(Float)
    wave_height = Column(Float)
    atmospheric_pressure = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class GliderData(Base):
    __tablename__ = "glider_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    glider_id = Column(String, nullable=False, index=True)
    mission_name = Column(String)
    measurement_date = Column(DateTime, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geometry('POINT'), nullable=False)
    depth = Column(Float)
    temperature = Column(Float)
    salinity = Column(Float)
    oxygen = Column(Float)
    chlorophyll = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserQuery(Base):
    __tablename__ = "user_queries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    query_text = Column(Text, nullable=False)
    generated_sql = Column(Text)
    reasoning = Column(Text)
    execution_time = Column(Float)
    result_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="queries")

class OceanAnomaly(Base):
    __tablename__ = "ocean_anomalies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    anomaly_type = Column(String, nullable=False)  # heatwave, cold_spell, salinity_anomaly
    severity = Column(String)  # low, medium, high, extreme
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geometry('POINT'), nullable=False)
    area_affected = Column(Geometry('POLYGON'))
    description = Column(Text)
    confidence_score = Column(Float)
    data_source = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    alerts = relationship("UserAlert", back_populates="anomaly")

class UserAlert(Base):
    __tablename__ = "user_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    anomaly_id = Column(UUID(as_uuid=True), ForeignKey("ocean_anomalies.id"))
    alert_type = Column(String, nullable=False)
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    anomaly = relationship("OceanAnomaly", back_populates="alerts")

class DataEmbedding(Base):
    __tablename__ = "data_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_type = Column(String, nullable=False)  # query, description, metadata
    content_text = Column(Text, nullable=False)
    embedding_model = Column(String)
    source_table = Column(String)
    source_id = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)