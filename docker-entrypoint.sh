#!/usr/bin/env bash
# ==============================================================================
# Alex Docker Entrypoint
# Boots Matrix Supervisor, Model Gateway, and Jarvis Web Dashboard
# ==============================================================================

set -euo pipefail

echo "=========================================================="
echo "    Starting Project Alex Container (Jarvis × Matrix)    "
echo "=========================================================="

# Ensure directories inside container exist
mkdir -p storage/data storage/reports storage/workspace storage/logs

# Initialize SQLite database if needed
python3 -c "import matrix.store; matrix.store.init_db()"

echo "[Alex] Starting Matrix Supervisor & Gateway on 0.0.0.0:8700..."
exec python3 -m uvicorn matrix.api:app --host 0.0.0.0 --port 8700
