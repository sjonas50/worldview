import logging
import redis

logger = logging.getLogger("worldview-ingestion")


def create_constraints(host: str, port: int, graph_name: str) -> None:
    """Create UNIQUE constraints via GRAPH.CONSTRAINT CREATE Redis command.

    Idempotent — silently skips constraints that already exist.
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


def initialize_indices(graph) -> None:
    """Create indices for fast lookups.

    Idempotent — CREATE INDEX IF NOT EXISTS is safe to re-run.
    """
    indices = [
        "CREATE INDEX IF NOT EXISTS FOR (a:Aircraft) ON (a.hex)",
        "CREATE INDEX IF NOT EXISTS FOR (a:Aircraft) ON (a.isMilitary)",
        "CREATE INDEX IF NOT EXISTS FOR (a:Aircraft) ON (a.lastSeen)",
        "CREATE INDEX IF NOT EXISTS FOR (l:Location) ON (l.id)",
        "CREATE INDEX IF NOT EXISTS FOR (l:Location) ON (l.type)",
        "CREATE INDEX IF NOT EXISTS FOR (o:Operator) ON (o.id)",
    ]

    for idx in indices:
        try:
            graph.query(idx)
            logger.info(f"Index ready: {idx}")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.debug(f"Index already exists: {idx}")
            else:
                logger.warning(f"Index creation note: {e}")
