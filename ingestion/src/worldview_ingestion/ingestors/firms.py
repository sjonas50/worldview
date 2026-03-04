"""FIRMS thermal anomaly ingestor — polls /api/firms and writes to FalkorDB.

Creates/updates:
- ThermalAnomaly nodes (MERGE by deterministic id)
- DETECTED_NEAR relationships to nearest Location
"""

import logging
from datetime import datetime, timezone

import httpx

from ..utils import find_nearest_location

logger = logging.getLogger("worldview-ingestion")


def ingest_firms(graph, backend_url: str, locations: list[dict]) -> dict:
    """Fetch FIRMS hotspots from Express backend and write to FalkorDB."""
    with httpx.Client(timeout=30) as client:
        resp = client.get(f"{backend_url}/api/firms")
        resp.raise_for_status()
        hotspots = resp.json()

    if not hotspots:
        logger.debug("No FIRMS hotspots returned from backend")
        return {"hotspots": 0, "near_locations": 0}

    # Filter valid entries
    valid = [
        h for h in hotspots
        if h.get("latitude") is not None
        and h.get("longitude") is not None
        and (h.get("frp") or 0) > 0
    ]

    if not valid:
        return {"hotspots": 0, "near_locations": 0}

    # Generate deterministic ids for dedup across poll cycles
    for h in valid:
        h["id"] = (
            f"firms_{h['latitude']:.4f}_{h['longitude']:.4f}"
            f"_{h.get('acq_date', '')}_{h.get('acq_time', '')}"
        )

    # --- Batch 1: MERGE ThermalAnomaly nodes ---
    params = [
        {
            "id": h["id"],
            "latitude": h["latitude"],
            "longitude": h["longitude"],
            "brightness": h.get("brightness", 0) or 0,
            "frp": h.get("frp", 0) or 0,
            "confidence": h.get("confidence", "l") or "l",
            "acq_date": h.get("acq_date", "") or "",
            "acq_time": h.get("acq_time", "") or "",
            "satellite": h.get("satellite", "") or "",
            "daynight": h.get("daynight", "D") or "D",
            "timestamp": h.get("timestamp", 0) or 0,
        }
        for h in valid
    ]

    chunk_size = 100
    for i in range(0, len(params), chunk_size):
        chunk = params[i : i + chunk_size]
        graph.query(
            """
            UNWIND $hotspots AS h
            MERGE (t:ThermalAnomaly {id: h.id})
            SET t.latitude = h.latitude,
                t.longitude = h.longitude,
                t.brightness = h.brightness,
                t.frp = h.frp,
                t.confidence = h.confidence,
                t.acq_date = h.acq_date,
                t.acq_time = h.acq_time,
                t.satellite = h.satellite,
                t.daynight = h.daynight,
                t.timestamp = h.timestamp
            """,
            {"hotspots": chunk},
        )

    # --- Batch 2: MERGE DETECTED_NEAR edges to nearest Location ---
    observations = []
    for h in valid:
        nearest_id = find_nearest_location(h["latitude"], h["longitude"], locations)
        if nearest_id:
            observations.append({
                "anomalyId": h["id"],
                "locId": nearest_id,
                "timestamp": h.get("timestamp", 0) or 0,
            })

    for i in range(0, len(observations), chunk_size):
        chunk = observations[i : i + chunk_size]
        graph.query(
            """
            UNWIND $obs AS o
            MATCH (t:ThermalAnomaly {id: o.anomalyId}), (l:Location {id: o.locId})
            MERGE (t)-[:DETECTED_NEAR {timestamp: o.timestamp}]->(l)
            """,
            {"obs": chunk},
        )

    stats = {"hotspots": len(valid), "near_locations": len(observations)}
    logger.info(
        f"Ingested {stats['hotspots']} hotspots, "
        f"{stats['near_locations']} near locations"
    )
    return stats
