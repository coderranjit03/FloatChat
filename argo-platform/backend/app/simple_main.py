from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import sqlite3
import json
from datetime import datetime
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="ARGO Oceanographic Data Platform - Prototype",
    version="1.0.0",
    description="Prototype platform for ARGO oceanographic data discovery"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class QueryRequest(BaseModel):
    query: str
    user_context: Optional[Dict] = None
    include_explanation: bool = True

class QueryResponse(BaseModel):
    sql_query: str
    results: List[Dict[str, Any]]
    explanation: str
    confidence_score: float
    execution_time: float

class DashboardData(BaseModel):
    total_floats: int
    active_floats: int
    total_profiles: int
    recent_anomalies: int
    coverage_stats: Dict[str, Any]

class User(BaseModel):
    id: str
    email: str
    full_name: str
    role: str

# Initialize SQLite database with sample data
def init_database():
    conn = sqlite3.connect('argo_platform.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS argo_floats (
            id INTEGER PRIMARY KEY,
            float_id TEXT UNIQUE,
            platform_number TEXT,
            project_name TEXT,
            pi_name TEXT,
            data_center TEXT,
            deployment_date TEXT,
            status TEXT,
            latitude REAL,
            longitude REAL,
            created_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS argo_profiles (
            id INTEGER PRIMARY KEY,
            float_id TEXT,
            profile_number INTEGER,
            cycle_number INTEGER,
            date_time TEXT,
            latitude REAL,
            longitude REAL,
            ocean_temperature REAL,
            salinity REAL,
            pressure REAL,
            created_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ocean_anomalies (
            id INTEGER PRIMARY KEY,
            float_id TEXT,
            anomaly_type TEXT,
            description TEXT,
            severity TEXT,
            latitude REAL,
            longitude REAL,
            detected_at TEXT,
            confidence REAL
        )
    ''')
    
    # Insert sample data
    sample_floats = [
        ('ARGO_1001', '1001', 'Global Ocean Monitoring', 'Dr. Ocean Smith', 'AOML', '2023-01-15', 'active', 145.5, -25.3, '2023-01-15T10:00:00'),
        ('ARGO_1002', '1002', 'Pacific Climate Study', 'Dr. Marine Johnson', 'PMEL', '2023-02-20', 'active', 175.2, -35.7, '2023-02-20T10:00:00'),
        ('ARGO_1003', '1003', 'Atlantic Research', 'Dr. Deep Waters', 'WHOI', '2023-03-10', 'active', -45.8, 20.1, '2023-03-10T10:00:00'),
    ]
    
    for float_data in sample_floats:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO argo_floats 
                (float_id, platform_number, project_name, pi_name, data_center, deployment_date, status, latitude, longitude, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', float_data)
        except:
            pass
    
    # Sample profiles
    sample_profiles = [
        ('ARGO_1001', 1, 1, '2023-01-20T12:00:00', 145.6, -25.4, 18.5, 35.2, 10.0, '2023-01-20T12:00:00'),
        ('ARGO_1002', 1, 1, '2023-02-25T12:00:00', 175.3, -35.8, 16.8, 34.8, 15.0, '2023-02-25T12:00:00'),
        ('ARGO_1003', 1, 1, '2023-03-15T12:00:00', -45.7, 20.2, 22.1, 36.5, 5.0, '2023-03-15T12:00:00'),
    ]
    
    for profile_data in sample_profiles:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO argo_profiles 
                (float_id, profile_number, cycle_number, date_time, latitude, longitude, ocean_temperature, salinity, pressure, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', profile_data)
        except:
            pass
    
    # Sample anomalies
    sample_anomalies = [
        ('ARGO_1001', 'temperature_spike', 'Unusual temperature increase detected', 'medium', 145.6, -25.4, '2023-01-25T12:00:00', 0.8),
        ('ARGO_1002', 'salinity_drop', 'Significant salinity decrease observed', 'high', 175.3, -35.8, '2023-02-28T12:00:00', 0.9),
    ]
    
    for anomaly_data in sample_anomalies:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO ocean_anomalies 
                (float_id, anomaly_type, description, severity, latitude, longitude, detected_at, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', anomaly_data)
        except:
            pass
    
    conn.commit()
    conn.close()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()

# Enhanced query processing function
def process_natural_language_query(query: str) -> tuple:
    """Convert natural language to SQL and execute"""
    query_lower = query.lower()
    
    # Temperature queries
    if any(word in query_lower for word in ["temperature", "temp", "thermal", "warm", "cold", "heat"]):
        if "high" in query_lower or "warm" in query_lower or "hot" in query_lower:
            sql = "SELECT * FROM argo_profiles WHERE ocean_temperature IS NOT NULL ORDER BY ocean_temperature DESC LIMIT 10"
            explanation = "Finding the highest/warmest ocean temperature measurements"
        elif "low" in query_lower or "cold" in query_lower or "cool" in query_lower:
            sql = "SELECT * FROM argo_profiles WHERE ocean_temperature IS NOT NULL ORDER BY ocean_temperature ASC LIMIT 10"
            explanation = "Finding the lowest/coldest ocean temperature measurements"
        else:
            sql = "SELECT float_id, ocean_temperature, latitude, longitude, date_time FROM argo_profiles WHERE ocean_temperature IS NOT NULL ORDER BY date_time DESC LIMIT 15"
            explanation = "Retrieving recent ocean temperature data from ARGO profiles"
    
    # Salinity queries
    elif any(word in query_lower for word in ["salinity", "salt", "saline"]):
        if "high" in query_lower:
            sql = "SELECT * FROM argo_profiles WHERE salinity IS NOT NULL ORDER BY salinity DESC LIMIT 10"
            explanation = "Finding areas with highest salinity levels"
        elif "low" in query_lower:
            sql = "SELECT * FROM argo_profiles WHERE salinity IS NOT NULL ORDER BY salinity ASC LIMIT 10"
            explanation = "Finding areas with lowest salinity levels"
        else:
            sql = "SELECT float_id, salinity, latitude, longitude, date_time FROM argo_profiles WHERE salinity IS NOT NULL ORDER BY date_time DESC LIMIT 15"
            explanation = "Retrieving recent salinity measurements from ARGO profiles"
    
    # Pressure/Depth queries
    elif any(word in query_lower for word in ["pressure", "depth", "deep", "shallow"]):
        if "deep" in query_lower or "high" in query_lower:
            sql = "SELECT * FROM argo_profiles WHERE pressure IS NOT NULL ORDER BY pressure DESC LIMIT 10"
            explanation = "Finding measurements from deepest locations (highest pressure)"
        else:
            sql = "SELECT float_id, pressure, ocean_temperature, salinity, date_time FROM argo_profiles WHERE pressure IS NOT NULL ORDER BY pressure DESC LIMIT 15"
            explanation = "Retrieving pressure/depth data from ARGO profiles"
    
    # Location-based queries
    elif any(word in query_lower for word in ["pacific", "atlantic", "indian", "ocean", "location", "where"]):
        sql = "SELECT float_id, latitude, longitude, project_name, status FROM argo_floats ORDER BY deployment_date DESC LIMIT 15"
        explanation = "Showing ARGO float locations and deployment information"
    
    # Anomaly queries
    elif any(word in query_lower for word in ["anomal", "unusual", "strange", "alert", "problem", "issue"]):
        if "temperature" in query_lower:
            sql = "SELECT * FROM ocean_anomalies WHERE anomaly_type LIKE '%temperature%' ORDER BY detected_at DESC LIMIT 10"
            explanation = "Retrieving temperature-related anomalies detected by the system"
        elif "salinity" in query_lower:
            sql = "SELECT * FROM ocean_anomalies WHERE anomaly_type LIKE '%salinity%' ORDER BY detected_at DESC LIMIT 10"
            explanation = "Retrieving salinity-related anomalies detected by the system"
        else:
            sql = "SELECT * FROM ocean_anomalies ORDER BY confidence DESC, detected_at DESC LIMIT 10"
            explanation = "Retrieving recent ocean anomalies detected by the system"
    
    # Float status queries
    elif any(word in query_lower for word in ["float", "buoy", "sensor", "device", "platform"]):
        if "active" in query_lower:
            sql = "SELECT * FROM argo_floats WHERE status = 'active' ORDER BY deployment_date DESC"
            explanation = "Retrieving information about currently active ARGO floats"
        elif "project" in query_lower:
            sql = "SELECT project_name, COUNT(*) as float_count, data_center FROM argo_floats GROUP BY project_name, data_center ORDER BY float_count DESC"
            explanation = "Showing ARGO float distribution by research projects"
        else:
            sql = "SELECT * FROM argo_floats ORDER BY deployment_date DESC LIMIT 10"
            explanation = "Retrieving information about ARGO floats"
    
    # Data overview queries
    elif any(word in query_lower for word in ["data", "measurement", "profile", "sample", "record"]):
        if "recent" in query_lower or "latest" in query_lower or "new" in query_lower:
            sql = "SELECT * FROM argo_profiles ORDER BY date_time DESC LIMIT 15"
            explanation = "Showing the most recent oceanographic measurements"
        else:
            sql = "SELECT COUNT(*) as total_profiles, AVG(ocean_temperature) as avg_temp, AVG(salinity) as avg_salinity FROM argo_profiles"
            explanation = "Providing summary statistics of all oceanographic data"
    
    # Scientist/Research queries
    elif any(word in query_lower for word in ["scientist", "researcher", "pi", "principal", "investigator"]):
        sql = "SELECT pi_name, project_name, COUNT(*) as float_count FROM argo_floats GROUP BY pi_name, project_name ORDER BY float_count DESC"
        explanation = "Showing research projects and principal investigators"
    
    # Time-based queries
    elif any(word in query_lower for word in ["today", "yesterday", "week", "month", "year", "recent"]):
        sql = "SELECT * FROM argo_profiles ORDER BY date_time DESC LIMIT 20"
        explanation = "Showing recent oceanographic measurements ordered by date"
    
    # Default fallback
    else:
        sql = "SELECT * FROM argo_floats LIMIT 8"
        explanation = f"Showing sample ARGO float data for query: '{query}'. Try asking about temperature, salinity, anomalies, floats, locations, or recent data!"
    
    return sql, explanation

# API Endpoints
@app.post("/api/query", response_model=QueryResponse)
async def natural_language_query(request: QueryRequest):
    """Process natural language queries about ocean data"""
    try:
        start_time = datetime.now()
        
        # Process query
        sql_query, explanation = process_natural_language_query(request.query)
        
        # Execute query
        conn = sqlite3.connect('argo_platform.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        
        # Convert to dict
        results = [dict(row) for row in rows]
        conn.close()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResponse(
            sql_query=sql_query,
            results=results,
            explanation=explanation,
            confidence_score=0.9,
            execution_time=execution_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing error: {str(e)}")

@app.get("/api/dashboard", response_model=DashboardData)
async def get_dashboard_data():
    """Get dashboard statistics"""
    try:
        conn = sqlite3.connect('argo_platform.db')
        cursor = conn.cursor()
        
        # Get stats
        cursor.execute("SELECT COUNT(*) FROM argo_floats")
        total_floats = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM argo_floats WHERE status = 'active'")
        active_floats = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM argo_profiles")
        total_profiles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ocean_anomalies")
        recent_anomalies = cursor.fetchone()[0]
        
        conn.close()
        
        return DashboardData(
            total_floats=total_floats,
            active_floats=active_floats,
            total_profiles=total_profiles,
            recent_anomalies=recent_anomalies,
            coverage_stats={
                "pacific": 45.2,
                "atlantic": 32.8,
                "indian": 22.0
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")

@app.get("/api/floats")
async def get_floats():
    """Get all ARGO floats"""
    try:
        conn = sqlite3.connect('argo_platform.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM argo_floats ORDER BY created_at DESC")
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        conn.close()
        return {"floats": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profiles")
async def get_profiles():
    """Get ocean profiles"""
    try:
        conn = sqlite3.connect('argo_platform.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM argo_profiles ORDER BY date_time DESC LIMIT 50")
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        conn.close()
        return {"profiles": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/anomalies")
async def get_anomalies():
    """Get ocean anomalies"""
    try:
        conn = sqlite3.connect('argo_platform.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ocean_anomalies ORDER BY detected_at DESC")
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        conn.close()
        return {"anomalies": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login")
async def login(credentials: dict):
    """Simple login - accepts any credentials for demo"""
    email = credentials.get("email", "")
    
    # Demo users based on email
    if "scientist" in email:
        role = "scientist"
        name = "Dr. Ocean Scientist"
    elif "policy" in email:
        role = "policy_maker"
        name = "Policy Maker"
    elif "student" in email:
        role = "student"
        name = "Marine Student"
    else:
        role = "scientist"
        name = "Demo User"
    
    return {
        "user": User(
            id=f"demo_{role}",
            email=email,
            full_name=name,
            role=role
        ),
        "access_token": f"demo_token_{role}",
        "token_type": "bearer"
    }

@app.get("/")
async def root():
    return {
        "message": "ARGO Oceanographic Data Platform - Prototype",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "query": "/api/query",
            "dashboard": "/api/dashboard", 
            "floats": "/api/floats",
            "profiles": "/api/profiles",
            "anomalies": "/api/anomalies",
            "login": "/api/auth/login"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)