#!/usr/bin/env bash
# ==============================================================================
# Alex System Boot Script (Jarvis × Matrix × Hermes)
# Ensures Docker starts on boot, gateways run, and Alex services are active.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_DIR}"

echo "[Alex Boot] Initializing Alex operating environment..."

# 1. Ensure designated folders exist
mkdir -p storage/workspace storage/data storage/reports storage/logs

# 2. Check and start Docker if not running
if ! docker info >/dev/null 2>&1; then
    echo "[Alex Boot] Docker is not running. Launching Docker Desktop..."
    open -a Docker || true
    echo "[Alex Boot] Waiting for Docker daemon to become responsive..."
    TRIES=0
    until docker info >/dev/null 2>&1 || [ $TRIES -ge 30 ]; do
        sleep 2
        TRIES=$((TRIES + 1))
    done
fi

if docker info >/dev/null 2>&1; then
    echo "[Alex Boot] Docker is active. Starting gateway containers (FreeLLMAPI & OmniRoute)..."
    docker compose up -d || true
else
    echo "[Alex Boot] Warning: Docker daemon could not be reached. Local gateway fallback may be needed."
fi

# 3. Check / Start Matrix Middleware (Port 8700)
if ! lsof -i :8700 >/dev/null 2>&1; then
    echo "[Alex Boot] Starting Matrix Middleware on 127.0.0.1:8700..."
    nohup python3 -m matrix.api > storage/logs/matrix.log 2>&1 &
fi

# 4. Check / Start Hermes Agent (Port 8642)
if ! lsof -i :8642 >/dev/null 2>&1; then
    if command -v hermes >/dev/null 2>&1; then
        echo "[Alex Boot] Starting Hermes Agent Gateway on 127.0.0.1:8642..."
        nohup hermes gateway > storage/logs/hermes.log 2>&1 &
    else
        echo "[Alex Boot] Hermes binary not yet installed in global PATH. Skipping Hermes background start."
    fi
fi

echo "[Alex Boot] Alex services initialized successfully."
