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


class FIRMSHotspot(BaseModel):
    latitude: float
    longitude: float
    brightness: float = 0
    frp: float = 0
    confidence: str = "l"
    acq_date: str = ""
    acq_time: str = ""
    satellite: str = ""
    daynight: str = "D"
    timestamp: int = 0


class ConflictEvent(BaseModel):
    name: str = ""
    url: str = ""
    latitude: float
    longitude: float
    tone: float = 0
    goldstein: float = 0
    domain: str = ""
    sourceCountry: str = ""
    eventType: str = "unknown"
    timestamp: int = 0


class Vessel(BaseModel):
    mmsi: str
    name: str = ""
    latitude: float
    longitude: float
    heading: float | None = None
    cog: float | None = None
    sog: float = 0
    navStatus: int | None = None
    shipType: int | None = None
    destination: str | None = None
    imo: str | None = None
    callSign: str | None = None
    length: float | None = None
    width: float | None = None
    country: str | None = None
    countryCode: str | None = None
    timestamp: str = ""


class CorrelationAlert(BaseModel):
    id: str
    rule_type: str
    confidence: str
    summary: str
    detected_at: int
    source_entities: dict = {}
    thresholds: dict = {}
    data_sources: list[str] = []


class QueryAudit(BaseModel):
    id: str
    query: str
    answer: str
    session_id: str
    timestamp: int
    model: str = ""
