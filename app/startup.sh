#!/bin/bash
# Azure App Service startup script for Python application
# Uses a persistent virtual environment under /home/site/wwwroot/antenv
# so pip install only runs on first start (or after a fresh deploy with Oryx build).

set -e

VENV_DIR="/home/site/wwwroot/antenv"
APP_DIR="/home/site/wwwroot"

cd "$APP_DIR"

if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ]; then
    echo "Activating existing virtual environment..."
    source "$VENV_DIR/bin/activate"
else
    echo "No virtual environment found — creating and installing dependencies..."
    python -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    echo "Dependencies installed successfully."
fi

echo "Starting Gunicorn..."
exec gunicorn --bind=0.0.0.0:8000 \
              --workers=4 \
              --worker-class=uvicorn.workers.UvicornWorker \
              --timeout=600 \
              main:app
