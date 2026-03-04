"""Cross-layer correlation engine.

Executes pattern-matching queries across the knowledge graph to find
intelligence-relevant relationships between different data layers.
Creates correlation edges and CorrelationAlert audit trail nodes.
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from ..utils import haversine_km

logger = logging.getLogger("worldview-ingestion")


def _calc_confidence(distance_km: float, time_delta_min: float, frp: float = 0) -> str:
    """Calculate correlation confidence level."""
    if distance_km < 10 and time_delta_min < 10 and frp > 100:
        return "high"
    elif distance_km < 25 and time_delta_min < 20:
        return "medium"
    return "low"


def _create_alert(
    graph,
    rule_type: str,
    confidence: str,
    summary: str,
    source_entities: dict,
    thresholds: dict,
    data_sources: list[str],
) -> str:
    """Create a CorrelationAlert node in the graph. Returns alert id."""
    alert_id = f"corr_{uuid.uuid4().hex[:12]}"
    detected_at = int(datetime.now(timezone.utc).timestamp() * 1000)

    graph.query(
        """
        CREATE (a:CorrelationAlert {
            id: $id,
            ruleType: $ruleType,
            confidence: $confidence,
            summary: $summary,
            detectedAt: $detectedAt,
            sourceEntities: $sourceEntities,
            thresholds: $thresholds,
            dataSources: $dataSources,
            acknowledged: false
        })
        """,
        {
            "id": alert_id,
            "ruleType": rule_type,
            "confidence": confidence,
            "summary": summary,
            "detectedAt": detected_at,
            "sourceEntities": json.dumps(source_entities),
            "thresholds": json.dumps(thresholds),
            "dataSources": json.dumps(data_sources),
        },
    )
    return alert_id


def _rule_aircraft_thermal(graph) -> int:
    """Rule 1: Military aircraft within 50km of high-FRP nighttime thermal anomaly
    within 30-minute window.

    Uses Python-side haversine to avoid FalkorDB cross-product performance issues.
    """
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    one_hour_ago = now_ms - 3_600_000
    one_day_ago = now_ms - 86_400_000

    # Fetch recent military aircraft
    aircraft_result = graph.query(
        """
        MATCH (a:Aircraft)
        WHERE a.isMilitary = true AND a.lastSeen > $since
        RETURN a.hex, a.callsign, a.operator, a.lastLat, a.lastLon, a.lastSeen
        """,
        {"since": one_hour_ago},
    )

    # Fetch recent high-FRP nighttime hotspots
    hotspot_result = graph.query(
        """
        MATCH (t:ThermalAnomaly)
        WHERE t.daynight = 'N' AND t.confidence = 'h' AND t.frp > 50
          AND t.timestamp > $since
        RETURN t.id, t.latitude, t.longitude, t.frp, t.timestamp
        """,
        {"since": one_day_ago},
    )

    if not aircraft_result.result_set or not hotspot_result.result_set:
        return 0

    correlations_found = 0

    for ac_row in aircraft_result.result_set:
        ac_hex, ac_cs, ac_op, ac_lat, ac_lon, ac_seen = ac_row

        for hs_row in hotspot_result.result_set:
            hs_id, hs_lat, hs_lon, hs_frp, hs_ts = hs_row

            # Distance check (50km threshold)
            dist_km = haversine_km(ac_lat, ac_lon, hs_lat, hs_lon)
            if dist_km > 50:
                continue

            # Time check (30 min = 1,800,000 ms)
            time_delta_ms = abs(ac_seen - hs_ts)
            if time_delta_ms > 1_800_000:
                continue

            time_delta_min = time_delta_ms / 60_000

            # Check if correlation already exists
            existing = graph.query(
                """
                MATCH (a:Aircraft {hex: $hex})-[:PROXIMATE_TO]->(t:ThermalAnomaly {id: $tid})
                RETURN count(*) AS cnt
                """,
                {"hex": ac_hex, "tid": hs_id},
            )
            if existing.result_set and existing.result_set[0][0] > 0:
                continue

            confidence = _calc_confidence(dist_km, time_delta_min, hs_frp)

            # Create PROXIMATE_TO edge
            detected_at = int(datetime.now(timezone.utc).timestamp() * 1000)
            graph.query(
                """
                MATCH (a:Aircraft {hex: $hex}), (t:ThermalAnomaly {id: $tid})
                CREATE (a)-[:PROXIMATE_TO {
                    distance_km: $dist,
                    time_delta_min: $tdelta,
                    confidence: $conf,
                    detected_at: $dat
                }]->(t)
                """,
                {
                    "hex": ac_hex,
                    "tid": hs_id,
                    "dist": round(dist_km, 2),
                    "tdelta": round(time_delta_min, 1),
                    "conf": confidence,
                    "dat": detected_at,
                },
            )

            # Create audit trail alert
            summary = (
                f"Aircraft {ac_cs or ac_hex} ({ac_op or 'unknown'}) "
                f"within {dist_km:.1f}km of thermal anomaly "
                f"(FRP={hs_frp}MW) — {confidence} confidence"
            )
            _create_alert(
                graph,
                rule_type="aircraft_thermal_proximity",
                confidence=confidence,
                summary=summary,
                source_entities={
                    "aircraft_hex": ac_hex,
                    "aircraft_callsign": ac_cs or "",
                    "aircraft_operator": ac_op or "",
                    "anomaly_id": hs_id,
                    "anomaly_frp": hs_frp,
                },
                thresholds={
                    "max_distance_km": 50,
                    "max_time_delta_min": 30,
                    "min_frp_mw": 50,
                    "required_daynight": "N",
                    "required_confidence": "h",
                },
                data_sources=["Airplanes.live ADS-B", "NASA FIRMS VIIRS"],
            )

            correlations_found += 1
            logger.info(f"CORRELATION: {summary}")

    return correlations_found


def _rule_thermal_conflict(graph) -> int:
    """Rule 2: Thermal anomaly within 100km of GDELT conflict event
    within 2-hour window.

    Uses Python-side haversine for geo filtering.
    """
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    one_day_ago = now_ms - 86_400_000

    # Fetch recent thermal anomalies
    thermal_result = graph.query(
        """
        MATCH (t:ThermalAnomaly)
        WHERE t.timestamp > $since
        RETURN t.id, t.latitude, t.longitude, t.frp, t.timestamp
        """,
        {"since": one_day_ago},
    )

    # Fetch recent conflict events
    conflict_result = graph.query(
        """
        MATCH (c:ConflictEvent)
        WHERE c.eventType = 'conflict' AND c.timestamp > $since
        RETURN c.id, c.name, c.latitude, c.longitude, c.timestamp
        """,
        {"since": one_day_ago},
    )

    if not thermal_result.result_set or not conflict_result.result_set:
        return 0

    correlations_found = 0

    for t_row in thermal_result.result_set:
        t_id, t_lat, t_lon, t_frp, t_ts = t_row

        for c_row in conflict_result.result_set:
            c_id, c_name, c_lat, c_lon, c_ts = c_row

            # Distance check (100km threshold)
            dist_km = haversine_km(t_lat, t_lon, c_lat, c_lon)
            if dist_km > 100:
                continue

            # Time check (2 hours = 7,200,000 ms)
            time_delta_ms = abs(t_ts - c_ts)
            if time_delta_ms > 7_200_000:
                continue

            time_delta_min = time_delta_ms / 60_000

            # Check if correlation already exists
            existing = graph.query(
                """
                MATCH (t:ThermalAnomaly {id: $tid})-[:CORRELATED_WITH]->(c:ConflictEvent {id: $cid})
                RETURN count(*) AS cnt
                """,
                {"tid": t_id, "cid": c_id},
            )
            if existing.result_set and existing.result_set[0][0] > 0:
                continue

            confidence = "medium"
            if dist_km < 25 and time_delta_min < 30:
                confidence = "high"
            elif dist_km > 75 or time_delta_min > 90:
                confidence = "low"

            # Create CORRELATED_WITH edge
            detected_at = int(datetime.now(timezone.utc).timestamp() * 1000)
            graph.query(
                """
                MATCH (t:ThermalAnomaly {id: $tid}), (c:ConflictEvent {id: $cid})
                CREATE (t)-[:CORRELATED_WITH {
                    distance_km: $dist,
                    time_delta_min: $tdelta,
                    confidence: $conf,
                    detected_at: $dat
                }]->(c)
                """,
                {
                    "tid": t_id,
                    "cid": c_id,
                    "dist": round(dist_km, 2),
                    "tdelta": round(time_delta_min, 1),
                    "conf": confidence,
                    "dat": detected_at,
                },
            )

            # Create audit trail alert
            summary = (
                f"Thermal anomaly (FRP={t_frp}MW) "
                f"within {dist_km:.1f}km of conflict event: "
                f"{(c_name or 'unknown')[:80]} — {confidence} confidence"
            )
            _create_alert(
                graph,
                rule_type="thermal_conflict_correlation",
                confidence=confidence,
                summary=summary,
                source_entities={
                    "anomaly_id": t_id,
                    "anomaly_frp": t_frp,
                    "event_id": c_id,
                    "event_name": (c_name or "")[:100],
                },
                thresholds={
                    "max_distance_km": 100,
                    "max_time_delta_min": 120,
                    "required_event_type": "conflict",
                },
                data_sources=["NASA FIRMS VIIRS", "GDELT Project"],
            )

            correlations_found += 1
            logger.info(f"CORRELATION: {summary}")

    return correlations_found


def run_correlations(graph, _backend_url: str = "", _locations: list = None) -> dict:
    """Execute all correlation rules. Called by the periodic ingestion loop.

    Extra params (_backend_url, _locations) accepted for interface compatibility
    with the periodic runner but not used.
    """
    rule1_count = _rule_aircraft_thermal(graph)
    rule2_count = _rule_thermal_conflict(graph)

    stats = {
        "aircraft_thermal": rule1_count,
        "thermal_conflict": rule2_count,
        "total": rule1_count + rule2_count,
    }

    if stats["total"] > 0:
        logger.info(
            f"Correlation cycle: {stats['total']} new correlations "
            f"(Rule1={rule1_count}, Rule2={rule2_count})"
        )
    else:
        logger.debug("Correlation cycle: no new correlations")

    return stats
