"""Shared utility functions for ingestors."""

import math

# Earth radius in km for haversine
_R = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points in km."""
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return _R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def find_nearest_location(
    lat: float, lon: float, locations: list[dict], max_km: float = 500.0
) -> str | None:
    """Find the nearest seeded Location within max_km. Returns location id or None."""
    best_id = None
    best_dist = max_km

    for loc in locations:
        dist = haversine_km(lat, lon, loc["lat"], loc["lon"])
        if dist < best_dist:
            best_dist = dist
            best_id = loc["id"]

    return best_id
