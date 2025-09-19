# FloatChat - ARGO Data Query Assistant

A Smart India Hackathon prototype that allows users to query ARGO ocean data using natural language and get interactive visualizations.

## Features

- 🌊 Natural language querying of ocean data
- 📊 Interactive visualizations (time series, depth profiles, maps)
- 🔍 AI transparency (shows generated SQL queries)
- 💬 Chat-based interface
- 📋 Raw data display

## Installation

1. Install dependencies:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

2. Run the application:
\`\`\`bash
streamlit run app.py
\`\`\`

## Sample Queries

- "Show salinity near equator in March 2023"
- "What's the temperature by depth?"
- "Show all March 2023 data"
- "Display surface water data"
- "Show deep water measurements"
- "Show data from float 1001"

## Data Structure

The prototype uses sample ARGO float data with columns:
- `float_id`: Float identifier
- `lat`, `lon`: Geographic coordinates
- `time`: Measurement timestamp
- `depth`: Measurement depth (meters)
- `temperature`: Water temperature (°C)
- `salinity`: Water salinity (PSU)

## Architecture

- **Frontend**: Streamlit chat interface
- **Backend**: SQLite database with natural language parsing
- **Visualizations**: Plotly charts and Folium maps
- **AI Features**: Query explanation and result summarization
