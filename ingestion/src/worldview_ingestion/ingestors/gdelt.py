"""GDELT conflict event ingestor — polls /api/gdelt and writes to FalkorDB.

Creates/updates:
- ConflictEvent nodes (MERGE by md5-hashed URL)
- REPORTED_NEAR relationships to nearest Location
"""

import hashlib
import logging
from datetime import datetime, timezone

import httpx

from ..utils import find_nearest_location

logger = logging.getLogger("worldview-ingestion")


def _classify_event(goldstein: float) -> str:
    """Classify event type by Goldstein scale (matches frontend useConflictEvents.ts)."""
    if goldstein <= -5:
        return "conflict"
    elif goldstein <= -2:
        return "tension"
    elif goldstein <= 2:
        return "diplomatic"
    else:
        return "cooperation"


def ingest_gdelt(graph, backend_url: str, locations: list[dict]) -> dict:
    """Fetch GDELT conflict events from Express backend and write to FalkorDB."""
    with httpx.Client(timeout=30) as client:
        resp = client.get(f"{backend_url}/api/gdelt")
        resp.raise_for_status()
        data = resp.json()

    features = data.get("features") or []
    if not features:
        logger.debug("No GDELT features returned from backend")
        return {"events": 0, "near_locations": 0}

    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

    # Parse and filter valid entries
    valid = []
    for feat in features:
        coords = (feat.get("geometry") or {}).get("coordinates", [0, 0])
        props = feat.get("properties") or {}
        lon, lat = coords[0], coords[1]

        # Skip zero-coordinate entries
        if lat == 0 and lon == 0:
            continue

        url = props.get("url", "") or ""
        if not url:
            continue

        goldstein = float(props.get("goldstein", 0) or 0)

        valid.append({
            "id": hashlib.md5(url.encode()).hexdigest()[:16],
            "name": (props.get("name", "") or "")[:200],
            "url": url[:500],
            "latitude": lat,
            "longitude": lon,
            "tone": float(props.get("tone", 0) or 0),
            "goldstein": goldstein,
            "domain": (props.get("domain", "") or "")[:100],
            "sourceCountry": (props.get("sourcecountry", "") or "")[:50],
            "eventType": _classify_event(goldstein),
            "timestamp": now_ms,
        })

    if not valid:
        return {"events": 0, "near_locations": 0}

    # --- Batch 1: MERGE ConflictEvent nodes ---
    chunk_size = 100
    for i in range(0, len(valid), chunk_size):
        chunk = valid[i : i + chunk_size]
        graph.query(
            """
            UNWIND $events AS e
            MERGE (c:ConflictEvent {id: e.id})
            SET c.name = e.name,
                c.url = e.url,
                c.latitude = e.latitude,
                c.longitude = e.longitude,
                c.tone = e.tone,
                c.goldstein = e.goldstein,
                c.domain = e.domain,
                c.sourceCountry = e.sourceCountry,
                c.eventType = e.eventType,
                c.timestamp = e.timestamp
            """,
            {"events": chunk},
        )

    # --- Batch 2: MERGE REPORTED_NEAR edges to nearest Location ---
    observations = []
    for e in valid:
        nearest_id = find_nearest_location(e["latitude"], e["longitude"], locations)
        if nearest_id:
            observations.append({
                "eventId": e["id"],
                "locId": nearest_id,
                "timestamp": e["timestamp"],
            })

    for i in range(0, len(observations), chunk_size):
        chunk = observations[i : i + chunk_size]
        graph.query(
            """
            UNWIND $obs AS o
            MATCH (c:ConflictEvent {id: o.eventId}), (l:Location {id: o.locId})
            MERGE (c)-[:REPORTED_NEAR {timestamp: o.timestamp}]->(l)
            """,
            {"obs": chunk},
        )

    stats = {"events": len(valid), "near_locations": len(observations)}
    logger.info(
        f"Ingested {stats['events']} conflict events, "
        f"{stats['near_locations']} near locations"
    )
    return stats
