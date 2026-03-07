"""Commercial flight ingestor — polls /api/flights and writes to FalkorDB.

Creates/updates:
- Flight nodes (MERGE by icao24, update latest state)
- OBSERVED_AT relationships to nearest Location (temporal edges)

Separate from Aircraft (military) to avoid mixing data sources.
"""

import logging
from datetime import datetime, timezone

import httpx

from ..utils import find_nearest_location

logger = logging.getLogger("worldview-ingestion")


def ingest_flights(
    graph, backend_url: str, locations: list[dict]
) -> dict:
    """Fetch commercial flights from Express backend and write to FalkorDB."""
    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

    with httpx.Client(timeout=30) as client:
        resp = client.get(f"{backend_url}/api/flights")
        resp.raise_for_status()
        flights = resp.json()

    if not flights:
        logger.debug("No commercial flights returned from backend")
        return {"flights": 0, "observations": 0}

    # Filter valid entries with coordinates
    valid = [
        f for f in flights
        if f.get("icao24") and f.get("latitude") is not None and f.get("longitude") is not None
    ]

    if not valid:
        return {"flights": 0, "observations": 0}

    # --- Batch 1: MERGE Flight nodes ---
    chunk_size = 200
    flight_params = [
        {
            "icao24": f["icao24"],
            "callsign": f.get("callsign", "") or "",
            "registration": f.get("registration", "") or "",
            "aircraftType": f.get("aircraftType", "") or "",
            "description": f.get("description", "") or "",
            "operator": f.get("operator", "") or "",
            "airline": f.get("airline", "") or "",
            "originAirport": f.get("originAirport", "") or "",
            "destAirport": f.get("destAirport", "") or "",
            "lastLat": f["latitude"],
            "lastLon": f["longitude"],
            "lastAlt": f.get("altitude", 0) or 0,
            "lastHeading": f.get("heading"),
            "lastSpeed": f.get("velocity"),
            "lastSquawk": f.get("squawk", "") or "",
            "lastSeen": timestamp,
        }
        for f in valid
    ]

    for i in range(0, len(flight_params), chunk_size):
        chunk = flight_params[i : i + chunk_size]
        graph.query(
            """
            UNWIND $flights AS f
            MERGE (fl:Flight {icao24: f.icao24})
            SET fl.callsign = f.callsign,
                fl.registration = f.registration,
                fl.aircraftType = f.aircraftType,
                fl.description = f.description,
                fl.operator = f.operator,
                fl.airline = f.airline,
                fl.originAirport = f.originAirport,
                fl.destAirport = f.destAirport,
                fl.lastLat = f.lastLat,
                fl.lastLon = f.lastLon,
                fl.lastAlt = f.lastAlt,
                fl.lastHeading = f.lastHeading,
                fl.lastSpeed = f.lastSpeed,
                fl.lastSquawk = f.lastSquawk,
                fl.lastSeen = f.lastSeen
            """,
            {"flights": chunk},
        )

    # --- Batch 2: OBSERVED_AT edges to nearest Location ---
    observations = []
    for f in valid:
        nearest_id = find_nearest_location(
            f["latitude"], f["longitude"], locations
        )
        if nearest_id:
            observations.append({
                "icao24": f["icao24"],
                "locId": nearest_id,
                "lat": f["latitude"],
                "lon": f["longitude"],
                "alt": f.get("altitude", 0) or 0,
                "heading": f.get("heading"),
                "speed": f.get("velocity"),
                "timestamp": timestamp,
            })

    for i in range(0, len(observations), chunk_size):
        chunk = observations[i : i + chunk_size]
        graph.query(
            """
            UNWIND $obs AS o
            MATCH (fl:Flight {icao24: o.icao24}), (l:Location {id: o.locId})
            CREATE (fl)-[:OBSERVED_AT {
                lat: o.lat,
                lon: o.lon,
                alt: o.alt,
                heading: o.heading,
                speed: o.speed,
                timestamp: o.timestamp
            }]->(l)
            """,
            {"obs": chunk},
        )

    stats = {"flights": len(valid), "observations": len(observations)}
    logger.info(
        f"Ingested {stats['flights']} commercial flights, "
        f"{stats['observations']} observations"
    )
    return stats
