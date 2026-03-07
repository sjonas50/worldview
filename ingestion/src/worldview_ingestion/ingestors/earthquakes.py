"""Earthquake ingestor — polls USGS earthquake feed and writes to FalkorDB.

Creates/updates:
- Earthquake nodes (MERGE by USGS event id)
- OCCURRED_NEAR relationships to nearest Location
"""

import logging
from datetime import datetime, timezone

import httpx

from ..utils import find_nearest_location

logger = logging.getLogger("worldview-ingestion")

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"


def ingest_earthquakes(
    graph, backend_url: str, locations: list[dict]
) -> dict:
    """Fetch earthquakes from USGS and write to FalkorDB."""
    with httpx.Client(timeout=30) as client:
        resp = client.get(USGS_URL)
        resp.raise_for_status()
        data = resp.json()

    features = data.get("features", [])
    if not features:
        logger.debug("No earthquakes returned from USGS")
        return {"earthquakes": 0, "near_locations": 0}

    # Filter valid entries with coordinates
    valid = []
    for f in features:
        props = f.get("properties", {})
        coords = f.get("geometry", {}).get("coordinates", [])
        if len(coords) >= 2 and props.get("mag") is not None:
            valid.append({
                "id": f.get("id", ""),
                "mag": props.get("mag", 0) or 0,
                "place": props.get("place", "") or "",
                "time": props.get("time", 0) or 0,
                "longitude": coords[0],
                "latitude": coords[1],
                "depth": coords[2] if len(coords) > 2 else 0,
                "type": props.get("type", "earthquake"),
                "status": props.get("status", ""),
                "tsunami": props.get("tsunami", 0),
                "sig": props.get("sig", 0) or 0,
            })

    if not valid:
        return {"earthquakes": 0, "near_locations": 0}

    # --- Batch 1: MERGE Earthquake nodes ---
    chunk_size = 100
    for i in range(0, len(valid), chunk_size):
        chunk = valid[i : i + chunk_size]
        graph.query(
            """
            UNWIND $quakes AS q
            MERGE (e:Earthquake {id: q.id})
            SET e.mag = q.mag,
                e.place = q.place,
                e.time = q.time,
                e.longitude = q.longitude,
                e.latitude = q.latitude,
                e.depth = q.depth,
                e.type = q.type,
                e.status = q.status,
                e.tsunami = q.tsunami,
                e.sig = q.sig
            """,
            {"quakes": chunk},
        )

    # --- Batch 2: MERGE OCCURRED_NEAR edges to nearest Location ---
    observations = []
    for q in valid:
        nearest_id = find_nearest_location(q["latitude"], q["longitude"], locations)
        if nearest_id:
            observations.append({
                "quakeId": q["id"],
                "locId": nearest_id,
                "timestamp": q["time"],
            })

    for i in range(0, len(observations), chunk_size):
        chunk = observations[i : i + chunk_size]
        graph.query(
            """
            UNWIND $obs AS o
            MATCH (e:Earthquake {id: o.quakeId}), (l:Location {id: o.locId})
            MERGE (e)-[:OCCURRED_NEAR {timestamp: o.timestamp}]->(l)
            """,
            {"obs": chunk},
        )

    stats = {"earthquakes": len(valid), "near_locations": len(observations)}
    logger.info(
        f"Ingested {stats['earthquakes']} earthquakes, "
        f"{stats['near_locations']} near locations"
    )
    return stats
