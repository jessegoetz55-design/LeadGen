#!/bin/bash
# Quick run script for Harvest Platform

echo "🌾 Harvest Platform - Starting..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null

# Install dependencies if needed
if [ ! -f "venv/installed" ]; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
    touch venv/installed
fi

# Initialize database if needed
if [ ! -f "harvest.db" ]; then
    echo "🗄️ Initializing database..."
    python init_db.py
fi

# Run Streamlit
echo "🚀 Launching Streamlit app..."
streamlit run app.py
