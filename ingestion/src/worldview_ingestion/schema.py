import logging
import redis

logger = logging.getLogger("worldview-ingestion")


def initialize_indices(graph) -> None:
    """Create indices for fast lookups.

    Must run BEFORE constraints (FalkorDB requires a supporting index).
    Uses FalkorDB's CREATE INDEX ON syntax (no IF NOT EXISTS).
    """
    indices = [
        "CREATE INDEX ON :Aircraft(hex)",
        "CREATE INDEX ON :Aircraft(isMilitary)",
        "CREATE INDEX ON :Aircraft(lastSeen)",
        "CREATE INDEX ON :Location(id)",
        "CREATE INDEX ON :Location(type)",
        "CREATE INDEX ON :Operator(id)",
    ]

    for idx in indices:
        try:
            graph.query(idx)
            logger.info(f"Index created: {idx}")
        except Exception as e:
            if "already indexed" in str(e).lower() or "already exists" in str(e).lower():
                logger.debug(f"Index already exists: {idx}")
            else:
                logger.warning(f"Index creation note: {e}")


def create_constraints(host: str, port: int, graph_name: str) -> None:
    """Create UNIQUE constraints via GRAPH.CONSTRAINT CREATE Redis command.

    Idempotent — silently skips constraints that already exist.
    Indices must exist first (call initialize_indices before this).
    """
    r = redis.Redis(host=host, port=port, decode_responses=True)

    constraints = [
        f"GRAPH.CONSTRAINT CREATE {graph_name} UNIQUE NODE Aircraft PROPERTIES 1 hex",
        f"GRAPH.CONSTRAINT CREATE {graph_name} UNIQUE NODE Location PROPERTIES 1 id",
        f"GRAPH.CONSTRAINT CREATE {graph_name} UNIQUE NODE Operator PROPERTIES 1 id",
    ]

    for cmd in constraints:
        try:
            r.execute_command(*cmd.split())
            logger.info(f"Created constraint: {cmd}")
        except Exception as e:
            if "already exists" in str(e).lower() or "constraint already" in str(e).lower():
                logger.debug(f"Constraint already exists: {cmd}")
            else:
                logger.warning(f"Constraint creation note: {e}")

    r.close()
