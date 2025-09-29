import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
import json
from datetime import datetime, timedelta
import time
import os
from typing import Dict, List, Any, Optional
import numpy as np

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")

# Page configuration
st.set_page_config(
    page_title="ARGO Oceanographic Data Platform",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .alert-card {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .success-card {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

class ARGOPlatformUI:
    """Main UI class for the ARGO platform"""
    
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_info' not in st.session_state:
            st.session_state.user_info = {}
        if 'access_token' not in st.session_state:
            st.session_state.access_token = None
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
    
    def make_api_request(self, endpoint: str, method: str = "GET", data: dict = None) -> dict:
        """Make authenticated API request"""
        headers = {
            "Content-Type": "application/json"
        }
        
        if st.session_state.access_token:
            headers["Authorization"] = f"Bearer {st.session_state.access_token}"
        
        try:
            url = f"{BACKEND_URL}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            else:
                response = requests.request(method, url, headers=headers, json=data)
            
            if response.status_code == 401:
                st.session_state.authenticated = False
                st.error("Authentication expired. Please log in again.")
                st.rerun()
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {str(e)}")
            return {}
    
    def login_page(self):
        """Display login page"""
        st.markdown('<div class="main-header"><h1 style="color: white; text-align: center; margin: 0;">🌊 ARGO Oceanographic Data Platform</h1></div>', unsafe_allow_html=True)
        
        st.markdown("### Welcome to the Next-Generation Ocean Data Discovery Platform")
        st.markdown("Explore oceanographic data using natural language queries and AI-powered insights.")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("#### Sign In")
            
            # Login form
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="Enter your email")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                submitted = st.form_submit_button("Sign In", use_container_width=True)
                
                if submitted:
                    if email and password:
                        try:
                            # Make login request
                            response = requests.post(
                                f"{BACKEND_URL}/api/v1/auth/login",
                                json={"email": email, "password": password}
                            )
                            
                            if response.status_code == 200:
                                data = response.json()
                                st.session_state.authenticated = True
                                st.session_state.access_token = data["access_token"]
                                st.session_state.user_info = data["user_info"]
                                st.success("Login successful!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Invalid credentials")
                        except Exception as e:
                            st.error(f"Login failed: {str(e)}")
                    else:
                        st.error("Please enter both email and password")
            
            st.markdown("---")
            st.markdown("#### Demo Accounts")
            st.info("**Scientist:** scientist@argo.com | **Policymaker:** policy@argo.com | **Student:** student@argo.com")
            st.markdown("*Use any password for demo purposes*")
    
    def main_app(self):
        """Main application interface"""
        # Sidebar
        self.render_sidebar()
        
        # Main content
        page = st.session_state.get('current_page', 'Dashboard')
        
        if page == 'Dashboard':
            self.dashboard_page()
        elif page == 'Natural Language Query':
            self.natural_language_query_page()
        elif page == 'Data Explorer':
            self.data_explorer_page()
        elif page == 'Anomaly Alerts':
            self.anomaly_alerts_page()
        elif page == 'Real-time Data':
            self.realtime_data_page()
        elif page == 'Analytics':
            self.analytics_page()
    
    def render_sidebar(self):
        """Render sidebar navigation"""
        with st.sidebar:
            # User info
            st.markdown(f"**Welcome, {st.session_state.user_info.get('full_name', 'User')}**")
            st.markdown(f"*Role: {st.session_state.user_info.get('role', 'Unknown').title()}*")
            
            if st.button("Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.access_token = None
                st.session_state.user_info = {}
                st.rerun()
            
            st.markdown("---")
            
            # Navigation
            pages = [
                "Dashboard",
                "Natural Language Query", 
                "Data Explorer",
                "Anomaly Alerts",
                "Real-time Data",
                "Analytics"
            ]
            
            for page in pages:
                if st.button(page, use_container_width=True, key=f"nav_{page}"):
                    st.session_state.current_page = page
                    st.rerun()
            
            st.markdown("---")
            
            # Quick stats
            st.markdown("### Quick Stats")
            try:
                summary = self.make_api_request("/api/v1/dashboard/summary")
                if summary:
                    st.metric("Active Floats", summary.get("active_floats", "N/A"))
                    st.metric("Recent Profiles", summary.get("recent_profiles", "N/A"))
                    st.metric("Recent Anomalies", summary.get("recent_anomalies", "N/A"))
            except:
                pass
    
    def dashboard_page(self):
        """Main dashboard page"""
        st.title("🌊 Ocean Data Dashboard")
        
        # Get dashboard data
        summary = self.make_api_request("/api/v1/dashboard/summary")
        recent_activity = self.make_api_request("/api/v1/dashboard/recent-activity")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Floats", summary.get("total_floats", 0))
        with col2:
            st.metric("Active Floats", summary.get("active_floats", 0))
        with col3:
            st.metric("Total Profiles", f"{summary.get('total_profiles', 0):,}")
        with col4:
            st.metric("Recent Anomalies", summary.get("recent_anomalies", 0))
        
        # Recent activity
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📊 Global Ocean Status")
            self.render_global_map()
        
        with col2:
            st.subheader("🔔 Recent Activity")
            if recent_activity and recent_activity.get("activity"):
                for activity in recent_activity["activity"][:5]:
                    with st.expander(f"{activity['type'].replace('_', ' ').title()}", expanded=False):
                        st.write(activity['description'])
                        st.caption(f"Time: {activity['timestamp']}")
                        if 'location' in activity:
                            loc = activity['location']
                            st.caption(f"Location: {loc['latitude']:.2f}°N, {loc['longitude']:.2f}°E")
            else:
                st.info("No recent activity")
        
        # Role-specific content
        user_role = st.session_state.user_info.get('role', 'student')
        if user_role == 'scientist':
            self.scientist_dashboard_section()
        elif user_role == 'policymaker':
            self.policymaker_dashboard_section()
        else:
            self.student_dashboard_section()
    
    def natural_language_query_page(self):
        """Natural language query interface"""
        st.title("💬 AI-Powered Ocean Data Query")
        st.markdown("Ask questions about ocean data in plain English!")
        
        # Sample queries
        st.subheader("📝 Sample Queries")
        sample_queries = [
            "Show temperature trends in the North Atlantic over the past year",
            "Find salinity anomalies near the equator",
            "What's the average temperature at 1000m depth?",
            "Show me data from ARGO float 1001",
            "Detect ocean heatwaves in the Pacific",
            "Compare surface temperatures between regions"
        ]
        
        cols = st.columns(2)
        for i, query in enumerate(sample_queries):
            with cols[i % 2]:
                if st.button(query, key=f"sample_{i}"):
                    self.process_natural_language_query(query)
        
        st.markdown("---")
        
        # Query input
        st.subheader("🔍 Ask Your Question")
        
        query_input = st.text_area(
            "Enter your question:",
            placeholder="e.g., Show me temperature profiles from the Southern Ocean in 2023",
            height=100
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Submit Query", type="primary", use_container_width=True):
                if query_input.strip():
                    self.process_natural_language_query(query_input)
                else:
                    st.error("Please enter a query")
        
        with col2:
            include_explanation = st.checkbox("Include AI explanation", value=True)
        
        # Display chat history
        if st.session_state.chat_messages:
            st.markdown("---")
            st.subheader("💭 Query History")
            
            for i, message in enumerate(reversed(st.session_state.chat_messages[-10:])):  # Last 10
                with st.expander(f"Query {len(st.session_state.chat_messages) - i}: {message['query'][:50]}...", expanded=i == 0):
                    self.display_query_results(message)
    
    def process_natural_language_query(self, query: str):
        """Process natural language query"""
        with st.spinner("🤖 Processing your query..."):
            try:
                response = self.make_api_request(
                    "/api/v1/query",
                    method="POST",
                    data={
                        "query": query,
                        "include_explanation": True
                    }
                )
                
                if response:
                    # Add to chat history
                    st.session_state.chat_messages.append({
                        "query": query,
                        "response": response,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Display results
                    st.success("✅ Query processed successfully!")
                    self.display_query_results(st.session_state.chat_messages[-1])
                else:
                    st.error("Failed to process query")
            
            except Exception as e:
                st.error(f"Error processing query: {str(e)}")
    
    def display_query_results(self, message: dict):
        """Display query results"""
        response = message["response"]
        
        # Query information
        st.markdown("**🔍 Query Analysis:**")
        st.code(response.get("sql_query", ""), language="sql")
        st.markdown(f"*Confidence: {response.get('confidence', 0):.0%} | Results: {response.get('result_count', 0)} | Time: {response.get('execution_time', 0):.2f}s*")
        
        # AI explanation
        if response.get("explanation"):
            with st.expander("🤖 AI Explanation", expanded=False):
                st.markdown(response["explanation"])
        
        # Results visualization
        results = response.get("results", [])
        if results:
            df = pd.DataFrame(results)
            
            # Determine visualization types
            suggested_viz = response.get("suggested_visualizations", [])
            
            if len(results) > 0:
                # Data table
                with st.expander("📊 Raw Data", expanded=False):
                    st.dataframe(df, use_container_width=True)
                
                # Visualizations
                col1, col2 = st.columns(2)
                
                with col1:
                    if "map" in suggested_viz and "latitude" in df.columns and "longitude" in df.columns:
                        st.markdown("**🗺️ Geographic Distribution**")
                        self.create_data_map(df)
                
                with col2:
                    if "time_series" in suggested_viz and any(col for col in df.columns if "date" in col.lower() or "time" in col.lower()):
                        st.markdown("**📈 Time Series**")
                        self.create_time_series(df)
                
                if "depth_profile" in suggested_viz and "depth" in df.columns:
                    st.markdown("**🌊 Depth Profile**")
                    self.create_depth_profile(df)
        else:
            st.warning("No data found for your query")
    
    def data_explorer_page(self):
        """Data exploration interface"""
        st.title("📊 Data Explorer")
        
        # Data source selection
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.subheader("Data Sources")
            data_source = st.selectbox(
                "Select data source:",
                ["ARGO Floats", "Satellite Data", "Buoy Data", "Glider Data"]
            )
            
            # Filters
            st.subheader("Filters")
            date_range = st.date_input(
                "Date Range",
                value=(datetime.now() - timedelta(days=30), datetime.now()),
                key="explorer_dates"
            )
            
            if data_source == "ARGO Floats":
                self.argo_explorer_filters()
        
        with col2:
            st.subheader(f"{data_source} Data")
            
            if data_source == "ARGO Floats":
                self.display_argo_explorer()
            else:
                st.info(f"{data_source} explorer coming soon!")
    
    def anomaly_alerts_page(self):
        """Anomaly alerts and detection page"""
        st.title("🚨 Ocean Anomaly Detection & Alerts")
        
        # Recent anomalies
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🔍 Recent Ocean Anomalies")
            
            # Get anomalies
            anomalies_data = self.make_api_request("/api/v1/anomalies")
            
            if anomalies_data:
                df_anomalies = pd.DataFrame(anomalies_data)
                
                if not df_anomalies.empty:
                    # Anomaly map
                    self.create_anomaly_map(df_anomalies)
                    
                    # Anomaly list
                    st.subheader("📋 Anomaly Details")
                    for _, anomaly in df_anomalies.iterrows():
                        severity_color = {
                            "low": "🟢", "medium": "🟡", 
                            "high": "🟠", "extreme": "🔴"
                        }.get(anomaly.get("severity", "low"), "⚪")
                        
                        with st.expander(f"{severity_color} {anomaly['anomaly_type'].replace('_', ' ').title()} - {anomaly['severity'].title()}"):
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.write(f"**Location:** {anomaly['location']['latitude']:.2f}°N, {anomaly['location']['longitude']:.2f}°E")
                                st.write(f"**Start Date:** {anomaly['start_date']}")
                                if anomaly.get("confidence_score"):
                                    st.write(f"**Confidence:** {anomaly['confidence_score']:.0%}")
                            with col_b:
                                st.write(f"**Description:** {anomaly['description']}")
                                st.write(f"**Data Source:** {anomaly['data_source']}")
                else:
                    st.info("No recent anomalies detected")
            else:
                st.info("Unable to load anomaly data")
        
        with col2:
            st.subheader("⚙️ Detection Controls")
            
            if st.button("🔄 Run Anomaly Detection", use_container_width=True):
                with st.spinner("Running anomaly detection..."):
                    result = self.make_api_request("/api/v1/anomalies/detect", method="POST")
                    if result:
                        st.success("Anomaly detection started!")
                    else:
                        st.error("Failed to start detection")
            
            st.markdown("---")
            st.subheader("📧 Alert Settings")
            
            # Alert preferences (mock interface)
            st.checkbox("Email alerts", value=True)
            st.selectbox("Alert severity threshold", ["Low", "Medium", "High", "Extreme"])
            st.multiselect("Anomaly types", ["Heatwave", "Cold spell", "Salinity anomaly"], default=["Heatwave"])
            
            if st.button("Save Settings", use_container_width=True):
                st.success("Alert settings saved!")
    
    def realtime_data_page(self):
        """Real-time data ingestion and monitoring"""
        st.title("⚡ Real-time Data Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📥 Data Ingestion")
            
            # Upload interface
            uploaded_file = st.file_uploader("Upload ARGO data (JSON/CSV)", type=['json', 'csv'])
            
            if uploaded_file:
                if st.button("Process Upload"):
                    with st.spinner("Processing uploaded data..."):
                        # Mock processing
                        st.success("Data processed and ingested!")
            
            st.markdown("---")
            
            # Manual data entry
            with st.expander("➕ Add Manual Entry"):
                float_id = st.text_input("Float ID")
                lat = st.number_input("Latitude", min_value=-90.0, max_value=90.0)
                lon = st.number_input("Longitude", min_value=-180.0, max_value=180.0)
                temp = st.number_input("Temperature (°C)")
                salinity = st.number_input("Salinity (PSU)")
                
                if st.button("Add Entry"):
                    st.success("Entry added to ingestion queue!")
        
        with col2:
            st.subheader("📊 Ingestion Status")
            
            # Mock real-time stats
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Records Today", "1,247", "↗️ +156")
            with col_b:
                st.metric("Processing Rate", "45/min", "↗️ +5")
            
            # Recent ingestion log
            st.subheader("📝 Recent Activity")
            activity_log = [
                "2024-01-15 14:30 - ARGO Float 1001: 50 profiles ingested",
                "2024-01-15 14:25 - Satellite SST: 1,200 measurements processed",
                "2024-01-15 14:20 - Buoy Network: Real-time update received",
                "2024-01-15 14:15 - Quality control: 15 records flagged",
                "2024-01-15 14:10 - ARGO Float 1003: Profile validation completed"
            ]
            
            for log_entry in activity_log:
                st.text(log_entry)
    
    def analytics_page(self):
        """Analytics and insights page"""
        st.title("📈 Ocean Data Analytics")
        
        # Analytics tabs
        tab1, tab2, tab3 = st.tabs(["🌡️ Temperature Trends", "🧂 Salinity Analysis", "🌊 Ocean Health"])
        
        with tab1:
            st.subheader("Global Temperature Trends")
            self.create_temperature_analytics()
        
        with tab2:
            st.subheader("Salinity Distribution Analysis")
            self.create_salinity_analytics()
        
        with tab3:
            st.subheader("Ocean Health Indicators")
            self.create_ocean_health_dashboard()
    
    def create_data_map(self, df: pd.DataFrame):
        """Create interactive map for data visualization"""
        try:
            if "latitude" in df.columns and "longitude" in df.columns:
                # Create folium map
                center_lat = df["latitude"].mean()
                center_lon = df["longitude"].mean()
                
                m = folium.Map(location=[center_lat, center_lon], zoom_start=4)
                
                # Add data points
                for _, row in df.iterrows():
                    # Create popup content
                    popup_content = "<br>".join([
                        f"{col}: {val}" for col, val in row.items() 
                        if col not in ["latitude", "longitude"] and pd.notna(val)
                    ])
                    
                    # Color by temperature if available
                    color = "blue"
                    if "temperature" in row and pd.notna(row["temperature"]):
                        temp = float(row["temperature"])
                        if temp > 25:
                            color = "red"
                        elif temp > 15:
                            color = "orange"
                        elif temp > 5:
                            color = "yellow"
                    
                    folium.CircleMarker(
                        location=[row["latitude"], row["longitude"]],
                        radius=5,
                        popup=popup_content,
                        color=color,
                        fill=True,
                        fillColor=color,
                        fillOpacity=0.7
                    ).add_to(m)
                
                # Display map
                st_folium(m, width=700, height=400)
        except Exception as e:
            st.error(f"Error creating map: {str(e)}")
    
    def render_global_map(self):
        """Render global ocean status map"""
        try:
            # Create a sample global map
            fig = go.Figure(go.Scattergeo(
                lon=np.random.uniform(-180, 180, 50),
                lat=np.random.uniform(-60, 60, 50),
                text=[f"Float {i+1000}" for i in range(50)],
                mode='markers',
                marker=dict(
                    size=8,
                    color=np.random.uniform(0, 30, 50),
                    colorscale='Viridis',
                    colorbar=dict(title="Temperature (°C)"),
                    line=dict(width=0.5, color='white')
                )
            ))
            
            fig.update_layout(
                geo=dict(
                    projection_type='natural earth',
                    showland=True,
                    landcolor='lightgray',
                    showocean=True,
                    oceancolor='lightblue'
                ),
                height=400,
                margin=dict(l=0, r=0, t=0, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error rendering global map: {str(e)}")
    
    def scientist_dashboard_section(self):
        """Dashboard section for scientists"""
        st.markdown("---")
        st.subheader("🔬 Scientist Dashboard")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Data Quality Metrics**")
            st.metric("Quality Controlled Records", "85%", "↗️ +2%")
            st.metric("Recent Validations", "1,247", "↗️ +156")
        
        with col2:
            st.markdown("**🔍 Research Tools**")
            if st.button("Export Dataset", use_container_width=True):
                st.success("Dataset export initiated!")
            if st.button("Create Analysis Report", use_container_width=True):
                st.success("Analysis report queued!")
    
    def policymaker_dashboard_section(self):
        """Dashboard section for policymakers"""
        st.markdown("---")
        st.subheader("🏛️ Policy Dashboard")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🌡️ Key Climate Indicators**")
            st.metric("Ocean Temperature Trend", "+0.2°C/decade", "↗️")
            st.metric("Sea Level Rise Rate", "+3.2mm/year", "↗️")
        
        with col2:
            st.markdown("**⚠️ Policy Alerts**")
            st.warning("Marine heatwave detected in North Pacific")
            st.info("New climate data available for Q4 2024")
    
    def student_dashboard_section(self):
        """Dashboard section for students"""
        st.markdown("---")
        st.subheader("🎓 Learning Dashboard")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📚 Educational Resources**")
            if st.button("Ocean Science Tutorial", use_container_width=True):
                st.info("Tutorial: Understanding ARGO floats and ocean measurements")
            if st.button("Data Interpretation Guide", use_container_width=True):
                st.info("Guide: How to read temperature and salinity profiles")
        
        with col2:
            st.markdown("**🎯 Practice Exercises**")
            if st.button("Practice Query 1: Temperature Trends", use_container_width=True):
                self.process_natural_language_query("Show me temperature trends in the Atlantic Ocean")
            if st.button("Practice Query 2: Depth Profiles", use_container_width=True):
                self.process_natural_language_query("What's the temperature at different depths?")

def main():
    """Main application entry point"""
    app = ARGOPlatformUI()
    
    if not st.session_state.authenticated:
        app.login_page()
    else:
        app.main_app()

if __name__ == "__main__":
    main()