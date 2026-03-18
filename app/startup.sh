#!/bin/bash
# Azure App Service startup script
#
# When Oryx builds are enabled (SCM_DO_BUILD_DURING_DEPLOYMENT=true), Oryx:
#   - Installs dependencies into antenv at build time
#   - Packages antenv into output.tar.zst
#   - Extracts to /tmp/<hash>/ at runtime and activates the venv BEFORE calling this script
#
# So we must NOT unset PYTHONPATH or try to manage the venv ourselves.
# We only need to: install ODBC (system-level), append wwwroot to PYTHONPATH,
# then launch gunicorn.

set -e

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

# ── PYTHONPATH: Add app root for local module imports ────────────────────────
# Oryx has already activated the venv and set PYTHONPATH to the antenv site-packages.
# The app may run from /home/site/wwwroot (classic zip) or /tmp/<hash> (Oryx artifact).
# Detect the correct root from this script's own location.
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}${APP_DIR}"

cd "$APP_DIR"

# ── Start application ─────────────────────────────────────────────────────────
echo "Starting Gunicorn from ${APP_DIR} with PYTHONPATH=${PYTHONPATH}"
exec gunicorn --bind=0.0.0.0:${PORT:-8000} \
              --workers=4 \
              --worker-class=uvicorn.workers.UvicornWorker \
              --timeout=600 \
              main:app
