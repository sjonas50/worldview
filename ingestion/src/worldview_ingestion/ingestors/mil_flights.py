"""Military flight ingestor — polls /api/flights/military and writes to FalkorDB.

Creates/updates:
- Aircraft nodes (MERGE by hex, update latest state)
- OBSERVED_AT relationships to nearest Location (temporal edges)
- Operator nodes + OPERATED_BY relationships
"""

import logging
from datetime import datetime, timezone

import httpx

from ..utils import find_nearest_location

logger = logging.getLogger("worldview-ingestion")


def ingest_mil_flights(
    graph, backend_url: str, locations: list[dict]
) -> dict:
    """Fetch military flights from Express backend and write to FalkorDB.

    Returns stats dict with counts of operations performed.
    """
    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

    # Fetch from Express backend
    with httpx.Client(timeout=30) as client:
        resp = client.get(f"{backend_url}/api/flights/military")
        resp.raise_for_status()
        flights = resp.json()

    if not flights:
        logger.debug("No military flights returned from backend")
        return {"aircraft": 0, "observations": 0, "operators": 0}

    # Filter valid entries
    valid = [
        f for f in flights
        if f.get("hex") and f.get("latitude") is not None and f.get("longitude") is not None
    ]

    if not valid:
        return {"aircraft": 0, "observations": 0, "operators": 0}

    # --- Batch 1: MERGE Aircraft nodes ---
    aircraft_params = [
        {
            "hex": f["hex"],
            "callsign": f.get("callsign", "") or "",
            "registration": f.get("registration", "") or "",
            "aircraftType": f.get("aircraftType", "") or "",
            "description": f.get("description", "") or "",
            "operator": f.get("operator", "") or "",
            "isMilitary": True,
            "isLADD": bool(f.get("isLADD", False)),
            "dbFlags": f.get("dbFlags", 0),
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

    # Batch in chunks of 100
    chunk_size = 100
    for i in range(0, len(aircraft_params), chunk_size):
        chunk = aircraft_params[i : i + chunk_size]
        graph.query(
            """
            UNWIND $aircraft AS a
            MERGE (ac:Aircraft {hex: a.hex})
            SET ac.callsign = a.callsign,
                ac.registration = a.registration,
                ac.aircraftType = a.aircraftType,
                ac.description = a.description,
                ac.operator = a.operator,
                ac.isMilitary = a.isMilitary,
                ac.isLADD = a.isLADD,
                ac.dbFlags = a.dbFlags,
                ac.lastLat = a.lastLat,
                ac.lastLon = a.lastLon,
                ac.lastAlt = a.lastAlt,
                ac.lastHeading = a.lastHeading,
                ac.lastSpeed = a.lastSpeed,
                ac.lastSquawk = a.lastSquawk,
                ac.lastSeen = a.lastSeen
            """,
            {"aircraft": chunk},
        )

    # --- Batch 2: Create OBSERVED_AT edges to nearest Location ---
    observations = []
    for f in valid:
        nearest_id = find_nearest_location(
            f["latitude"], f["longitude"], locations
        )
        if nearest_id:
            observations.append({
                "hex": f["hex"],
                "locId": nearest_id,
                "lat": f["latitude"],
                "lon": f["longitude"],
                "alt": f.get("altitude", 0) or 0,
                "altFeet": f.get("altitudeFeet", 0) or 0,
                "heading": f.get("heading"),
                "speed": f.get("velocity"),
                "speedKnots": f.get("velocityKnots"),
                "squawk": f.get("squawk", "") or "",
                "timestamp": timestamp,
            })

    for i in range(0, len(observations), chunk_size):
        chunk = observations[i : i + chunk_size]
        graph.query(
            """
            UNWIND $obs AS o
            MATCH (a:Aircraft {hex: o.hex}), (l:Location {id: o.locId})
            CREATE (a)-[:OBSERVED_AT {
                lat: o.lat,
                lon: o.lon,
                alt: o.alt,
                altFeet: o.altFeet,
                heading: o.heading,
                speed: o.speed,
                speedKnots: o.speedKnots,
                squawk: o.squawk,
                timestamp: o.timestamp
            }]->(l)
            """,
            {"obs": chunk},
        )

    # --- Batch 3: MERGE Operator nodes + OPERATED_BY ---
    operators = {}
    for f in valid:
        op = (f.get("operator") or "").strip()
        if op:
            op_id = op.lower().replace(" ", "_").replace("'", "")
            operators[op_id] = op

    if operators:
        op_params = [{"id": k, "name": v} for k, v in operators.items()]
        graph.query(
            """
            UNWIND $ops AS o
            MERGE (op:Operator {id: o.id})
            SET op.name = o.name, op.type = 'military'
            """,
            {"ops": op_params},
        )

        # Link aircraft to operators
        links = []
        for f in valid:
            op = (f.get("operator") or "").strip()
            if op:
                op_id = op.lower().replace(" ", "_").replace("'", "")
                links.append({"hex": f["hex"], "opId": op_id})

        for i in range(0, len(links), chunk_size):
            chunk = links[i : i + chunk_size]
            graph.query(
                """
                UNWIND $links AS lnk
                MATCH (a:Aircraft {hex: lnk.hex}), (o:Operator {id: lnk.opId})
                MERGE (a)-[:OPERATED_BY]->(o)
                """,
                {"links": chunk},
            )

    stats = {
        "aircraft": len(valid),
        "observations": len(observations),
        "operators": len(operators),
    }
    logger.info(
        f"Ingested {stats['aircraft']} aircraft, "
        f"{stats['observations']} observations, "
        f"{stats['operators']} operators"
    )
    return stats
