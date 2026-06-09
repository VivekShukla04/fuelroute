#!/usr/bin/env bash
set -e

if [ $# -lt 1 ]; then
    echo "Usage: ./setup.sh /path/to/fuel-prices-for-be-assessment.csv"
    exit 1
fi

CSV_PATH="$1"

echo "=== fuelroute setup ==="

echo ""
echo "[1/4] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo ""
echo "[2/4] Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "[3/4] Importing fuel station data..."
python manage.py quick_import "$CSV_PATH"

echo ""
echo "[4/4] Starting server..."
echo ""
echo "  Open http://localhost:8000/ in your browser"
echo "  Press Ctrl+C to stop"
echo ""
python manage.py runserver 0.0.0.0:8000
