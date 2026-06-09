import csv
import json
import time
from pathlib import Path
import requests
from django.core.management.base import BaseCommand
from api.models import FuelStation

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "FuelRouteAPI/1.0 (data import)"
CACHE_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "geocode_cache.json"


def _load_cache():
    if CACHE_FILE.exists():
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}


def _save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


def geocode_city_state(city: str, state: str, cache: dict) -> tuple[float, float] | None:
    key = f"{city}, {state}"
    if key in cache:
        return tuple(cache[key])

    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"q": key, "format": "json", "limit": 1, "countrycodes": "us"},
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data:
            lat, lon = float(data[0]["lat"]), float(data[0]["lon"])
            cache[key] = [lat, lon]
            return lat, lon
    except requests.RequestException:
        pass
    return None


class Command(BaseCommand):
    help = "Import fuel prices CSV into database with city-level geocoding"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to the fuel prices CSV file")
        parser.add_argument("--delay", type=float, default=0.3, help="Delay between geocoding requests (seconds)")
        parser.add_argument("--batch-size", type=int, default=500, help="DB batch insert size")

    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        delay = options["delay"]
        batch_size = options["batch_size"]

        FuelStation.objects.all().delete()

        rows = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append({
                    "opis_truckstop_id": int(row["OPIS Truckstop ID"]),
                    "truckstop_name": row["Truckstop Name"].strip(),
                    "address": row["Address"].strip(),
                    "city": row["City"].strip(),
                    "state": row["State"].strip(),
                    "rack_id": int(row["Rack ID"]),
                    "retail_price": float(row["Retail Price"]),
                })

        self.stdout.write(f"Loaded {len(rows)} rows")

        unique_stations = {}
        for r in rows:
            key = (r["opis_truckstop_id"], r["truckstop_name"], r["city"], r["state"], r["address"])
            if key not in unique_stations:
                unique_stations[key] = r

        self.stdout.write(f"Unique stations: {len(unique_stations)}")

        geocode_cache = _load_cache()
        city_state_coords = {}
        new_geocoded = 0

        for key, r in unique_stations.items():
            cs_key = (r["city"], r["state"])
            if cs_key not in city_state_coords:
                coords = geocode_city_state(r["city"], r["state"], geocode_cache)
                city_state_coords[cs_key] = coords
                if coords:
                    new_geocoded += 1
                if new_geocoded % 10 == 0 and new_geocoded > 0:
                    _save_cache(geocode_cache)
                    self.stdout.write(f"  Geocoded {new_geocoded} cities...")
                time.sleep(delay)

        _save_cache(geocode_cache)
        self.stdout.write(f"Geocoded {new_geocoded} unique cities")
        self.stdout.write("Importing into database...")

        bulk = []
        for key, r in unique_stations.items():
            coords = city_state_coords.get((r["city"], r["state"]))
            lat, lon = coords if coords else (None, None)
            bulk.append(FuelStation(
                opis_truckstop_id=r["opis_truckstop_id"],
                truckstop_name=r["truckstop_name"],
                address=r["address"],
                city=r["city"],
                state=r["state"],
                rack_id=r["rack_id"],
                retail_price=r["retail_price"],
                latitude=lat,
                longitude=lon,
            ))

        for i in range(0, len(bulk), batch_size):
            FuelStation.objects.bulk_create(bulk[i:i+batch_size], ignore_conflicts=True)

        total = FuelStation.objects.count()
        with_coords = FuelStation.objects.filter(latitude__isnull=False).count()
        self.stdout.write(self.style.SUCCESS(
            f"Imported {total} stations ({with_coords} with coordinates, {total - with_coords} without)"
        ))
