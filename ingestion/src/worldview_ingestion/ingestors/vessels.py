"""AIS vessel ingestor — polls /api/ships and writes to FalkorDB.

Creates/updates:
- Vessel nodes (MERGE by MMSI, update latest state)
- OBSERVED_AT relationships to nearest Location (temporal edges)
"""

import logging
from datetime import datetime, timezone

import httpx

from ..utils import find_nearest_location

logger = logging.getLogger("worldview-ingestion")


def ingest_vessels(graph, backend_url: str, locations: list[dict]) -> dict:
    """Fetch AIS vessel data from Express backend and write to FalkorDB."""
    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

    with httpx.Client(timeout=30) as client:
        resp = client.get(f"{backend_url}/api/ships", params={"moving": "1"})
        resp.raise_for_status()
        ships = resp.json()

    if not ships:
        logger.debug("No vessels returned from backend")
        return {"vessels": 0, "observations": 0}

    # Filter valid entries
    valid = [
        s for s in ships
        if s.get("mmsi")
        and s.get("latitude") is not None
        and s.get("longitude") is not None
        and not (s["latitude"] == 0 and s["longitude"] == 0)
    ]

    if not valid:
        return {"vessels": 0, "observations": 0}

    # --- Batch 1: MERGE Vessel nodes ---
    vessel_params = [
        {
            "mmsi": s["mmsi"],
            "name": (s.get("name") or "")[:100],
            "imo": s.get("imo") or "",
            "callSign": s.get("callSign") or "",
            "shipType": s.get("shipType"),
            "country": s.get("country") or "",
            "countryCode": s.get("countryCode") or "",
            "length": s.get("length"),
            "width": s.get("width"),
            "destination": (s.get("destination") or "")[:100],
            "lastLat": s["latitude"],
            "lastLon": s["longitude"],
            "lastSog": s.get("sog", 0) or 0,
            "lastCog": s.get("cog"),
            "lastHeading": s.get("heading"),
            "lastSeen": timestamp,
        }
        for s in valid
    ]

    chunk_size = 100
    for i in range(0, len(vessel_params), chunk_size):
        chunk = vessel_params[i : i + chunk_size]
        graph.query(
            """
            UNWIND $vessels AS v
            MERGE (s:Vessel {mmsi: v.mmsi})
            SET s.name = v.name,
                s.imo = v.imo,
                s.callSign = v.callSign,
                s.shipType = v.shipType,
                s.country = v.country,
                s.countryCode = v.countryCode,
                s.length = v.length,
                s.width = v.width,
                s.destination = v.destination,
                s.lastLat = v.lastLat,
                s.lastLon = v.lastLon,
                s.lastSog = v.lastSog,
                s.lastCog = v.lastCog,
                s.lastHeading = v.lastHeading,
                s.lastSeen = v.lastSeen
            """,
            {"vessels": chunk},
        )

    # --- Batch 2: CREATE OBSERVED_AT edges to nearest Location ---
    observations = []
    for s in valid:
        nearest_id = find_nearest_location(s["latitude"], s["longitude"], locations)
        if nearest_id:
            observations.append({
                "mmsi": s["mmsi"],
                "locId": nearest_id,
                "lat": s["latitude"],
                "lon": s["longitude"],
                "sog": s.get("sog", 0) or 0,
                "cog": s.get("cog"),
                "heading": s.get("heading"),
                "timestamp": timestamp,
            })

    for i in range(0, len(observations), chunk_size):
        chunk = observations[i : i + chunk_size]
        graph.query(
            """
            UNWIND $obs AS o
            MATCH (v:Vessel {mmsi: o.mmsi}), (l:Location {id: o.locId})
            CREATE (v)-[:OBSERVED_AT {
                lat: o.lat,
                lon: o.lon,
                sog: o.sog,
                cog: o.cog,
                heading: o.heading,
                timestamp: o.timestamp
            }]->(l)
            """,
            {"obs": chunk},
        )

    stats = {"vessels": len(valid), "observations": len(observations)}
    logger.info(
        f"Ingested {stats['vessels']} vessels, "
        f"{stats['observations']} observations"
    )
    return stats
