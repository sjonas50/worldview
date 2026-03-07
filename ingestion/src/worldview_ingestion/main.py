"""WorldView OSINT Ingestion Service.

FastAPI application that polls the Express backend for OSINT data
and writes it into a FalkorDB knowledge graph with cross-layer correlations.

Start with: uvicorn worldview_ingestion.main:app --host 0.0.0.0 --port 8000
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel as PydanticBaseModel

from .config import Settings
from .db import get_graph
from .schema import create_constraints, initialize_indices
from .seed.locations import load_all_locations, seed_locations
from .ingestors.mil_flights import ingest_mil_flights
from .ingestors.flights import ingest_flights
from .ingestors.firms import ingest_firms
from .ingestors.gdelt import ingest_gdelt
from .ingestors.vessels import ingest_vessels
from .ingestors.earthquakes import ingest_earthquakes
from .correlations.engine import run_correlations
from .graphrag_service import GraphRAGService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("worldview-ingestion")

settings = Settings()

# Cached location data for nearest-location lookups
_locations: list[dict] = []


async def _run_periodic(
    name: str,
    func,
    interval: int,
    graph_args: tuple,
    locations: list[dict],
):
    """Run an ingestor function on a fixed interval with error backoff."""
    await asyncio.sleep(5)  # startup delay

    consecutive_errors = 0
    max_backoff = 300

    while True:
        try:
            graph = get_graph(*graph_args)
            stats = await asyncio.to_thread(
                func, graph, settings.backend_url, locations
            )
            consecutive_errors = 0
            logger.debug(f"[{name}] cycle complete: {stats}")
        except Exception as e:
            consecutive_errors += 1
            backoff = min(interval * (2 ** consecutive_errors), max_backoff)
            logger.error(
                f"[{name}] error #{consecutive_errors}: {e}. "
                f"Retry in {backoff}s"
            )
            await asyncio.sleep(backoff)
            continue

        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init schema, seed locations, start ingestion loops."""
    global _locations

    logger.info(
        f"Connecting to FalkorDB at {settings.falkordb_host}:{settings.falkordb_port} "
        f"graph={settings.falkordb_graph}"
    )

    graph = get_graph(
        settings.falkordb_host, settings.falkordb_port, settings.falkordb_graph
    )

    # Initialize schema (idempotent) — indices must exist before constraints
    logger.info("Initializing schema...")
    initialize_indices(graph)
    create_constraints(
        settings.falkordb_host, settings.falkordb_port, settings.falkordb_graph
    )

    # Seed location data
    logger.info("Seeding location data...")
    _locations = load_all_locations()
    await asyncio.to_thread(seed_locations, graph, _locations)

    # Initialize GraphRAG service (non-blocking)
    graphrag = GraphRAGService(settings)
    app.state.graphrag = graphrag
    try:
        initialized = await asyncio.to_thread(graphrag.initialize)
        if initialized:
            logger.info("GraphRAG service ready")
        else:
            logger.warning("GraphRAG service not initialized (check LLM_API_KEY)")
    except Exception as e:
        logger.warning(f"GraphRAG init deferred: {e}")

    # Start background ingestion loops (each with its own interval)
    graph_args = (
        settings.falkordb_host,
        settings.falkordb_port,
        settings.falkordb_graph,
    )

    tasks = [
        asyncio.create_task(
            _run_periodic("mil_flights", ingest_mil_flights,
                          settings.mil_flight_poll_interval, graph_args, _locations)
        ),
        asyncio.create_task(
            _run_periodic("vessels", ingest_vessels,
                          settings.vessel_poll_interval, graph_args, _locations)
        ),
        asyncio.create_task(
            _run_periodic("firms", ingest_firms,
                          settings.firms_poll_interval, graph_args, _locations)
        ),
        asyncio.create_task(
            _run_periodic("gdelt", ingest_gdelt,
                          settings.gdelt_poll_interval, graph_args, _locations)
        ),
        asyncio.create_task(
            _run_periodic("earthquakes", ingest_earthquakes,
                          settings.earthquake_poll_interval, graph_args, _locations)
        ),
        asyncio.create_task(
            _run_periodic("flights", ingest_flights,
                          settings.flight_poll_interval, graph_args, _locations)
        ),
        asyncio.create_task(
            _run_periodic("correlations", run_correlations,
                          settings.correlation_interval, graph_args, _locations)
        ),
    ]

    # Session cleanup task for GraphRAG
    async def _cleanup_graphrag_sessions():
        while True:
            await asyncio.sleep(300)
            app.state.graphrag.cleanup_sessions()

    tasks.append(asyncio.create_task(_cleanup_graphrag_sessions()))

    logger.info(
        f"Started {len(tasks) - 1} ingestion loops + GraphRAG session cleaner "
        f"(mil={settings.mil_flight_poll_interval}s, "
        f"flights={settings.flight_poll_interval}s, "
        f"vessels={settings.vessel_poll_interval}s, "
        f"firms={settings.firms_poll_interval}s, "
        f"gdelt={settings.gdelt_poll_interval}s, "
        f"earthquakes={settings.earthquake_poll_interval}s, "
        f"correlations={settings.correlation_interval}s)"
    )

    yield  # App is running

    # Shutdown
    logger.info("Shutting down ingestion loops...")
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


app = FastAPI(
    title="WorldView OSINT Ingestion",
    description="Knowledge graph ingestion service for the WorldView OSINT platform",
    version="0.3.0",
    lifespan=lifespan,
)


# ─── Health & Stats ────────────────────────────────────────────


@app.get("/health")
async def health():
    """Health check with FalkorDB connectivity test."""
    try:
        graph = get_graph(
            settings.falkordb_host, settings.falkordb_port, settings.falkordb_graph
        )
        result = graph.query("MATCH (a:Aircraft) RETURN count(a) AS cnt")
        aircraft_count = result.result_set[0][0] if result.result_set else 0
        status = "ok"
    except Exception as e:
        aircraft_count = -1
        status = f"error: {e}"

    return {
        "status": status,
        "graph": settings.falkordb_graph,
        "aircraft_nodes": aircraft_count,
    }


@app.get("/stats")
async def stats():
    """Graph statistics — node and relationship counts."""
    try:
        graph = get_graph(
            settings.falkordb_host, settings.falkordb_port, settings.falkordb_graph
        )

        result = graph.query(
            """
            OPTIONAL MATCH (a:Aircraft)
            WITH count(a) AS aircraft
            OPTIONAL MATCH (fl:Flight)
            WITH aircraft, count(fl) AS flights
            OPTIONAL MATCH (l:Location)
            WITH aircraft, flights, count(l) AS locations
            OPTIONAL MATCH (o:Operator)
            WITH aircraft, flights, locations, count(o) AS operators
            OPTIONAL MATCH (t:ThermalAnomaly)
            WITH aircraft, flights, locations, operators, count(t) AS hotspots
            OPTIONAL MATCH (c:ConflictEvent)
            WITH aircraft, flights, locations, operators, hotspots, count(c) AS events
            OPTIONAL MATCH (v:Vessel)
            WITH aircraft, flights, locations, operators, hotspots, events, count(v) AS vessels
            OPTIONAL MATCH (e:Earthquake)
            WITH aircraft, flights, locations, operators, hotspots, events, vessels, count(e) AS earthquakes
            OPTIONAL MATCH (ca:CorrelationAlert)
            WITH aircraft, flights, locations, operators, hotspots, events, vessels, earthquakes, count(ca) AS correlations
            OPTIONAL MATCH (qa:QueryAudit)
            RETURN aircraft, flights, locations, operators, hotspots, events, vessels, earthquakes, correlations, count(qa) AS queries
            """
        )
        row = result.result_set[0] if result.result_set else [0] * 10

        return {
            "aircraft": row[0],
            "flights": row[1],
            "locations": row[2],
            "operators": row[3],
            "hotspots": row[4],
            "events": row[5],
            "vessels": row[6],
            "earthquakes": row[7],
            "correlations": row[8],
            "queries": row[9],
        }
    except Exception as e:
        return {"error": str(e)}


# ─── Correlation Alerts ────────────────────────────────────────


@app.get("/correlations")
async def get_correlations(since: int = 0, limit: int = 50):
    """Return recent correlation alerts for the frontend IntelFeed."""
    try:
        graph = get_graph(
            settings.falkordb_host, settings.falkordb_port, settings.falkordb_graph
        )
        result = graph.query(
            """
            MATCH (a:CorrelationAlert)
            WHERE a.detectedAt > $since
            RETURN a.id, a.ruleType, a.confidence, a.summary, a.detectedAt
            ORDER BY a.detectedAt DESC
            LIMIT $limit
            """,
            {"since": since, "limit": limit},
        )
        alerts = []
        for row in result.result_set:
            alerts.append({
                "id": row[0],
                "ruleType": row[1],
                "confidence": row[2],
                "summary": row[3],
                "detectedAt": row[4],
            })
        return {"alerts": alerts}
    except Exception as e:
        return {"error": str(e), "alerts": []}


# ─── GraphRAG Natural Language Query ──────────────────────────


class QueryRequest(PydanticBaseModel):
    query: str
    session_id: str | None = None


@app.post("/query")
async def natural_language_query(request: QueryRequest):
    """Natural language OSINT query against the knowledge graph."""
    graphrag: GraphRAGService = app.state.graphrag
    result = await asyncio.to_thread(
        graphrag.query, request.query, request.session_id
    )
    return result


@app.get("/query/status")
async def query_status():
    """Check if GraphRAG is initialized and ready."""
    graphrag: GraphRAGService = app.state.graphrag
    return {
        "initialized": graphrag.is_initialized,
        "model": settings.llm_model if graphrag.is_initialized else None,
        "enabled": settings.graphrag_enabled,
    }


# ─── Timeline & Trajectory ────────────────────────────────────


@app.get("/timeline")
async def get_timeline(
    since: int = 0,
    until: int = 0,
    entity_type: str | None = None,
    limit: int = 100,
):
    """Return a timeline of graph events for the UI scrubber.

    Aggregates: CorrelationAlert, ThermalAnomaly, ConflictEvent timestamps.
    """
    try:
        graph = get_graph(
            settings.falkordb_host, settings.falkordb_port, settings.falkordb_graph
        )

        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        if until == 0:
            until = now_ms
        if since == 0:
            since = until - 86_400_000  # Default: last 24 hours

        events = []

        # Correlation alerts
        if entity_type is None or entity_type == "correlation":
            result = graph.query(
                """
                MATCH (a:CorrelationAlert)
                WHERE a.detectedAt >= $since AND a.detectedAt <= $until
                RETURN 'correlation' AS type, a.id AS id, a.summary AS summary,
                       a.detectedAt AS timestamp, a.confidence AS detail
                ORDER BY a.detectedAt DESC
                LIMIT $limit
                """,
                {"since": since, "until": until, "limit": limit},
            )
            for row in result.result_set:
                events.append({
                    "type": row[0], "id": row[1], "summary": row[2],
                    "timestamp": row[3], "detail": row[4],
                })

        # Thermal anomalies
        if entity_type is None or entity_type == "thermal":
            result = graph.query(
                """
                MATCH (t:ThermalAnomaly)
                WHERE t.timestamp >= $since AND t.timestamp <= $until
                RETURN 'thermal' AS type, t.id AS id,
                       t.daynight AS summary,
                       t.timestamp AS timestamp, t.confidence AS detail
                ORDER BY t.timestamp DESC
                LIMIT $limit
                """,
                {"since": since, "until": until, "limit": limit},
            )
            for row in result.result_set:
                events.append({
                    "type": row[0], "id": row[1], "summary": row[2],
                    "timestamp": row[3], "detail": row[4],
                })

        # Conflict events
        if entity_type is None or entity_type == "conflict":
            result = graph.query(
                """
                MATCH (c:ConflictEvent)
                WHERE c.timestamp >= $since AND c.timestamp <= $until
                RETURN 'conflict' AS type, c.id AS id, c.name AS summary,
                       c.timestamp AS timestamp, c.eventType AS detail
                ORDER BY c.timestamp DESC
                LIMIT $limit
                """,
                {"since": since, "until": until, "limit": limit},
            )
            for row in result.result_set:
                events.append({
                    "type": row[0], "id": row[1], "summary": row[2],
                    "timestamp": row[3], "detail": row[4],
                })

        # Earthquakes
        if entity_type is None or entity_type == "earthquake":
            result = graph.query(
                """
                MATCH (e:Earthquake)
                WHERE e.time >= $since AND e.time <= $until
                RETURN 'earthquake' AS type, e.id AS id, e.place AS summary,
                       e.time AS timestamp, e.mag AS detail
                ORDER BY e.time DESC
                LIMIT $limit
                """,
                {"since": since, "until": until, "limit": limit},
            )
            for row in result.result_set:
                events.append({
                    "type": row[0], "id": row[1], "summary": row[2],
                    "timestamp": row[3], "detail": row[4],
                })

        # Sort all events by timestamp descending
        events.sort(key=lambda e: e["timestamp"], reverse=True)
        return {"events": events[:limit], "since": since, "until": until}
    except Exception as e:
        return {"error": str(e), "events": []}


@app.get("/trajectory/{entity_type}/{entity_id}")
async def get_entity_trajectory(
    entity_type: str,
    entity_id: str,
    since: int = 0,
    limit: int = 500,
):
    """Return the historical trajectory of an aircraft or vessel.

    Queries OBSERVED_AT edges with lat/lon/timestamp for plotting
    a track line on the globe.
    """
    try:
        graph = get_graph(
            settings.falkordb_host, settings.falkordb_port, settings.falkordb_graph
        )

        if since == 0:
            since = int(datetime.now(timezone.utc).timestamp() * 1000) - 86_400_000

        if entity_type == "aircraft":
            result = graph.query(
                """
                MATCH (a:Aircraft {hex: $id})-[obs:OBSERVED_AT]->(l:Location)
                WHERE obs.timestamp >= $since
                RETURN obs.lat, obs.lon, obs.alt, obs.heading, obs.speed,
                       obs.timestamp, l.name
                ORDER BY obs.timestamp ASC
                LIMIT $limit
                """,
                {"id": entity_id, "since": since, "limit": limit},
            )
        elif entity_type == "vessel":
            result = graph.query(
                """
                MATCH (v:Vessel {mmsi: $id})-[obs:OBSERVED_AT]->(l:Location)
                WHERE obs.timestamp >= $since
                RETURN obs.lat, obs.lon, 0, obs.heading, obs.sog,
                       obs.timestamp, l.name
                ORDER BY obs.timestamp ASC
                LIMIT $limit
                """,
                {"id": entity_id, "since": since, "limit": limit},
            )
        else:
            return {"error": f"Unsupported entity type: {entity_type}", "points": []}

        points = []
        for row in result.result_set:
            points.append({
                "lat": row[0], "lon": row[1], "alt": row[2],
                "heading": row[3], "speed": row[4],
                "timestamp": row[5], "location": row[6],
            })

        return {"entity_type": entity_type, "entity_id": entity_id, "points": points}
    except Exception as e:
        return {"error": str(e), "points": []}


# ─── Satellite Passes (on-demand SGP4 computation) ───────────────

from .satellite_passes import compute_passes as _compute_passes
from .regions import list_regions as _list_regions


@app.get("/satellite-passes")
async def get_satellite_passes(
    region: str = "iran",
    hours: float = 24.0,
    direction: str = "past",
    group: str = "active",
    step_minutes: float | None = None,
    max_results: int = 200,
):
    """Compute satellite passes over a strategic region."""
    hours = min(max(hours, 0.5), 72.0)
    try:
        return await _compute_passes(
            region=region,
            hours=hours,
            direction=direction,
            group=group,
            step_minutes=step_minutes,
            max_results=max_results,
        )
    except Exception as e:
        logger.error("Satellite pass computation error: %s", e)
        return {"error": str(e), "passes": []}


@app.get("/satellite-passes/regions")
async def get_available_regions():
    """List all available strategic regions for satellite pass queries."""
    return {"regions": _list_regions()}
