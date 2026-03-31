#!/bin/bash
set -e

if ! dpkg -s msodbcsql18 >/dev/null 2>&1; then
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

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}${APP_DIR}"

cd "$APP_DIR"

echo "Starting Gunicorn from ${APP_DIR} with PYTHONPATH=${PYTHONPATH}"
exec gunicorn --bind=0.0.0.0:${PORT:-8000} \
              --workers=4 \
              --worker-class=uvicorn.workers.UvicornWorker \
              --timeout=600 \
              main:app
