"""WorldView OSINT Ingestion Service.

FastAPI application that polls the Express backend for military flight data
and writes it into a FalkorDB knowledge graph.

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("worldview-ingestion")

settings = Settings()

# Cached location data for nearest-location lookups
_locations: list[dict] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init schema, seed locations, start ingestion loop."""
    global _locations

    logger.info(
        f"Connecting to FalkorDB at {settings.falkordb_host}:{settings.falkordb_port} "
        f"graph={settings.falkordb_graph}"
    )

    graph = get_graph(
        settings.falkordb_host, settings.falkordb_port, settings.falkordb_graph
    )

    # Initialize schema (idempotent)
    logger.info("Initializing schema constraints...")
    create_constraints(
        settings.falkordb_host, settings.falkordb_port, settings.falkordb_graph
    )
    initialize_indices(graph)

    # Seed location data
    logger.info("Seeding location data...")
    _locations = load_all_locations()
    await asyncio.to_thread(seed_locations, graph, _locations)

    # Start background ingestion loop
    logger.info(
        f"Starting ingestion loop (poll interval: {settings.mil_flight_poll_interval}s, "
        f"backend: {settings.backend_url})"
    )
    task = asyncio.create_task(_ingestion_loop())

    yield  # App is running

    # Shutdown
    logger.info("Shutting down ingestion loop...")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


async def _ingestion_loop():
    """Background loop polling military flights on a fixed interval."""
    # Brief delay to let services stabilize
    await asyncio.sleep(5)

    consecutive_errors = 0
    max_backoff = 120  # seconds

    while True:
        try:
            graph = get_graph(
                settings.falkordb_host,
                settings.falkordb_port,
                settings.falkordb_graph,
            )
            stats = await asyncio.to_thread(
                ingest_mil_flights, graph, settings.backend_url, _locations
            )
            consecutive_errors = 0
            logger.debug(f"Ingestion cycle complete: {stats}")

        except Exception as e:
            consecutive_errors += 1
            backoff = min(
                settings.mil_flight_poll_interval * (2 ** consecutive_errors),
                max_backoff,
            )
            logger.error(
                f"Ingestion error (attempt {consecutive_errors}): {e}. "
                f"Retrying in {backoff}s"
            )
            await asyncio.sleep(backoff)
            continue

        await asyncio.sleep(settings.mil_flight_poll_interval)


app = FastAPI(
    title="WorldView OSINT Ingestion",
    description="Knowledge graph ingestion service for the WorldView OSINT platform",
    version="0.1.0",
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
            OPTIONAL MATCH ()-[r:OBSERVED_AT]->()
            RETURN aircraft, locations, operators, count(r) AS observations
            """
        )
        row = result.result_set[0] if result.result_set else [0, 0, 0, 0]

        return {
            "aircraft": row[0],
            "locations": row[1],
            "operators": row[2],
            "observations": row[3],
        }
    except Exception as e:
        return {"error": str(e)}
