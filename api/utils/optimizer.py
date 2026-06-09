import math
import sys
from typing import List, Tuple
from django.conf import settings
from api.models import FuelStation

EARTH_RADIUS_MI = 3958.8
SEARCH_MAX_DISTANCE_MI = 30.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return EARTH_RADIUS_MI * 2 * math.asin(math.sqrt(a))


def _build_spatial_index():
    stations = FuelStation.objects.filter(
        latitude__isnull=False, longitude__isnull=False
    ).values(
        "truckstop_name", "address", "city", "state",
        "latitude", "longitude", "retail_price"
    )
    result = []
    for s in stations:
        result.append({
            "name": s["truckstop_name"],
            "address": s["address"],
            "city": s["city"],
            "state": s["state"],
            "lat": float(s["latitude"]),
            "lon": float(s["longitude"]),
            "price": float(s["retail_price"]),
        })
    return result


STATION_CACHE = None


def get_all_stations():
    global STATION_CACHE
    if STATION_CACHE is None:
        STATION_CACHE = _build_spatial_index()
    return STATION_CACHE


def find_nearest_fuel_station(lat: float, lon: float) -> dict | None:
    stations = get_all_stations()
    best = None
    best_price = float("inf")

    for s in stations:
        d = haversine(lat, lon, s["lat"], s["lon"])
        if d <= SEARCH_MAX_DISTANCE_MI and s["price"] < best_price:
            best_price = s["price"]
            best = s

    return best


def get_nearest_fuel_station_at_point(lat: float, lon: float) -> dict | None:
    stations = get_all_stations()
    best = None
    best_price = float("inf")

    for s in stations:
        d = haversine(lat, lon, s["lat"], s["lon"])
        if d <= SEARCH_MAX_DISTANCE_MI and s["price"] < best_price:
            best_price = s["price"]
            best = {**s, "distance_mi": round(d, 2)}

    return best


def optimize_fuel_stops(
    route_coords: List[Tuple[float, float]],
    total_distance_mi: float,
) -> Tuple[List[dict], float]:
    max_range = settings.FUEL_TANK_RANGE_MILES
    mpg = settings.VEHICLE_MPG
    total_gallons = total_distance_mi / mpg

    num_stops_needed = max(0, math.ceil(total_distance_mi / max_range) - 1)

    if num_stops_needed == 0:
        avg_price = 3.50
        return [], round(total_gallons * avg_price, 2)

    segment_length = total_distance_mi / (num_stops_needed + 1)

    stations = get_all_stations()

    fuel_stops = []
    cumulative_dist = 0.0
    last_stop_segment_end = 0

    for stop_num in range(1, num_stops_needed + 1):
        target_dist = stop_num * segment_length

        search_start = int((stop_num - 1) / num_stops_needed * len(route_coords))
        search_end = int(stop_num / num_stops_needed * len(route_coords))

        best_stop = None
        best_price = float("inf")

        step = max(1, (search_end - search_start) // 100)
        idx_margin = max(1, (search_end - search_start) // 20)

        for i in range(search_start, min(search_end + idx_margin, len(route_coords)), step):
            lat, lon = route_coords[i][0], route_coords[i][1]
            for s in stations:
                d = haversine(lat, lon, s["lat"], s["lon"])
                if d <= SEARCH_MAX_DISTANCE_MI and s["price"] < best_price:
                    best_price = s["price"]
                    best_stop = {**s, "distance_from_start_mi": round(target_dist, 1)}

        if not best_stop:
            for i in range(search_start, min(search_end, len(route_coords))):
                lat, lon = route_coords[i][0], route_coords[i][1]
                for s in stations:
                    d = haversine(lat, lon, s["lat"], s["lon"])
                    if d <= SEARCH_MAX_DISTANCE_MI * 2.0 and s["price"] < best_price:
                        best_price = s["price"]
                        best_stop = {**s, "distance_from_start_mi": round(target_dist, 1)}

        if best_stop:
            leg_distance = target_dist - cumulative_dist
            gallons_needed = leg_distance / mpg
            cost = gallons_needed * best_price

            fuel_stops.append({
                "name": best_stop["name"],
                "address": best_stop["address"],
                "city": best_stop["city"],
                "state": best_stop["state"],
                "price_per_gallon": best_price,
                "latitude": best_stop["lat"],
                "longitude": best_stop["lon"],
                "distance_from_start_mi": round(target_dist, 1),
                "estimated_gallons": round(gallons_needed, 2),
                "cost": round(cost, 2),
            })
            cumulative_dist = target_dist
            last_stop_segment_end = stop_num

    if fuel_stops:
        avg_price = sum(s["price_per_gallon"] for s in fuel_stops) / len(fuel_stops)
        total_fuel_cost = round(total_gallons * avg_price, 2)
    else:
        total_fuel_cost = round(total_gallons * 3.50, 2)

    return fuel_stops, total_fuel_cost
