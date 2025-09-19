import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import re
import sqlite3
import io

# Configure Streamlit page
st.set_page_config(
    page_title="FloatChat - ARGO Data Query Assistant",
    page_icon="🌊",
    layout="wide"
)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'data_initialized' not in st.session_state:
    st.session_state.data_initialized = False

class ARGODataManager:
    """Manages ARGO ocean data and database operations"""
    
    def __init__(self):
        self.db_path = ":memory:"  # In-memory SQLite database
        self.setup_database()
    
    def create_sample_data(self):
        """Create sample ARGO float data"""
        np.random.seed(42)  # For reproducible data
        
        # Generate 30 sample records
        n_records = 30
        
        # Float IDs (simulate 3 different floats)
        float_ids = np.random.choice([1001, 1002, 1003], n_records)
        
        # Time range: March 2023
        start_date = datetime(2023, 3, 1)
        dates = [start_date + timedelta(days=np.random.randint(0, 31)) for _ in range(n_records)]
        
        # Latitude: focus around equator (-10 to 10 degrees)
        latitudes = np.random.uniform(-10, 10, n_records)
        
        # Longitude: Pacific Ocean region (120 to 180 degrees)
        longitudes = np.random.uniform(120, 180, n_records)
        
        # Depth: various depths (0 to 2000m)
        depths = np.random.choice([0, 10, 50, 100, 200, 500, 1000, 2000], n_records)
        
        # Temperature: realistic ocean temperatures (15-30°C at surface, decreasing with depth)
        temperatures = []
        for depth in depths:
            if depth <= 50:
                temp = np.random.uniform(25, 30)  # Warm surface water
            elif depth <= 200:
                temp = np.random.uniform(20, 25)  # Thermocline
            else:
                temp = np.random.uniform(2, 8)    # Deep water
            temperatures.append(round(temp, 2))
        
        # Salinity: realistic values (34-37 PSU)
        salinities = np.random.uniform(34.0, 37.0, n_records).round(2)
        
        data = {
            'float_id': float_ids,
            'lat': latitudes.round(4),
            'lon': longitudes.round(4),
            'time': dates,
            'depth': depths,
            'temperature': temperatures,
            'salinity': salinities
        }
        
        return pd.DataFrame(data)
    
    def setup_database(self):
        """Initialize SQLite database with sample data"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
        # Create sample data
        df = self.create_sample_data()
        
        # Store in SQLite
        df.to_sql('argo_data', self.conn, if_exists='replace', index=False)
        
        st.session_state.data_initialized = True
        return df
    
    def execute_query(self, sql_query):
        """Execute SQL query and return results"""
        try:
            df = pd.read_sql_query(sql_query, self.conn)
            return df, None
        except Exception as e:
            return None, str(e)

class NaturalLanguageParser:
    """Converts natural language queries to SQL"""
    
    def __init__(self):
        # Define query patterns and their SQL templates
        self.patterns = {
            'salinity_near_equator': {
                'keywords': ['salinity', 'equator', 'near equator'],
                'sql_template': "SELECT * FROM argo_data WHERE lat BETWEEN -5 AND 5 AND time LIKE '%2023-03%'"
            },
            'temperature_by_depth': {
                'keywords': ['temperature', 'depth'],
                'sql_template': "SELECT depth, AVG(temperature) as avg_temperature FROM argo_data GROUP BY depth ORDER BY depth"
            },
            'all_march_data': {
                'keywords': ['march', '2023', 'march 2023'],
                'sql_template': "SELECT * FROM argo_data WHERE time LIKE '%2023-03%'"
            },
            'surface_data': {
                'keywords': ['surface', 'surface water'],
                'sql_template': "SELECT * FROM argo_data WHERE depth <= 50"
            },
            'deep_water': {
                'keywords': ['deep', 'deep water'],
                'sql_template': "SELECT * FROM argo_data WHERE depth >= 500"
            },
            'float_specific': {
                'keywords': ['float'],
                'sql_template': "SELECT * FROM argo_data WHERE float_id = {float_id}"
            },
            'all_data': {
                'keywords': ['all', 'everything', 'show all'],
                'sql_template': "SELECT * FROM argo_data"
            }
        }
    
    def parse_query(self, user_query):
        """Convert natural language to SQL query"""
        user_query_lower = user_query.lower()
        
        # Check for float ID in query
        float_match = re.search(r'float\s+(\d+)', user_query_lower)
        if float_match:
            float_id = float_match.group(1)
            return f"SELECT * FROM argo_data WHERE float_id = {float_id}"
        
        # Check patterns
        for pattern_name, pattern_info in self.patterns.items():
            for keyword in pattern_info['keywords']:
                if keyword in user_query_lower:
                    return pattern_info['sql_template']
        
        # Default fallback
        return "SELECT * FROM argo_data LIMIT 10"
    
    def generate_explanation(self, user_query, sql_query):
        """Generate explanation of what the query does"""
        explanations = {
            'salinity': "Analyzing salinity measurements",
            'temperature': "Examining temperature data",
            'equator': "Filtering data near the equatorial region",
            'depth': "Grouping data by depth levels",
            'march': "Focusing on March 2023 measurements",
            'surface': "Looking at surface water data",
            'deep': "Examining deep water measurements"
        }
        
        user_query_lower = user_query.lower()
        explanation_parts = []
        
        for key, explanation in explanations.items():
            if key in user_query_lower:
                explanation_parts.append(explanation)
        
        if explanation_parts:
            return f"Query interpretation: {', '.join(explanation_parts)}"
        else:
            return "Query interpretation: Retrieving ARGO ocean data"

class VisualizationEngine:
    """Handles data visualization"""
    
    @staticmethod
    def create_time_series_plot(df):
        """Create time series visualization"""
        if 'time' not in df.columns:
            return None
        
        # Convert time to datetime if it's not already
        df['time'] = pd.to_datetime(df['time'])
        
        # Create subplots for temperature and salinity
        fig = go.Figure()
        
        # Temperature line
        fig.add_trace(go.Scatter(
            x=df['time'],
            y=df['temperature'],
            mode='lines+markers',
            name='Temperature (°C)',
            line=dict(color='red'),
            yaxis='y'
        ))
        
        # Salinity line (secondary y-axis)
        fig.add_trace(go.Scatter(
            x=df['time'],
            y=df['salinity'],
            mode='lines+markers',
            name='Salinity (PSU)',
            line=dict(color='blue'),
            yaxis='y2'
        ))
        
        # Update layout
        fig.update_layout(
            title='Ocean Data Time Series',
            xaxis_title='Date',
            yaxis=dict(title='Temperature (°C)', side='left'),
            yaxis2=dict(title='Salinity (PSU)', side='right', overlaying='y'),
            hovermode='x unified',
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_depth_profile(df):
        """Create depth profile visualization"""
        if 'depth' not in df.columns:
            return None
        
        # Group by depth and calculate averages
        depth_profile = df.groupby('depth').agg({
            'temperature': 'mean',
            'salinity': 'mean'
        }).reset_index()
        
        fig = go.Figure()
        
        # Temperature profile
        fig.add_trace(go.Scatter(
            x=depth_profile['temperature'],
            y=depth_profile['depth'],
            mode='lines+markers',
            name='Temperature (°C)',
            line=dict(color='red')
        ))
        
        # Salinity profile
        fig.add_trace(go.Scatter(
            x=depth_profile['salinity'],
            y=depth_profile['depth'],
            mode='lines+markers',
            name='Salinity (PSU)',
            line=dict(color='blue'),
            xaxis='x2'
        ))
        
        # Update layout
        fig.update_layout(
            title='Ocean Depth Profiles',
            yaxis=dict(title='Depth (m)', autorange='reversed'),
            xaxis=dict(title='Temperature (°C)', side='bottom'),
            xaxis2=dict(title='Salinity (PSU)', side='top', overlaying='x'),
            height=500
        )
        
        return fig
    
    @staticmethod
    def create_map_visualization(df):
        """Create map visualization with float locations"""
        if 'lat' not in df.columns or 'lon' not in df.columns:
            return None
        
        # Create base map centered on data
        center_lat = df['lat'].mean()
        center_lon = df['lon'].mean()
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=4,
            tiles='OpenStreetMap'
        )
        
        # Add markers for each data point
        for idx, row in df.iterrows():
            popup_text = f"""
            Float ID: {row['float_id']}<br>
            Date: {row['time']}<br>
            Depth: {row['depth']}m<br>
            Temperature: {row['temperature']}°C<br>
            Salinity: {row['salinity']} PSU
            """
            
            # Color code by temperature
            temp = row['temperature']
            if temp > 25:
                color = 'red'
            elif temp > 15:
                color = 'orange'
            else:
                color = 'blue'
            
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=8,
                popup=popup_text,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7
            ).add_to(m)
        
        return m

def generate_ai_summary(df, user_query):
    """Generate AI summary of results"""
    if df is None or df.empty:
        return "No data found for your query."
    
    summary_parts = []
    
    # Basic stats
    summary_parts.append(f"Found {len(df)} data points")
    
    # Temperature stats
    if 'temperature' in df.columns:
        avg_temp = df['temperature'].mean()
        summary_parts.append(f"Average temperature: {avg_temp:.1f}°C")
    
    # Salinity stats
    if 'salinity' in df.columns:
        avg_salinity = df['salinity'].mean()
        summary_parts.append(f"Average salinity: {avg_salinity:.1f} PSU")
    
    # Depth range
    if 'depth' in df.columns:
        depth_range = f"{df['depth'].min()}-{df['depth'].max()}m"
        summary_parts.append(f"Depth range: {depth_range}")
    
    # Time range
    if 'time' in df.columns:
        time_range = f"{df['time'].min()} to {df['time'].max()}"
        summary_parts.append(f"Time period: {time_range}")
    
    return " | ".join(summary_parts)

# Initialize components
@st.cache_resource
def initialize_components():
    data_manager = ARGODataManager()
    nl_parser = NaturalLanguageParser()
    viz_engine = VisualizationEngine()
    return data_manager, nl_parser, viz_engine

# Main Streamlit App
def main():
    st.title("🌊 FloatChat - ARGO Data Query Assistant")
    st.markdown("Ask questions about ocean data in natural language!")
    
    # Initialize components
    data_manager, nl_parser, viz_engine = initialize_components()
    
    # Sidebar with sample queries
    with st.sidebar:
        st.header("💡 Sample Queries")
        sample_queries = [
            "Show salinity near equator in March 2023",
            "What's the temperature by depth?",
            "Show all March 2023 data",
            "Display surface water data",
            "Show deep water measurements",
            "Show data from float 1001"
        ]
        
        for query in sample_queries:
            if st.button(query, key=f"sample_{query}"):
                st.session_state.messages.append({"role": "user", "content": query})
                st.rerun()
        
        st.markdown("---")
        st.markdown("**Data Info:**")
        st.markdown("- 30 sample ARGO float records")
        st.markdown("- March 2023 timeframe")
        st.markdown("- Equatorial Pacific region")
        st.markdown("- 3 different float IDs")
    
    # Chat interface
    st.header("💬 Chat Interface")
    
    # Display chat history
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                st.markdown(message["content"])
                
                # If this message has associated data, show visualizations
                if "data" in message:
                    df = message["data"]
                    
                    # Show visualizations inline in chat
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Time series plot
                        if 'time' in df.columns and len(df) > 1:
                            fig_ts = viz_engine.create_time_series_plot(df)
                            if fig_ts:
                                st.plotly_chart(fig_ts, use_container_width=True, key=f"ts_{i}")
                        
                        # Depth profile
                        if 'depth' in df.columns and len(df.groupby('depth')) > 1:
                            fig_depth = viz_engine.create_depth_profile(df)
                            if fig_depth:
                                st.plotly_chart(fig_depth, use_container_width=True, key=f"depth_{i}")
                    
                    with col2:
                        # Map visualization
                        if 'lat' in df.columns and 'lon' in df.columns:
                            map_viz = viz_engine.create_map_visualization(df)
                            if map_viz:
                                st_folium(map_viz, width=400, height=400, key=f"map_{i}")
                    
                    # Data table
                    with st.expander("📋 View Raw Data", expanded=False):
                        st.dataframe(df, use_container_width=True)
    
    # User input
    if prompt := st.chat_input("Ask about ocean data..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process query
        with st.chat_message("assistant"):
            with st.spinner("Processing your query..."):
                # Parse natural language to SQL
                sql_query = nl_parser.parse_query(prompt)
                explanation = nl_parser.generate_explanation(prompt, sql_query)
                
                # Show AI transparency
                st.markdown("### 🔍 Query Analysis")
                st.code(sql_query, language='sql')
                st.markdown(f"*{explanation}*")
                
                # Execute query
                df, error = data_manager.execute_query(sql_query)
                
                if error:
                    st.error(f"Query error: {error}")
                    response = f"Sorry, there was an error processing your query: {error}"
                    # Add assistant response without data
                    st.session_state.messages.append({"role": "assistant", "content": response})
                elif df is None or df.empty:
                    st.warning("No data found for your query.")
                    response = "No data found matching your criteria."
                    # Add assistant response without data
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    # Generate AI summary
                    summary = generate_ai_summary(df, prompt)
                    st.markdown(f"### 📊 Results Summary")
                    st.info(summary)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 📈 Data Visualization")
                        
                        # Time series plot
                        if 'time' in df.columns and len(df) > 1:
                            fig_ts = viz_engine.create_time_series_plot(df)
                            if fig_ts:
                                st.plotly_chart(fig_ts, use_container_width=True)
                        
                        # Depth profile
                        if 'depth' in df.columns and len(df.groupby('depth')) > 1:
                            fig_depth = viz_engine.create_depth_profile(df)
                            if fig_depth:
                                st.plotly_chart(fig_depth, use_container_width=True)
                    
                    with col2:
                        st.markdown("#### 🗺️ Geographic Distribution")
                        
                        # Map visualization
                        if 'lat' in df.columns and 'lon' in df.columns:
                            map_viz = viz_engine.create_map_visualization(df)
                            if map_viz:
                                st_folium(map_viz, width=400, height=400)
                    
                    # Data table in expandable section
                    with st.expander("📋 View Raw Data", expanded=False):
                        st.dataframe(df, use_container_width=True)
                    
                    response = f"Found {len(df)} records. {summary}"
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response,
                        "data": df  # Store dataframe for chat history visualization
                    })

if __name__ == "__main__":
    main()
