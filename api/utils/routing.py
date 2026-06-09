import re
import requests
from django.core.cache import cache

OSRM_BASE_URL = "https://router.project-osrm.org"


def _sanitize(key):
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", key)


def get_route(start_coords: tuple[float, float], finish_coords: tuple[float, float]) -> dict | None:
    cache_key = _sanitize(f"route:{start_coords}:{finish_coords}")
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"{OSRM_BASE_URL}/route/v1/driving/{start_coords[1]},{start_coords[0]};{finish_coords[1]},{finish_coords[0]}"
    params = {
        "overview": "full",
        "geometries": "polyline6",
        "steps": "true",
        "alternatives": "false",
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "Ok" or not data.get("routes"):
            return None
        route = data["routes"][0]
        cache.set(cache_key, route, 86400 * 7)
        return route
    except requests.RequestException:
        return None


def decode_polyline(encoded: str, precision: int = 6) -> list[tuple[float, float]]:
    scale = 10 ** precision
    coords = []
    index = 0
    lat = 0
    lng = 0

    while index < len(encoded):
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat

        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        dlng = ~(result >> 1) if (result & 1) else (result >> 1)
        lng += dlng

        coords.append((lat / scale, lng / scale))

    return coords
