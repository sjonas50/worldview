from falkordb import FalkorDB

_db: FalkorDB | None = None


def get_db(host: str, port: int) -> FalkorDB:
    """Get or create a FalkorDB client singleton."""
    global _db
    if _db is None:
        _db = FalkorDB(host=host, port=port)
    return _db


def get_graph(host: str, port: int, graph_name: str):
    """Get a named graph from the FalkorDB instance."""
    db = get_db(host, port)
    return db.select_graph(graph_name)
