"""WorldView OSINT Ingestion Service.

FastAPI application that polls the Express backend for OSINT data
and writes it into a FalkorDB knowledge graph with cross-layer correlations.

Start with: uvicorn worldview_ingestion.main:app --host 0.0.0.0 --port 8000
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import Settings
from .db import get_graph
from .schema import create_constraints, initialize_indices
from .seed.locations import load_all_locations, seed_locations
from .ingestors.mil_flights import ingest_mil_flights
from .ingestors.firms import ingest_firms
from .ingestors.gdelt import ingest_gdelt
from .ingestors.vessels import ingest_vessels
from .correlations.engine import run_correlations

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
            _run_periodic("correlations", run_correlations,
                          settings.correlation_interval, graph_args, _locations)
        ),
    ]

    logger.info(
        f"Started {len(tasks)} ingestion loops "
        f"(mil={settings.mil_flight_poll_interval}s, "
        f"vessels={settings.vessel_poll_interval}s, "
        f"firms={settings.firms_poll_interval}s, "
        f"gdelt={settings.gdelt_poll_interval}s, "
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
    version="0.2.0",
    lifespan=lifespan,
)


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
            OPTIONAL MATCH (l:Location)
            WITH aircraft, count(l) AS locations
            OPTIONAL MATCH (o:Operator)
            WITH aircraft, locations, count(o) AS operators
            OPTIONAL MATCH (t:ThermalAnomaly)
            WITH aircraft, locations, operators, count(t) AS hotspots
            OPTIONAL MATCH (c:ConflictEvent)
            WITH aircraft, locations, operators, hotspots, count(c) AS events
            OPTIONAL MATCH (v:Vessel)
            WITH aircraft, locations, operators, hotspots, events, count(v) AS vessels
            OPTIONAL MATCH (ca:CorrelationAlert)
            RETURN aircraft, locations, operators, hotspots, events, vessels, count(ca) AS correlations
            """
        )
        row = result.result_set[0] if result.result_set else [0] * 7

        return {
            "aircraft": row[0],
            "locations": row[1],
            "operators": row[2],
            "hotspots": row[3],
            "events": row[4],
            "vessels": row[5],
            "correlations": row[6],
        }
    except Exception as e:
        return {"error": str(e)}


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
