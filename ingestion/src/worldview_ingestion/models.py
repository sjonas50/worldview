from pydantic import BaseModel


class MilFlight(BaseModel):
    hex: str
    callsign: str = ""
    registration: str = ""
    aircraftType: str = ""
    description: str = ""
    operator: str = ""
    latitude: float
    longitude: float
    altitude: float = 0
    altitudeFeet: float = 0
    heading: float | None = None
    velocity: float | None = None
    velocityKnots: float | None = None
    squawk: str = ""
    verticalRate: float | None = None
    dbFlags: int = 0
    isMilitary: bool = True
    isLADD: bool = False
    emergency: bool = False


class Location(BaseModel):
    id: str
    name: str
    type: str  # airport | base | strait | port
    lat: float
    lon: float
    country: str = ""
    iata: str = ""
