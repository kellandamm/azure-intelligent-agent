#!/bin/bash
# Azure App Service startup script for Python application
# - Installs ODBC Driver 18 for SQL Server (system-level, once per container image)
# - Uses a persistent virtual environment under /home/site/wwwroot/antenv
#   so pip install only runs on first start (or after a fresh Oryx build).

set -e

VENV_DIR="/home/site/wwwroot/antenv"
APP_DIR="/home/site/wwwroot"

# ── Install ODBC Driver 18 (system-level, needed by pyodbc) ──────────────────
if ! dpkg -l msodbcsql18 >/dev/null 2>&1; then
    echo "Installing ODBC Driver 18 for SQL Server..."
    UBUNTU_VERSION=$(lsb_release -rs 2>/dev/null || echo "22.04")
    (
        set +e
        curl -sSL https://packages.microsoft.com/keys/microsoft.asc \
            | gpg --dearmor > /usr/share/keyrings/microsoft-prod.gpg
        curl -sSL "https://packages.microsoft.com/config/ubuntu/${UBUNTU_VERSION}/prod.list" \
            > /etc/apt/sources.list.d/mssql-release.list
        apt-get update -qq
        ACCEPT_EULA=Y apt-get install -y -qq msodbcsql18 unixodbc-dev
        echo "ODBC Driver 18 installed successfully."
    ) || echo "WARNING: ODBC Driver 18 installation failed — SQL Server connections may not work."
else
    echo "ODBC Driver 18 already installed."
fi

# ── Python virtual environment ────────────────────────────────────────────────
cd "$APP_DIR"

# Clear any inherited PYTHONPATH that may conflict with local modules
unset PYTHONPATH

if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ]; then
    echo "Activating existing virtual environment..."
    source "$VENV_DIR/bin/activate"
else
    echo "No virtual environment found — creating and installing dependencies..."
    python -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    pip install --no-cache-dir -r requirements.txt
    echo "Dependencies installed successfully."
fi

# Set PYTHONPATH so gunicorn workers can find local modules (config, utils, app, etc.)
export PYTHONPATH=/home/site/wwwroot

# ── Start application ─────────────────────────────────────────────────────────
echo "Starting Gunicorn..."
exec gunicorn --bind=0.0.0.0:${PORT:-8000} \
              --workers=4 \
              --worker-class=uvicorn.workers.UvicornWorker \
              --timeout=600 \
              main:app
