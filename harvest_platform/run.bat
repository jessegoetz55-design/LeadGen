@echo off
REM Quick run script for Harvest Platform (Windows)

echo 🌾 Harvest Platform - Starting...

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist "venv\installed" (
    echo 📥 Installing dependencies...
    pip install -r requirements.txt
    echo installed > venv\installed
)

REM Initialize database if needed
if not exist "harvest.db" (
    echo 🗄️ Initializing database...
    python init_db.py
)

REM Run Streamlit
echo 🚀 Launching Streamlit app...
streamlit run app.py
