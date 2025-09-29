# ARGO Oceanographic Data Platform

A next-generation platform for ARGO oceanographic data discovery with AI-powered natural language queries, real-time data ingestion, and advanced visualization capabilities.

## 🌊 Features

### Core Capabilities

- **🤖 Conversational AI**: Natural language queries converted to SQL with explainable reasoning
- **🔍 Semantic Search**: Vector database-powered contextual data retrieval
- **📊 Advanced Visualizations**: Interactive maps, time series, depth profiles, and anomaly alerts
- **⚡ Real-time Data**: Live ingestion, versioning, and traceability of oceanographic data
- **🔐 Role-based Access**: Secure authentication with Firebase/OAuth2 and role-specific dashboards
- **🚨 Anomaly Detection**: AI-powered detection of ocean events (heatwaves, anomalies) with alerts

### Multi-source Data Integration

- ARGO Float profiles and measurements
- Satellite oceanographic data (SST, SSH, chlorophyll)
- Buoy network observations
- Glider mission data
- Quality-controlled and real-time datasets

### User Roles & Dashboards

- **🔬 Scientists**: Research-focused tools with data export and analysis features
- **🏛️ Policymakers**: Climate indicators, trend analysis, and policy alerts
- **🎓 Students**: Educational resources and guided discovery tools
- **👨‍💼 Administrators**: System monitoring and user management

## 🏗️ Architecture

### Technology Stack

- **Backend**: FastAPI with async/await support
- **Frontend**: Streamlit with interactive visualizations
- **Databases**: PostgreSQL + PostGIS (geospatial), Chroma (vector), Redis (caching)
- **AI/NLP**: LangChain, Mistral LLM, HuggingFace models, RAG pipeline
- **Visualization**: Plotly, Folium, Geopandas, Leaflet
- **Security**: OAuth2, Firebase Authentication, JWT tokens
- **Infrastructure**: Docker containerization, microservices architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │     FastAPI     │    │   PostgreSQL    │
│   Frontend      │◄──►│    Backend      │◄──►│   + PostGIS     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                       ┌───────┼───────┐
                       ▼       ▼       ▼
               ┌─────────┐ ┌─────┐ ┌─────────┐
               │ Chroma  │ │Redis│ │LangChain│
               │Vector DB│ │Cache│ │AI/NLP   │
               └─────────┘ └─────┘ └─────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL with PostGIS (handled by Docker)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd argo-platform
cp .env.example .env
# Edit .env with your API keys and configuration
```

### 2. Start with Docker Compose

```bash
docker-compose up -d
```

This will start:

- PostgreSQL with PostGIS (port 5432)
- Redis cache (port 6379)
- Chroma vector database (port 8000)
- FastAPI backend (port 8001)
- Streamlit frontend (port 8501)

### 3. Access the Platform

- **Frontend**: http://localhost:8501
- **API Documentation**: http://localhost:8001/docs
- **Vector Database**: http://localhost:8000

### 4. Login with Demo Accounts

- **Scientist**: `scientist@argo.com` (any password)
- **Policymaker**: `policy@argo.com` (any password)
- **Student**: `student@argo.com` (any password)

## 🔧 Development Setup

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env

# Start individual services
# Terminal 1: Backend
cd backend && uvicorn app.main:app --reload --port 8001

# Terminal 2: Frontend
cd frontend && streamlit run streamlit_app.py --server.port 8501

# Terminal 3: Start databases with Docker
docker-compose up postgres redis chroma -d
```

### Configuration

Edit `.env` file with your credentials:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://argo_user:argo_password@localhost:5432/argo_platform

# AI Services (Optional - has fallbacks)
OPENAI_API_KEY=your_openai_key_here
MISTRAL_API_KEY=your_mistral_key_here
HUGGINGFACE_API_KEY=your_hf_key_here

# Firebase (Optional - has fallbacks)
FIREBASE_PROJECT_ID=your_project_id
# ... other Firebase configs

# JWT Security
SECRET_KEY=your_very_long_and_random_secret_key_here
```

## 📊 Usage Examples

### Natural Language Queries

```
"Show temperature trends in the North Atlantic over the past year"
"Find salinity anomalies near the equator"
"What's the average temperature at 1000m depth?"
"Show me data from ARGO float 1001"
"Detect ocean heatwaves in the Pacific"
```

### API Usage

```python
import requests

# Query ocean data
response = requests.post("http://localhost:8001/api/v1/query",
    json={
        "query": "Show surface temperature in the Pacific",
        "include_explanation": True
    },
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

data = response.json()
print(f"SQL: {data['sql_query']}")
print(f"Results: {len(data['results'])} records")
```

### Data Ingestion

```python
# Ingest new ARGO data
new_data = [{
    "float_id": "ARGO_2001",
    "profile_date": "2024-01-15T12:00:00Z",
    "latitude": -25.5,
    "longitude": 155.3,
    "measurements": [
        {"depth": 0, "temperature": 28.5, "salinity": 35.2},
        {"depth": 100, "temperature": 18.3, "salinity": 35.8}
    ]
}]

requests.post("http://localhost:8001/api/v1/ingest/argo",
    json=new_data,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

## 🔍 API Documentation

### Key Endpoints

#### Natural Language Query

- `POST /api/v1/query` - Convert natural language to SQL and execute
- `GET /api/v1/user/queries` - Get query history

#### Data Access

- `GET /api/v1/data/argo-floats` - List ARGO floats
- `GET /api/v1/data/profiles/{float_id}` - Get float profiles
- `GET /api/v1/data/measurements/{profile_id}` - Get profile measurements

#### Anomaly Detection

- `GET /api/v1/anomalies` - List ocean anomalies
- `POST /api/v1/anomalies/detect` - Trigger anomaly detection

#### Data Ingestion

- `POST /api/v1/ingest/argo` - Ingest ARGO data
- `POST /api/v1/ingest/satellite` - Ingest satellite data

#### Authentication

- `POST /api/v1/auth/login` - Login with credentials
- `POST /api/v1/auth/firebase-login` - Login with Firebase token
- `GET /api/v1/auth/me` - Get current user info

### Full API documentation available at `http://localhost:8001/docs`

## 🧪 Testing

```bash
# Run backend tests
cd backend && python -m pytest tests/

# Run frontend tests
cd frontend && python -m pytest tests/

# Test API endpoints
curl -X POST http://localhost:8001/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show recent temperature data"}'
```

## 🚀 Deployment

### Production Deployment

```bash
# Build and deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Or deploy individual services
docker build -f docker/backend.Dockerfile -t argo-backend .
docker build -f docker/frontend.Dockerfile -t argo-frontend .
```

### Environment Variables for Production

```bash
# Security
SECRET_KEY=production_secret_key_very_long_and_random
DEBUG=False

# Database (use managed database service)
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/argo_platform

# External Services
OPENAI_API_KEY=prod_openai_key
FIREBASE_PROJECT_ID=prod_firebase_project
```

## 🤝 Contributing

### Development Workflow

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

### Code Standards

- Follow PEP 8 for Python code
- Use type hints
- Add docstrings for functions and classes
- Write tests for new features
- Update documentation

### Adding New Features

1. **New Data Sources**: Add models in `backend/app/models/`, update ingestion in `services/data_service.py`
2. **AI Capabilities**: Extend `ai/langchain_service.py` with new LLM chains
3. **Visualizations**: Add components in `frontend/components/`
4. **API Endpoints**: Add routes in `backend/app/api/`

## 📈 Performance & Scaling

### Database Optimization

- PostGIS spatial indexes for geographic queries
- Redis caching for frequently accessed data
- Connection pooling and async queries
- Partitioning for large time-series data

### AI/NLP Optimization

- Vector embeddings cached in Chroma
- LLM response caching
- Batch processing for bulk operations
- Model quantization for faster inference

### Frontend Optimization

- Streamlit caching for expensive computations
- Lazy loading of large datasets
- Progressive data loading
- Optimized Plotly visualizations

## 🔧 Troubleshooting

### Common Issues

**Database Connection Issues**

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Reset database
docker-compose down -v && docker-compose up -d
```

**AI/NLP Not Working**

- Verify API keys in `.env` file
- Check Chroma vector database is accessible
- Ensure sufficient memory for LLM models

**Frontend Errors**

```bash
# Check Streamlit logs
docker-compose logs frontend

# Restart frontend
docker-compose restart frontend
```

**Performance Issues**

- Monitor database query performance
- Check Redis cache hit rates
- Scale services with Docker Compose

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **ARGO Program**: Global ocean observation system
- **Streamlit Team**: Interactive web app framework
- **FastAPI**: Modern, fast web framework for APIs
- **LangChain**: Framework for LLM applications
- **PostGIS**: Spatial database extension
- **Plotly**: Interactive visualization library

## 📞 Support

- **Documentation**: Full docs available in `/docs` folder
- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for questions and ideas
- **Email**: support@argo-platform.com

---

**Built for Smart India Hackathon 2024** 🇮🇳
_Advancing Ocean Science Through AI and Data Innovation_
