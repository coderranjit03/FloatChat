import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

# Configuration
API_BASE_URL = "http://backend:8001/api"

st.set_page_config(
    page_title="ARGO Oceanographic Platform - Prototype",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_user(email, password):
    """Simple login function"""
    try:
        response = requests.post(f"{API_BASE_URL}/auth/login", 
                               json={"email": email, "password": password})
        if response.status_code == 200:
            data = response.json()
            st.session_state.user = data['user']
            st.session_state.logged_in = True
            return True
        return False
    except:
        # Fallback for demo
        if "scientist" in email:
            st.session_state.user = {
                "id": "demo_scientist",
                "email": email,
                "full_name": "Dr. Ocean Scientist",
                "role": "scientist"
            }
        elif "policy" in email:
            st.session_state.user = {
                "id": "demo_policy",
                "email": email,
                "full_name": "Policy Maker",
                "role": "policy_maker"
            }
        else:
            st.session_state.user = {
                "id": "demo_student",
                "email": email,
                "full_name": "Marine Student",
                "role": "student"
            }
        st.session_state.logged_in = True
        return True

def make_api_request(endpoint):
    """Make API request with fallback data"""
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    
    # Fallback sample data
    if endpoint == "dashboard":
        return {
            "total_floats": 15,
            "active_floats": 12,
            "total_profiles": 145,
            "recent_anomalies": 3,
            "coverage_stats": {"pacific": 45.2, "atlantic": 32.8, "indian": 22.0}
        }
    elif endpoint == "floats":
        return {
            "floats": [
                {"id": 1, "float_id": "ARGO_1001", "platform_number": "1001", "project_name": "Global Ocean Monitoring", "status": "active", "latitude": 145.5, "longitude": -25.3},
                {"id": 2, "float_id": "ARGO_1002", "platform_number": "1002", "project_name": "Pacific Climate Study", "status": "active", "latitude": 175.2, "longitude": -35.7},
                {"id": 3, "float_id": "ARGO_1003", "platform_number": "1003", "project_name": "Atlantic Research", "status": "active", "latitude": -45.8, "longitude": 20.1}
            ]
        }
    elif endpoint == "profiles":
        return {
            "profiles": [
                {"float_id": "ARGO_1001", "ocean_temperature": 18.5, "salinity": 35.2, "pressure": 10.0, "latitude": 145.6, "longitude": -25.4},
                {"float_id": "ARGO_1002", "ocean_temperature": 16.8, "salinity": 34.8, "pressure": 15.0, "latitude": 175.3, "longitude": -35.8},
                {"float_id": "ARGO_1003", "ocean_temperature": 22.1, "salinity": 36.5, "pressure": 5.0, "latitude": -45.7, "longitude": 20.2}
            ]
        }
    return {}

def query_api(query_text):
    """Send natural language query to API"""
    try:
        response = requests.post(f"{API_BASE_URL}/query", 
                               json={"query": query_text, "include_explanation": True})
        if response.status_code == 200:
            return response.json()
    except:
        pass
    
    # Fallback response
    return {
        "sql_query": "SELECT * FROM argo_floats WHERE status = 'active'",
        "results": [
            {"float_id": "ARGO_1001", "temperature": 18.5, "salinity": 35.2},
            {"float_id": "ARGO_1002", "temperature": 16.8, "salinity": 34.8}
        ],
        "explanation": f"Demo response for query: '{query_text}' - This shows how the system would process your natural language request.",
        "confidence_score": 0.85,
        "execution_time": 0.12
    }

# Login Page
if not st.session_state.logged_in:
    st.title("🌊 ARGO Oceanographic Data Platform")
    st.subheader("Prototype Login")
    
    st.info("""
    **Demo Credentials:**
    - Scientist: scientist@argo.com (any password)
    - Policy Maker: policy@argo.com (any password) 
    - Student: student@argo.com (any password)
    """)
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if login_user(email, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Login failed")

# Main Application
else:
    # Header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("🌊 ARGO Platform - Prototype")
    with col2:
        st.write(f"👋 Welcome, {st.session_state.user['full_name']}")
    with col3:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()
    
    # Sidebar Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Select Page", [
        "Dashboard", 
        "Natural Language Query", 
        "Data Explorer", 
        "Visualization", 
        "About"
    ])
    
    # Dashboard Page
    if page == "Dashboard":
        st.header("📊 Platform Dashboard")
        
        # Get dashboard data
        dashboard_data = make_api_request("dashboard")
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Floats", dashboard_data.get("total_floats", 0))
        with col2:
            st.metric("Active Floats", dashboard_data.get("active_floats", 0))
        with col3:
            st.metric("Profiles", dashboard_data.get("total_profiles", 0))
        with col4:
            st.metric("Anomalies", dashboard_data.get("recent_anomalies", 0))
        
        # Coverage stats
        if "coverage_stats" in dashboard_data:
            st.subheader("Ocean Coverage")
            coverage_df = pd.DataFrame([
                {"Ocean": "Pacific", "Coverage": dashboard_data["coverage_stats"]["pacific"]},
                {"Ocean": "Atlantic", "Coverage": dashboard_data["coverage_stats"]["atlantic"]},
                {"Ocean": "Indian", "Coverage": dashboard_data["coverage_stats"]["indian"]}
            ])
            fig = px.bar(coverage_df, x="Ocean", y="Coverage", title="Coverage by Ocean Basin (%)")
            st.plotly_chart(fig, use_container_width=True)
    
    # Natural Language Query Page
    elif page == "Natural Language Query":
        st.header("🗣️ Ask Questions in Natural Language")
        
        st.info("""
        **Try asking questions like:**
        - "Show me ocean temperature data"
        - "What anomalies have been detected?"
        - "List all active floats"
        - "Find salinity measurements"
        """)
        
        query_text = st.text_input("Ask a question about ocean data:", 
                                 placeholder="e.g., Show me recent temperature anomalies in the Pacific")
        
        if st.button("Submit Query") and query_text:
            with st.spinner("Processing your query..."):
                result = query_api(query_text)
                
                if result:
                    st.success(f"Query processed in {result.get('execution_time', 0):.2f} seconds")
                    
                    # Show explanation
                    st.subheader("🧠 Query Understanding")
                    st.write(result.get("explanation", ""))
                    st.write(f"**Confidence Score:** {result.get('confidence_score', 0):.1%}")
                    
                    # Show generated SQL
                    with st.expander("Generated SQL Query"):
                        st.code(result.get("sql_query", ""), language="sql")
                    
                    # Show results
                    if result.get("results"):
                        st.subheader("📋 Results")
                        df = pd.DataFrame(result["results"])
                        st.dataframe(df, use_container_width=True)
                        
                        # Simple visualization if numeric data exists
                        numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
                        if len(numeric_columns) > 0:
                            st.subheader("📈 Quick Visualization")
                            if len(numeric_columns) >= 2:
                                x_col = st.selectbox("X-axis", numeric_columns)
                                y_col = st.selectbox("Y-axis", numeric_columns)
                                fig = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
                                st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("No results found for your query.")
    
    # Data Explorer
    elif page == "Data Explorer":
        st.header("🔍 Data Explorer")
        
        tab1, tab2, tab3 = st.tabs(["ARGO Floats", "Ocean Profiles", "Anomalies"])
        
        with tab1:
            st.subheader("ARGO Float Network")
            floats_data = make_api_request("floats")
            if floats_data.get("floats"):
                df = pd.DataFrame(floats_data["floats"])
                st.dataframe(df, use_container_width=True)
        
        with tab2:
            st.subheader("Ocean Measurement Profiles") 
            profiles_data = make_api_request("profiles")
            if profiles_data.get("profiles"):
                df = pd.DataFrame(profiles_data["profiles"])
                st.dataframe(df, use_container_width=True)
        
        with tab3:
            st.subheader("Detected Anomalies")
            try:
                anomalies_data = make_api_request("anomalies")
                if anomalies_data.get("anomalies"):
                    df = pd.DataFrame(anomalies_data["anomalies"])
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No anomalies detected recently.")
            except:
                st.info("Anomaly detection system is offline in prototype mode.")
    
    # Visualization Page  
    elif page == "Visualization":
        st.header("📈 Data Visualizations")
        
        # Get sample data
        profiles_data = make_api_request("profiles")
        
        if profiles_data.get("profiles"):
            df = pd.DataFrame(profiles_data["profiles"])
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'ocean_temperature' in df.columns:
                    fig1 = px.histogram(df, x='ocean_temperature', 
                                      title='Ocean Temperature Distribution',
                                      nbins=20)
                    st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                if 'salinity' in df.columns:
                    fig2 = px.histogram(df, x='salinity',
                                      title='Salinity Distribution', 
                                      nbins=20)
                    st.plotly_chart(fig2, use_container_width=True)
            
            # Map visualization
            if 'latitude' in df.columns and 'longitude' in df.columns:
                st.subheader("🗺️ Float Locations")
                fig3 = px.scatter_mapbox(df, lat='latitude', lon='longitude',
                                       hover_data=['float_id', 'ocean_temperature', 'salinity'],
                                       zoom=1, height=600,
                                       title="ARGO Float Measurement Locations")
                fig3.update_layout(mapbox_style="open-street-map")
                st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Loading visualization data...")
    
    # About Page
    elif page == "About":
        st.header("ℹ️ About This Prototype")
        
        st.markdown("""
        ## ARGO Oceanographic Data Platform - Prototype
        
        This is a **simplified prototype** demonstrating the core concepts of a next-generation 
        oceanographic data platform with AI-powered natural language querying.
        
        ### Key Features Demonstrated:
        - 🗣️ **Natural Language Queries**: Ask questions in plain English
        - 📊 **Interactive Dashboards**: Role-based data views
        - 🔍 **Data Explorer**: Browse oceanographic datasets  
        - 📈 **Visualizations**: Interactive charts and maps
        - 🔐 **Role-Based Access**: Different views for scientists, policy makers, students
        
        ### Technology Stack:
        - **Backend**: FastAPI with SQLite database
        - **Frontend**: Streamlit for rapid prototyping
        - **Visualization**: Plotly for interactive charts
        
        ### Production Features (Not in Prototype):
        - Full PostgreSQL + PostGIS database
        - Advanced AI/ML models for anomaly detection
        - Real-time data ingestion from ARGO network
        - Comprehensive authentication & authorization
        - Scalable microservices architecture
        - Advanced vector search capabilities
        
        ### Demo Data:
        This prototype uses sample ARGO data to demonstrate functionality.
        In production, this would connect to real-time oceanographic data sources.
        
        ---
        **Note**: This is a functional prototype showing the platform's potential.
        The full production system would include enterprise-grade security, 
        real-time data processing, and advanced AI capabilities.
        """)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**ARGO Platform Prototype v1.0**")
st.sidebar.markdown("🌊 Oceanographic Data Discovery")