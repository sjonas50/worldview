"""On-demand satellite pass computation over strategic regions.

Uses the sgp4 Python C extension for fast orbital propagation
and checks ground track intersection with region bounding boxes.

TLE data is fetched directly from CelesTrak with 2-hour in-memory cache.
"""

import logging
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import httpx
from sgp4.api import Satrec, WGS72, jday

from .regions import REGIONS, BoundingBox, resolve_region

logger = logging.getLogger("worldview-ingestion")

# ─── Constants ───────────────────────────────────────────────────

CELESTRAK_BASE = "https://celestrak.org/NORAD/elements/gp.php"
TLE_CACHE_TTL = 7200  # 2 hours

CELESTRAK_GROUPS: dict[str, str] = {
    "active": "active",
    "stations": "stations",
    "weather": "weather",
    "gps": "gps-ops",
    "starlink": "starlink",
    "military": "military",
    "science": "science",
    "geo": "geo",
    "resource": "resource",
}

TWO_PI = 2.0 * math.pi


# ─── TLE Management ─────────────────────────────────────────────


@dataclass
class TLEEntry:
    name: str
    norad_id: int
    line1: str
    line2: str
    satrec: Satrec


@dataclass
class _CacheEntry:
    entries: list[TLEEntry]
    fetched_at: float


_tle_cache: dict[str, _CacheEntry] = {}


def _parse_tle_text(text: str) -> list[TLEEntry]:
    """Parse 3-line TLE text into TLEEntry objects with pre-built Satrec."""
    lines = [ln.strip() for ln in text.strip().split("\n") if ln.strip()]
    entries: list[TLEEntry] = []
    i = 0
    while i + 2 < len(lines):
        name = lines[i]
        line1 = lines[i + 1]
        line2 = lines[i + 2]
        if line1.startswith("1 ") and line2.startswith("2 "):
            try:
                satrec = Satrec.twoline2rv(line1, line2, WGS72)
                norad_id = int(line2[2:7].strip())
                entries.append(
                    TLEEntry(
                        name=name.strip(),
                        norad_id=norad_id,
                        line1=line1,
                        line2=line2,
                        satrec=satrec,
                    )
                )
            except Exception:
                pass  # Skip malformed TLEs
            i += 3
        else:
            i += 1
    return entries


async def fetch_tles(group: str = "active") -> list[TLEEntry]:
    """Fetch TLEs from CelesTrak with 2-hour cache."""
    celestrak_group = CELESTRAK_GROUPS.get(group, group)

    cached = _tle_cache.get(celestrak_group)
    if cached and (time.time() - cached.fetched_at) < TLE_CACHE_TTL:
        return cached.entries

    url = f"{CELESTRAK_BASE}?GROUP={celestrak_group}&FORMAT=TLE"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            url,
            headers={"User-Agent": "WorldView-OSINT/1.0"},
        )
        resp.raise_for_status()

    entries = _parse_tle_text(resp.text)
    _tle_cache[celestrak_group] = _CacheEntry(entries=entries, fetched_at=time.time())
    logger.info("Fetched %d TLEs from CelesTrak group=%s", len(entries), celestrak_group)
    return entries


# ─── SGP4 Propagation ───────────────────────────────────────────


def _gmst(jd: float, fr: float) -> float:
    """Greenwich Mean Sidereal Time in radians."""
    t = (jd - 2451545.0 + fr) / 36525.0
    theta = (
        67310.54841
        + (876600.0 * 3600.0 + 8640184.812866) * t
        + 0.093104 * t * t
        - 6.2e-6 * t * t * t
    )
    return math.fmod(theta * (TWO_PI / 86400.0), TWO_PI)


def _propagate_geodetic(
    satrec: Satrec, jd: float, fr: float
) -> tuple[float, float, float] | None:
    """Propagate satellite and return (lat_deg, lon_deg, alt_km) or None."""
    e, r, _ = satrec.sgp4(jd, fr)
    if e != 0:
        return None

    x, y, z = r
    theta = _gmst(jd, fr)

    # ECI → ECEF rotation
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    x_ecef = x * cos_t + y * sin_t
    y_ecef = -x * sin_t + y * cos_t

    lon = math.degrees(math.atan2(y_ecef, x_ecef))
    lat = math.degrees(math.atan2(z, math.sqrt(x_ecef * x_ecef + y_ecef * y_ecef)))
    alt = math.sqrt(x * x + y * y + z * z) - 6371.0

    return lat, lon, alt


# ─── Pass Detection ──────────────────────────────────────────────


@dataclass
class SatellitePass:
    name: str
    norad_id: int
    enter_time: str  # ISO 8601
    exit_time: str
    duration_minutes: float
    peak_altitude_km: float
    sample_points: list[dict] = field(default_factory=list)


async def compute_passes(
    region: str | BoundingBox,
    hours: float = 24.0,
    direction: str = "past",
    group: str = "active",
    step_minutes: float | None = None,
    max_results: int = 200,
) -> dict:
    """Compute satellite passes over a region within a time window.

    Args:
        region: Region name/alias or BoundingBox.
        hours: Time window in hours (max 72).
        direction: "past" or "future".
        group: CelesTrak satellite group.
        step_minutes: Propagation step (auto-selected if None).
        max_results: Maximum passes returned.
    """
    # Resolve region
    if isinstance(region, str):
        resolved = resolve_region(region)
        if resolved is None:
            return {
                "error": f"Unknown region: '{region}'",
                "available_regions": list(REGIONS.keys()),
                "passes": [],
            }
        region_key, bbox = resolved
    else:
        bbox = region
        region_key = "custom"

    # Time window
    now = datetime.now(timezone.utc)
    if direction == "past":
        start = now - timedelta(hours=hours)
        end = now
    else:
        start = now
        end = now + timedelta(hours=hours)

    # Auto step size
    if step_minutes is None:
        if hours <= 6:
            step_minutes = 1.0
        elif hours <= 24:
            step_minutes = 2.0
        elif hours <= 48:
            step_minutes = 5.0
        else:
            step_minutes = 10.0

    step_seconds = step_minutes * 60.0
    total_seconds = (end - start).total_seconds()
    total_steps = int(total_seconds / step_seconds) + 1

    # Fetch TLEs
    t0 = time.time()
    tles = await fetch_tles(group)
    fetch_time = time.time() - t0

    # Propagate all satellites
    t1 = time.time()
    passes: list[SatellitePass] = []

    for tle in tles:
        in_region = False
        enter_dt: datetime | None = None
        points: list[dict] = []
        peak_alt = 0.0

        current = start
        while current <= end:
            jd, fr = jday(
                current.year,
                current.month,
                current.day,
                current.hour,
                current.minute,
                current.second + current.microsecond / 1e6,
            )
            result = _propagate_geodetic(tle.satrec, jd, fr)
            if result is None:
                current += timedelta(seconds=step_seconds)
                continue

            lat, lon, alt = result

            if bbox.contains(lat, lon):
                if not in_region:
                    in_region = True
                    enter_dt = current
                    points = []
                    peak_alt = alt
                if alt > peak_alt:
                    peak_alt = alt
                if len(points) < 10:
                    points.append(
                        {
                            "time": current.isoformat() + "Z",
                            "lat": round(lat, 4),
                            "lon": round(lon, 4),
                            "alt_km": round(alt, 1),
                        }
                    )
            else:
                if in_region and enter_dt is not None:
                    exit_dt = current - timedelta(seconds=step_seconds)
                    dur = (exit_dt - enter_dt).total_seconds() / 60.0
                    passes.append(
                        SatellitePass(
                            name=tle.name,
                            norad_id=tle.norad_id,
                            enter_time=enter_dt.isoformat() + "Z",
                            exit_time=exit_dt.isoformat() + "Z",
                            duration_minutes=round(dur, 1),
                            peak_altitude_km=round(peak_alt, 1),
                            sample_points=points,
                        )
                    )
                    in_region = False
                    enter_dt = None

            current += timedelta(seconds=step_seconds)

        # Satellite still over region at end of window
        if in_region and enter_dt is not None:
            dur = (end - enter_dt).total_seconds() / 60.0
            passes.append(
                SatellitePass(
                    name=tle.name,
                    norad_id=tle.norad_id,
                    enter_time=enter_dt.isoformat() + "Z",
                    exit_time=end.isoformat() + "Z",
                    duration_minutes=round(dur, 1),
                    peak_altitude_km=round(peak_alt, 1),
                    sample_points=points,
                )
            )

    compute_time = time.time() - t1

    # Sort: most recent first for past, earliest first for future
    passes.sort(key=lambda p: p.enter_time, reverse=(direction == "past"))
    passes = passes[:max_results]

    return {
        "region": region_key,
        "direction": direction,
        "hours": hours,
        "group": group,
        "step_minutes": step_minutes,
        "window_start": start.isoformat() + "Z",
        "window_end": end.isoformat() + "Z",
        "satellites_checked": len(tles),
        "total_passes": len(passes),
        "passes": [
            {
                "name": p.name,
                "norad_id": p.norad_id,
                "enter_time": p.enter_time,
                "exit_time": p.exit_time,
                "duration_minutes": p.duration_minutes,
                "peak_altitude_km": p.peak_altitude_km,
                "sample_points": p.sample_points,
            }
            for p in passes
        ],
        "performance": {
            "tle_fetch_seconds": round(fetch_time, 2),
            "compute_seconds": round(compute_time, 2),
            "total_propagations": len(tles) * total_steps,
        },
    }
