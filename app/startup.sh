#!/bin/bash
# Azure App Service startup script for Python application

echo "Starting Agent Framework Application..."

# Install dependencies
echo "Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# Start the application with Gunicorn
echo "Starting Gunicorn server..."
gunicorn --bind=0.0.0.0:8000 --workers=4 --worker-class=uvicorn.workers.UvicornWorker --timeout=600 main:app