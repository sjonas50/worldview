from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    falkordb_host: str = "localhost"
    falkordb_port: int = 6379
    falkordb_graph: str = "worldview_osint"
    backend_url: str = "http://localhost:3001"
    mil_flight_poll_interval: int = 15
    vessel_poll_interval: int = 60
    firms_poll_interval: int = 300
    gdelt_poll_interval: int = 900
    correlation_interval: int = 60

    model_config = {"env_file": ".env", "extra": "ignore"}
