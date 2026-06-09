# fuelroute

Optimize fuel stops along any US route. Enter start and destination cities — get a map, recommended fuel stops, and total cost.

**Vehicle**: 500 mi range, 10 MPG. Fuel prices from real US truck stop data.

## Quick Start

```bash
# 1. Clone or download this project
cd fuel_route_api

# 2. Create virtual environment & install dependencies
python3 -m venv venv
source venv/bin/activate      # Linux/Mac
# venv\Scripts\activate       # Windows

pip install -r requirements.txt

# 3. Import fuel station data
python manage.py quick_import /path/to/fuel-prices-for-be-assessment.csv

# 4. Start the server
python manage.py runserver 0.0.0.0:8000

# 5. Open in browser
#    http://localhost:8000/
```

## Usage

1. Open `http://localhost:8000/`
2. Enter start city (e.g. `New York, NY`) and destination (e.g. `Los Angeles, CA`)
3. Click **Plan Route**
4. Wait ~10 seconds for the first request (geocoding + routing APIs), then results appear

### API

```bash
curl "http://localhost:8000/api/route/?start=New+York,+NY&finish=Los+Angeles,+CA"
```

Returns JSON with route distance, fuel stops, cost, and map geometry.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| "No such table" / database error | Run `python manage.py quick_import ...` |
| "Network error" in browser | Make sure the server is running on port 8000 |
| Map tiles not loading | Server needs internet for OpenStreetMap tiles |
| Slow first request | First run caches geocoding + routing; ~10s normal |
| `CacheKeyWarning` | Ignore — local cache works fine despite warning |

## Notes

- Uses **OSRM** (free) for routing and **Nominatim** (free) for geocoding
- Station coordinates are approximate (state/city centers) — sufficient for route planning
- All geocoding, routing, and route results are cached (24h+) for speed
