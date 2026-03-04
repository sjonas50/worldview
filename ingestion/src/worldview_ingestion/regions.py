"""Strategic region bounding boxes for satellite pass computation.

Each region is defined as {south, west, north, east} in decimal degrees.
Aliases map common names/abbreviations to canonical region keys.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BoundingBox:
    south: float
    west: float
    north: float
    east: float

    def contains(self, lat: float, lon: float) -> bool:
        """Check if a lat/lon point falls within this bounding box."""
        return self.south <= lat <= self.north and self.west <= lon <= self.east


# ─── Canonical region definitions ────────────────────────────────

REGIONS: dict[str, BoundingBox] = {
    # Middle East / Central Asia
    "iran": BoundingBox(25.0, 44.0, 40.0, 63.5),
    "iraq": BoundingBox(29.1, 38.8, 37.4, 48.6),
    "syria": BoundingBox(32.3, 35.7, 37.3, 42.4),
    "yemen": BoundingBox(12.1, 42.5, 19.0, 54.5),
    "gaza": BoundingBox(31.2, 34.2, 31.6, 34.6),
    "lebanon": BoundingBox(33.0, 35.1, 34.7, 36.6),
    "afghanistan": BoundingBox(29.4, 60.5, 38.5, 74.9),
    # Straits / Maritime chokepoints
    "hormuz": BoundingBox(25.0, 54.5, 27.5, 57.5),
    "suez": BoundingBox(29.5, 31.5, 31.5, 33.5),
    "malacca": BoundingBox(1.0, 99.0, 7.0, 104.5),
    "bab_el_mandeb": BoundingBox(11.5, 42.5, 13.0, 44.0),
    "taiwan_strait": BoundingBox(23.0, 117.5, 25.5, 120.5),
    # Maritime zones
    "persian_gulf": BoundingBox(23.5, 47.5, 30.5, 56.5),
    "red_sea": BoundingBox(12.5, 32.5, 30.0, 44.0),
    "black_sea": BoundingBox(40.9, 27.4, 46.7, 42.0),
    "south_china_sea": BoundingBox(3.0, 100.0, 23.0, 121.0),
    "east_china_sea": BoundingBox(24.0, 120.0, 33.0, 131.0),
    "baltic": BoundingBox(53.5, 10.0, 66.0, 30.5),
    "east_med": BoundingBox(30.0, 24.0, 37.0, 36.5),
    # Asia-Pacific
    "taiwan": BoundingBox(21.9, 119.3, 25.3, 122.0),
    "dprk": BoundingBox(37.6, 124.2, 43.0, 130.7),
    "korea": BoundingBox(33.1, 124.0, 43.0, 131.9),
    # Europe
    "ukraine": BoundingBox(44.3, 22.1, 52.4, 40.2),
    "crimea": BoundingBox(44.3, 32.5, 46.2, 36.7),
    # Africa
    "libya": BoundingBox(19.5, 9.3, 33.2, 25.2),
    "sudan": BoundingBox(8.7, 21.8, 22.2, 38.6),
    "somalia": BoundingBox(-1.7, 40.9, 12.0, 51.4),
    "ethiopia": BoundingBox(3.4, 33.0, 14.9, 48.0),
    # South Asia
    "india_pakistan": BoundingBox(23.5, 60.8, 37.1, 77.8),
    # Arctic
    "arctic": BoundingBox(66.5, -180.0, 90.0, 180.0),
}


# ─── Aliases for natural language parsing ─────────────────────────

ALIASES: dict[str, str] = {
    "north korea": "dprk",
    "n korea": "dprk",
    "north_korea": "dprk",
    "south korea": "korea",
    "korean peninsula": "korea",
    "strait of hormuz": "hormuz",
    "strait of malacca": "malacca",
    "malacca strait": "malacca",
    "suez canal": "suez",
    "persian gulf": "persian_gulf",
    "arabian gulf": "persian_gulf",
    "gulf": "persian_gulf",
    "red sea": "red_sea",
    "south china sea": "south_china_sea",
    "scs": "south_china_sea",
    "east china sea": "east_china_sea",
    "taiwan strait": "taiwan_strait",
    "formosa strait": "taiwan_strait",
    "east mediterranean": "east_med",
    "eastern med": "east_med",
    "eastern mediterranean": "east_med",
    "black sea": "black_sea",
    "baltic sea": "baltic",
    "india pakistan": "india_pakistan",
    "india-pakistan": "india_pakistan",
    "kashmir": "india_pakistan",
    "bab el mandeb": "bab_el_mandeb",
    "bab-el-mandeb": "bab_el_mandeb",
}


def resolve_region(name: str) -> tuple[str, BoundingBox] | None:
    """Resolve a region name or alias to (canonical_key, BoundingBox).

    Returns None if the region is not recognized.
    """
    key = name.lower().strip().replace("-", "_")

    # Direct match
    if key in REGIONS:
        return key, REGIONS[key]

    # Alias match
    if key in ALIASES:
        canonical = ALIASES[key]
        return canonical, REGIONS[canonical]

    # Substring match (input in key or key in input)
    for rk in REGIONS:
        if key in rk or rk in key:
            return rk, REGIONS[rk]
    for ak, canonical in ALIASES.items():
        if key in ak or ak in key:
            return canonical, REGIONS[canonical]

    return None


def list_regions() -> list[dict]:
    """Return all regions with their bounding boxes for API documentation."""
    return [
        {
            "key": k,
            "south": v.south,
            "west": v.west,
            "north": v.north,
            "east": v.east,
        }
        for k, v in REGIONS.items()
    ]
