import json
import logging
import math
import re
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.cache import cache

from api.serializers import RouteRequestSerializer
from api.utils.geocoding import geocode_location
from api.utils.routing import get_route, decode_polyline
from api.utils.optimizer import optimize_fuel_stops

logger = logging.getLogger(__name__)


def _sanitize_cache_key(key):
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", key)


@api_view(["GET"])
def health_check(request):
    return Response({"status": "ok", "service": "Fuel Route API"})


@api_view(["GET", "POST"])
def plan_route(request):
    if request.method == "GET":
        serializer = RouteRequestSerializer(data=request.query_params)
    else:
        serializer = RouteRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    start = serializer.validated_data["start"]
    finish = serializer.validated_data["finish"]

    cache_key = _sanitize_cache_key(f"rp:{start.lower().strip()}:{finish.lower().strip()}")
    cached = cache.get(cache_key)
    if cached:
        return Response(cached)

    start_coords = geocode_location(f"{start}, USA")
    if not start_coords:
        return Response(
            {"error": f"Could not geocode start location: {start}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    finish_coords = geocode_location(f"{finish}, USA")
    if not finish_coords:
        return Response(
            {"error": f"Could not geocode finish location: {finish}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    route = get_route(start_coords, finish_coords)
    if not route:
        return Response(
            {"error": "Could not find a route between these locations"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    total_distance_m = route["distance"]
    total_distance_mi = total_distance_m / 1609.344
    route_geometry = route["geometry"]
    route_coords = decode_polyline(route_geometry)

    fuel_stops, total_fuel_cost = optimize_fuel_stops(route_coords, total_distance_mi)

    mpg = settings.VEHICLE_MPG
    total_gallons = total_distance_mi / mpg

    instructions = []
    try:
        for leg in route.get("legs", []):
            for step in leg.get("steps", []):
                maneuver = step.get("maneuver", {})
                instructions.append({
                    "instruction": maneuver.get("instruction", ""),
                    "distance_mi": round(step.get("distance", 0) / 1609.344, 1),
                    "name": step.get("name", ""),
                })
    except Exception:
        pass

    result = {
        "start_location": start,
        "finish_location": finish,
        "start_coordinates": [start_coords[1], start_coords[0]],
        "finish_coordinates": [finish_coords[1], finish_coords[0]],
        "total_distance_miles": round(total_distance_mi, 1),
        "total_fuel_cost": total_fuel_cost,
        "total_gallons": round(total_gallons, 2),
        "fuel_stops": fuel_stops,
        "route_geometry": route_geometry,
        "route_instructions": instructions[:30],
    }

    cache.set(cache_key, result, 86400)
    return Response(result)
