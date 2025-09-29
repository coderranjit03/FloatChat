from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional, Any
import asyncio
import time
from datetime import datetime

# Import local modules
try:
    from core.config import settings
    from core.database import get_db, engine, Base
    from api.auth import get_current_user
    from services.data_service import DataService
    from services.alert_service import AlertService
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from ai.langchain_service import nl_to_sql, query_explainer
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback settings
    class FallbackSettings:
        app_name = "ARGO Oceanographic Data Platform"
        app_version = "1.0.0"
        backend_cors_origins = ["*"]
        debug = True
    settings = FallbackSettings()
    
    # Create fallback database function
    async def get_db():
        yield None
    
    # Create fallback functions
    async def get_current_user():
        return {"id": "demo", "role": "scientist"}
    
    class DataService:
        def __init__(self): pass
        async def get_floats(self, *args, **kwargs): return []
        async def get_profiles(self, *args, **kwargs): return []
        async def get_measurements(self, *args, **kwargs): return []
    
    class AlertService:
        def __init__(self): pass
        async def get_anomalies(self, *args, **kwargs): return []
    
    async def nl_to_sql(*args, **kwargs): 
        return "SELECT * FROM argo_floats LIMIT 10"
    
    def query_explainer(*args, **kwargs): 
        return "Demo mode - showing sample oceanographic data"

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name if settings else "ARGO Oceanographic Data Platform",
    version=settings.app_version if settings else "1.0.0",
    description="Next-generation platform for ARGO oceanographic data discovery with AI-powered natural language queries"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins if settings else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Pydantic models for API
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query about ocean data")
    user_context: Optional[Dict] = Field(default=None, description="Additional user context")
    include_explanation: bool = Field(default=True, description="Include query explanation")

class QueryResponse(BaseModel):
    query_id: str
    sql_query: str
    reasoning: str
    confidence: float
    results: List[Dict[str, Any]]
    result_count: int
    execution_time: float
    suggested_visualizations: List[str]
    explanation: Optional[str] = None

class DataPoint(BaseModel):
    latitude: float
    longitude: float
    timestamp: datetime
    measurements: Dict[str, float]
    source: str
    quality_flags: Optional[Dict[str, str]] = None

class AnomalyAlert(BaseModel):
    id: str
    anomaly_type: str
    severity: str
    location: Dict[str, float]  # lat, lon
    start_date: datetime
    end_date: Optional[datetime]
    description: str
    confidence_score: float
    data_source: str

class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    preferences: Optional[Dict] = None

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    try:
        # Create database tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Initialize services
        app.state.data_service = DataService()
        app.state.alert_service = AlertService()
        
        print("✅ Application startup completed successfully")
    except Exception as e:
        print(f"❌ Startup error: {e}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": settings.app_version if settings else "1.0.0"
    }

# Natural Language Query API
@app.post("/api/v1/query", response_model=QueryResponse)
async def natural_language_query(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Process natural language queries and return oceanographic data
    """
    start_time = time.time()
    
    try:
        # Generate SQL from natural language
        sql_result = await nl_to_sql.generate_sql(
            request.query, 
            request.user_context
        )
        
        # Execute the query
        data_service = app.state.data_service
        results = await data_service.execute_query(
            sql_result["sql"], 
            db
        )
        
        execution_time = time.time() - start_time
        
        # Generate explanation if requested
        explanation = None
        if request.include_explanation:
            explanation = await query_explainer.explain_query(
                request.query,
                sql_result["sql"],
                len(results)
            )
        
        # Log the query (background task)
        background_tasks.add_task(
            log_user_query,
            current_user.id,
            request.query,
            sql_result["sql"],
            sql_result["reasoning"],
            len(results),
            execution_time
        )
        
        return QueryResponse(
            query_id=f"q_{int(time.time())}",
            sql_query=sql_result["sql"],
            reasoning=sql_result["reasoning"],
            confidence=sql_result["confidence"],
            results=results,
            result_count=len(results),
            execution_time=execution_time,
            suggested_visualizations=sql_result["suggested_visualizations"],
            explanation=explanation
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing error: {str(e)}")

# Data retrieval endpoints
@app.get("/api/v1/data/argo-floats")
async def get_argo_floats(
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get ARGO float information"""
    try:
        data_service = app.state.data_service
        floats = await data_service.get_argo_floats(db, limit, offset, status)
        return {"floats": floats, "count": len(floats)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/data/profiles/{float_id}")
async def get_float_profiles(
    float_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get profiles for a specific float"""
    try:
        data_service = app.state.data_service
        profiles = await data_service.get_float_profiles(db, float_id, start_date, end_date)
        return {"profiles": profiles, "count": len(profiles)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/data/measurements/{profile_id}")
async def get_profile_measurements(
    profile_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get measurements for a specific profile"""
    try:
        data_service = app.state.data_service
        measurements = await data_service.get_profile_measurements(db, profile_id)
        return {"measurements": measurements, "count": len(measurements)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Anomaly detection and alerts
@app.get("/api/v1/anomalies", response_model=List[AnomalyAlert])
async def get_ocean_anomalies(
    severity: Optional[str] = None,
    anomaly_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get ocean anomalies and alerts"""
    try:
        alert_service = app.state.alert_service
        anomalies = await alert_service.get_anomalies(
            db, severity, anomaly_type, start_date, end_date
        )
        return anomalies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/anomalies/detect")
async def trigger_anomaly_detection(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Trigger anomaly detection process"""
    try:
        alert_service = app.state.alert_service
        background_tasks.add_task(alert_service.run_anomaly_detection, db)
        return {"message": "Anomaly detection started", "status": "processing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# User management
@app.get("/api/v1/user/profile", response_model=UserProfile)
async def get_user_profile(current_user = Depends(get_current_user)):
    """Get current user profile"""
    return UserProfile(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name or "",
        role=current_user.role,
        preferences={}
    )

@app.get("/api/v1/user/queries")
async def get_user_query_history(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get user's query history"""
    try:
        data_service = app.state.data_service
        queries = await data_service.get_user_queries(db, current_user.id, limit)
        return {"queries": queries, "count": len(queries)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Data ingestion endpoints (for real-time data)
@app.post("/api/v1/ingest/argo")
async def ingest_argo_data(
    data: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Ingest new ARGO data"""
    try:
        data_service = app.state.data_service
        background_tasks.add_task(data_service.ingest_argo_data, db, data)
        return {"message": f"Ingesting {len(data)} records", "status": "processing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ingest/satellite")
async def ingest_satellite_data(
    data: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Ingest new satellite data"""
    try:
        data_service = app.state.data_service
        background_tasks.add_task(data_service.ingest_satellite_data, db, data)
        return {"message": f"Ingesting {len(data)} records", "status": "processing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Semantic search
@app.post("/api/v1/search/semantic")
async def semantic_search(
    query: str,
    k: int = 5,
    current_user = Depends(get_current_user)
):
    """Perform semantic search across data descriptions and metadata"""
    try:
        from ai.langchain_service import vector_store_manager
        results = await vector_store_manager.similarity_search(query, k)
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Dashboard data endpoints
@app.get("/api/v1/dashboard/summary")
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get dashboard summary statistics"""
    try:
        data_service = app.state.data_service
        summary = await data_service.get_dashboard_summary(db, current_user.role)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/dashboard/recent-activity")
async def get_recent_activity(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get recent system activity"""
    try:
        data_service = app.state.data_service
        activity = await data_service.get_recent_activity(db, limit)
        return {"activity": activity}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
async def log_user_query(user_id: str, query_text: str, sql_query: str, reasoning: str, result_count: int, execution_time: float):
    """Log user query for analytics"""
    try:
        # This would normally save to database
        print(f"Query logged: {user_id} - {query_text[:50]}... - {result_count} results in {execution_time:.2f}s")
    except Exception as e:
        print(f"Error logging query: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)