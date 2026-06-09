import re
import time
import requests
from django.core.cache import cache

NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "FuelRouteAPI/1.0 (educational project)"


def _sanitize(key):
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", key)


def geocode_location(location_name: str) -> tuple[float, float] | None:
    cache_key = _sanitize(f"geocode:{location_name.lower().strip()}")
    cached = cache.get(cache_key)
    if cached:
        return cached

    params = {
        "q": location_name,
        "format": "json",
        "limit": 1,
        "countrycodes": "us",
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        resp = requests.get(NOMINATIM_BASE_URL, params=params, headers=headers, timeout=10)
        if resp.status_code == 429:
            time.sleep(1)
            resp = requests.get(NOMINATIM_BASE_URL, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        result = (lat, lon)
        cache.set(cache_key, result, 86400 * 30)
        return result
    except requests.RequestException:
        return None
