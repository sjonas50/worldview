# WorldView OSINT Platform — Technical Build Document

**Project:** WorldView Extended (fork of kevtoe/worldview)
**Owner:** The Attic AI — Steve Jonas, CTO/COO
**Date:** March 3, 2026
**Status:** Phase 1 Complete (9 data layers), Phase 2 Planned (FalkorDB + Graphiti + Engram)

---

## Table of Contents

1. Platform Overview
2. Current Architecture
3. Data Source Integrations (Current)
4. Frontend Layer Components (Current)
5. Server API Routes (Current)
6. Environment & Deployment
7. Phase 2: FalkorDB Knowledge Graph Integration
8. Phase 2: Graphiti Temporal Ingestion Pipeline
9. Phase 2: Engram Reasoning Audit Trail
10. Phase 2: Cross-Layer Correlation Engine
11. Phase 2: GraphRAG Natural Language Query Interface
12. Phase 2: Docker Compose Full Stack
13. Phase 2: Build Order & Milestones
14. API Key Registry
15. Legal & Ethical Considerations

---

## 1. Platform Overview

WorldView is a real-time OSINT geospatial intelligence dashboard built on a 3D CesiumJS globe. It overlays live data feeds — flights, military aircraft, satellites, ships, thermal anomalies, conflict events, earthquakes, traffic, and CCTV cameras — onto an interactive Earth visualization with a tactical UI aesthetic.

The platform is inspired by Bilawal Sidhu's viral "WorldView" project (March 1, 2026, 3.6M views on X) which reconstructed Operation Epic Fury in 4D using OSINT agent swarms. Our fork extends the open-source implementation with additional intelligence-grade data layers, a historical reconstruction system, and (in Phase 2) a FalkorDB-backed knowledge graph for cross-layer correlation and AI-powered analysis.

### Design Philosophy

- Real-time monitoring AND historical reconstruction
- Cross-layer entity correlation (not just isolated data feeds)
- Auditable intelligence products (Engram reasoning capture)
- Natural language querying via GraphRAG
- Free/open-source data sources wherever possible
- Imperative CesiumJS rendering for 27K+ entity performance at 60fps

---

## 2. Current Architecture

### Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Frontend Framework | React + TypeScript | React 19, TS 5.9 |
| Build Tool | Vite | 7.3 |
| 3D Globe | CesiumJS via Resium | Cesium 1.138 |
| Styling | Tailwind CSS | v4.2 |
| Satellite Math | satellite.js | 6.0 |
| Geospatial Utils | @turf/turf | 7.3 |
| Backend Server | Express (Node.js ESM) | Express 5.2 |
| Caching | node-cache (in-memory) | 5.1 |
| Real-time Push | ws (WebSocket) | 8.19 |
| Deployment | Vercel (serverless) | — |

### Data Flow

```
External APIs ──► Express Proxy (port 3001)
                    │  • Rate limiting
                    │  • Response caching (node-cache)
                    │  • Credential hiding
                    │  • WebSocket push (OpenSky)
                    │  • Auto-snapshot recording (60s)
                    │
                    ▼
              React Hooks (polling + transform)
                    │
              App.tsx (state management)
                    │
    ┌───────────┬───┴───────┬────────────┐
GlobeViewer   9 Layers    UI Panels    StatusBar
 (CesiumJS)  (imperative) (React DOM)  (React DOM)
```

### File Structure Summary

```
worldview/
├── server/
│   ├── index.js              # All API routes + WebSocket + caching (1,439 lines)
│   └── data/sydneyRoads.js   # Static fallback road data
├── src/
│   ├── App.tsx                # Root component, state mgmt, layer composition (490 lines)
│   ├── hooks/                 # 13 data hooks (1,613 lines total)
│   │   ├── useFlights.ts         # Global flights (FR24 → adsb.fi fallback)
│   │   ├── useFlightsLive.ts     # Regional high-freq flights (adsb.fi)
│   │   ├── useMilFlights.ts      # Military flights (Airplanes.live) ★ NEW
│   │   ├── useSatellites.ts      # TLE fetch + SGP4 propagation
│   │   ├── useShips.ts           # AIS vessel tracking
│   │   ├── useFIRMS.ts           # NASA thermal anomalies ★ NEW
│   │   ├── useConflictEvents.ts  # GDELT conflict events ★ NEW
│   │   ├── useEarthquakes.ts     # USGS seismic data
│   │   ├── useCameras.ts         # Multi-source CCTV aggregation
│   │   ├── useTraffic.ts         # Road network + vehicle simulation
│   │   ├── useGeolocation.ts     # Browser GPS + IP fallback
│   │   ├── useAudio.ts           # Tactical audio engine
│   │   └── useIsMobile.ts        # Responsive breakpoint
│   ├── components/
│   │   ├── layers/            # 9 CesiumJS rendering layers (2,527 lines total)
│   │   │   ├── FlightLayer.tsx       # 27K+ aircraft, dead-reckoning
│   │   │   ├── MilFlightLayer.tsx    # Military aircraft (red diamonds) ★ NEW
│   │   │   ├── ShipLayer.tsx         # AIS vessels by category
│   │   │   ├── SatelliteLayer.tsx    # SGP4 orbit propagation
│   │   │   ├── FIRMSLayer.tsx        # Thermal anomaly hotspots ★ NEW
│   │   │   ├── ConflictLayer.tsx     # GDELT events by severity ★ NEW
│   │   │   ├── EarthquakeLayer.tsx   # Seismic markers
│   │   │   ├── TrafficLayer.tsx      # Road network + vehicles
│   │   │   └── CCTVLayer.tsx         # Camera billboards
│   │   ├── globe/
│   │   │   ├── GlobeViewer.tsx       # CesiumJS Viewer wrapper
│   │   │   └── EntityClickHandler.tsx
│   │   └── ui/
│   │       ├── OperationsPanel.tsx   # Layer toggles + shader controls
│   │       ├── IntelFeed.tsx         # Real-time event stream
│   │       ├── StatusBar.tsx         # Entity counts + coordinates
│   │       ├── TrackedEntityPanel.tsx
│   │       ├── CCTVPanel.tsx
│   │       ├── SplashScreen.tsx
│   │       ├── Crosshair.tsx
│   │       ├── AudioToggle.tsx
│   │       ├── FilmGrain.tsx
│   │       └── MobileModal.tsx
│   ├── shaders/postprocess.ts    # GLSL: CRT, NVG, FLIR effects
│   ├── data/airports.ts          # IATA → coordinate lookup
│   └── types/camera.ts
├── public/                        # Static assets + demo recordings
├── api/index.js                   # Vercel serverless entry point
├── vite.config.ts                 # Vite + React + Cesium + Tailwind + /api proxy
├── vercel.json                    # Vercel deployment config
└── CLAUDE.md                      # Project guide
```

---

## 3. Data Source Integrations (Current)

### 3.1 Commercial Flight Tracking

**Source: FlightRadar24 (primary) + adsb.fi (enrichment/fallback)**

| Property | FlightRadar24 | adsb.fi |
|----------|--------------|---------|
| Endpoint | `data-cloud.flightradar24.com/zones/fcgi/feed.js` | `opendata.adsb.fi/api/v2` |
| Auth | None (scraping) | None |
| Rate | 15s min interval | 5s poll |
| Coverage | Global (~27K aircraft) | Regional (250nm radius) |
| Cache TTL | 30s | 4s |
| Server Route | `GET /api/flights` | `GET /api/flights/live?lat=X&lon=Y&dist=Z` |

**Dual-source deduplication strategy:** Global FR24 data polled at 30s provides route info (origin/dest airports, airlines). Regional adsb.fi data polled at 5s provides high-frequency position updates within 250nm of camera. App.tsx merges them — live adsb.fi positions replace matching FR24 positions by ICAO24 hex, while FR24 route metadata enriches the live data. Zero duplicates.

**Dead-reckoning:** FlightLayer.tsx extrapolates aircraft positions between data updates using heading + ground speed for smooth 60fps rendering. Position = last_known + (velocity × heading × elapsed_time).

**Data schema per aircraft:**
```typescript
{
  icao24: string       // Mode S hex identifier
  callsign: string     // e.g. "UAL123"
  registration: string // e.g. "N12345"
  aircraftType: string // e.g. "B738"
  description: string  // e.g. "Boeing 737-800"
  operator: string     // e.g. "United Airlines"
  latitude: number
  longitude: number
  altitude: number     // metres (converted from baro feet)
  altitudeFeet: number
  heading: number | null
  velocity: number | null     // m/s
  velocityKnots: number | null
  verticalRate: number | null // m/s
  squawk: string
  category: string
  originAirport: string       // FR24 enrichment
  destAirport: string         // FR24 enrichment
  airline: string             // FR24 enrichment
}
```

**Rendering:** Imperative `BillboardCollection` with custom canvas-drawn aircraft icons. Altitude-band coloring: cyan (cruise ≥FL350), blue (high FL200-349), gold (mid FL100-199), orange (low FL030-099), red (near ground <3K ft). Icons rotate by heading. Scale by distance via `NearFarScalar`.

---

### 3.2 Military Flight Tracking ★ NEW

**Source: Airplanes.live**

| Property | Value |
|----------|-------|
| Endpoint | `api.airplanes.live/v2/mil` |
| Auth | **None** — completely free, no API key |
| Rate Limit | 1 request/second |
| Poll Interval | 10s |
| Cache TTL | 8s |
| Server Route | `GET /api/flights/military` |

**Why Airplanes.live:** This is the only major free source that does NOT filter military or LADD-blocked aircraft. FlightRadar24, ADS-B Exchange, and even adsb.fi suppress LADD (Limiting Aircraft Data Displayed) aircraft per FAA rules. Airplanes.live publishes everything — confirmed military, PIA (Privacy ICAO Address), and LADD-blocked birds.

**Database flags (dbFlags bitfield):**
- Bit 0 (1): Military
- Bit 1 (2): Interesting
- Bit 2 (4): PIA (Privacy ICAO Address — randomized hex)
- Bit 3 (8): LADD (hidden on commercial trackers)

**Emergency detection:** Squawk codes 7500 (hijack), 7600 (radio failure), 7700 (emergency) flagged in real-time with pulsing markers and intel feed alerts.

**Data schema:**
```typescript
{
  hex: string              // Mode S hex (ICAO24)
  callsign: string
  registration: string
  aircraftType: string     // e.g. "C17A", "KC135R", "F35A"
  description: string      // e.g. "C-17A Globemaster III"
  operator: string         // e.g. "United States Air Force"
  latitude: number
  longitude: number
  altitude: number         // metres
  altitudeFeet: number
  heading: number | null
  velocity: number | null  // m/s
  velocityKnots: number | null
  squawk: string
  verticalRate: number | null
  dbFlags: number
  isMilitary: boolean
  isLADD: boolean
  emergency: boolean
}
```

**Rendering:** Red diamond markers for confirmed military. Amber diamonds for LADD-blocked. Pulsing white outline for emergency squawks. Icons rotate by heading.

---

### 3.3 Satellite Tracking

**Source: TLE API (primary) + CelesTrak (fallback)**

| Property | TLE API | CelesTrak |
|----------|---------|-----------|
| Endpoint | `tle.ivanstanojevic.me/api/tle` | `celestrak.org/NORAD/elements/gp.php` |
| Auth | None | None |
| Rate | Reasonable use | 30 req/min |
| Format | JSON → 3-line TLE | Native TLE text |
| Cache TTL | 2 hours | 2 hours |
| Server Route | `GET /api/satellites?group=stations` |

**SGP4 Propagation:** TLE (Two-Line Element) orbital parameters are fetched once every 2 hours. `satellite.js` library computes real-time lat/lon/altitude positions using the SGP4/SDP4 propagation algorithm on the client side — no server computation needed. Positions update every frame for smooth orbital animation.

**Satellite groups available:** stations (ISS), starlink, gps-ops, weather, active, military (via CelesTrak `GROUP=military`).

**Rendering:** Point primitives with orbit path polylines. ISS highlighted separately. Orbit trails rendered as dashed polylines using `PolylineCollection`.

---

### 3.4 Ship Tracking (AIS)

**Source: AISStream.io (WebSocket)**

| Property | Value |
|----------|-------|
| Endpoint | `wss://stream.aisstream.io/v0/stream` |
| Auth | API key (free tier) |
| Strategy | Burst-collect: 20s WebSocket → cache 60s |
| Coverage | Global (all vessels broadcasting AIS) |
| Cache TTL | 60s |
| Server Route | `GET /api/ships?moving=1` |

**Burst-WebSocket pattern:** Opens a WebSocket for 20 seconds, collects PositionReport and ShipStaticData messages, deduplicates by MMSI (keeps latest), then closes. Collects ~2,000-4,000 unique vessels per burst. This avoids persistent connections and fits within Vercel's 30-second serverless timeout.

**Ship categories by AIS type code:**
- 70-79: Cargo (gray)
- 80-89: Tanker (blue)
- 60-69: Passenger (white)
- 30: Fishing (green)
- 35: Military (red)
- 31-32, 52: Tug (brown)
- 36-37: Pleasure (teal)
- 40-49: High-speed craft (yellow)

**Data schema:**
```typescript
{
  mmsi: string           // Maritime Mobile Service Identity
  name: string
  latitude: number
  longitude: number
  heading: number | null // True heading (511 = unavailable)
  cog: number | null     // Course over ground
  sog: number            // Speed over ground (knots)
  navStatus: NavStatus   // 0=engine, 1=anchor, 5=moored, etc.
  shipType: number | null
  destination: string | null
  imo: number | null
  callSign: string | null
  length: number | null  // metres (A+B dimensions)
  width: number | null   // metres (C+D dimensions)
  country: string | null
  countryCode: string | null
  timestamp: string
}
```

**Rendering:** Imperative `BillboardCollection` + `PointPrimitiveCollection`. Canvas-drawn ship icons colored by category. Heading arrow indicators. Name labels at close zoom via `LabelCollection`.

---

### 3.5 NASA FIRMS Thermal Anomalies ★ NEW

**Source: NASA Fire Information for Resource Management System**

| Property | Value |
|----------|-------|
| Endpoint | `firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/VIIRS_SNPP_NRT/world/{days}` |
| Auth | MAP_KEY (free registration) — works without key at reduced rate |
| Sensor | VIIRS (Visible Infrared Imaging Radiometer Suite) |
| Resolution | 375 metres |
| Latency | ~3 hours (60 seconds for US/Canada Ultra Real-Time) |
| Poll Interval | 5 minutes |
| Cache TTL | 5 minutes |
| Server Route | `GET /api/firms` |

**Strike signature detection logic:** A thermal anomaly is flagged as a potential military strike when ALL of:
- `daynight = 'N'` (nighttime detection — eliminates most agricultural/wildfire false positives)
- `frp > 50` MW (high fire radiative power — industrial/natural fires typically < 30 MW)
- `confidence = 'h'` (high confidence from VIIRS classifier)
- Isolated location (not part of a vegetation fire cluster)

**Data schema:**
```typescript
{
  latitude: number
  longitude: number
  brightness: number    // Brightness temperature (Kelvin)
  frp: number           // Fire radiative power (MW) — KEY INDICATOR
  confidence: string    // 'l' | 'n' | 'h'
  acq_date: string      // YYYY-MM-DD
  acq_time: string      // HHMM UTC
  satellite: string
  daynight: string      // 'D' | 'N'
  timestamp: number     // Unix ms
}
```

**Rendering:** Point primitives sized by FRP (4px base + sqrt(FRP) × 1.5, max 20px). Colors: bright red (#FF1744) for potential strikes, orange (#FF6D00) for high-conf, amber (#FF9100) for nominal, pale (#FFB74D) for low-conf. High-FRP strikes get an additional canvas-drawn pulsing ring billboard.

---

### 3.6 GDELT Conflict Events ★ NEW

**Source: GDELT Project GeoJSON API**

| Property | Value |
|----------|-------|
| Endpoint | `api.gdeltproject.org/api/v2/geo/geo` |
| Auth | **None** |
| Update Frequency | Every 15 minutes |
| Coverage | Global, 65 languages |
| Default Query | `conflict OR military OR strike OR missile` |
| Max Points | 500 (configurable up to 2,000) |
| Cache TTL | 15 minutes |
| Server Route | `GET /api/gdelt?query=X&timespan=24h&maxpoints=500` |

**Goldstein scale classification:**
- **Conflict** (red): Goldstein ≤ -5 — active hostilities, use of force
- **Tension** (orange): Goldstein -5 to -2 — threats, sanctions, protests
- **Diplomatic** (yellow): Goldstein -2 to +2 — statements, meetings, negotiations
- **Cooperation** (green): Goldstein > +2 — agreements, aid, joint exercises

**Data schema:**
```typescript
{
  id: string
  name: string           // Event headline
  url: string            // Source article URL
  latitude: number
  longitude: number
  tone: number           // Sentiment (-100 to +100)
  goldstein: number      // Goldstein scale (-10 to +10)
  domain: string         // Source domain
  sourceCountry: string
  timestamp: string
  eventType: 'conflict' | 'tension' | 'diplomatic' | 'cooperation' | 'unknown'
  shareImage: string     // Article thumbnail
}
```

**Rendering:** Point primitives colored by event type. Size scales with absolute Goldstein value (bigger = more intense). Alpha scales with hostility (conflict = 0.9, tension = 0.75, diplomatic/cooperation = 0.55).

---

### 3.7 Seismic Data

**Source: USGS Earthquake Hazards Program**

| Property | Value |
|----------|-------|
| Endpoint | `earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson` |
| Auth | **None** |
| Update Frequency | Every minute |
| Coverage | Global |
| Cache TTL | 60 seconds |
| Server Route | `GET /api/earthquakes` |

**Explosion detection note:** USGS classifies events by type — `earthquake`, `explosion`, `quarry blast`, `nuclear explosion`. Events at depth ~0 km with distinctive waveforms may indicate non-seismic detonations. The `type` field in the GeoJSON properties can flag these.

**Rendering:** Resium Entity components with pulsing ellipses sized by magnitude. Color gradient from yellow (small) to red (large).

---

### 3.8 CCTV Camera Feeds

**Sources: TfL London + Austin TX Open Data + Transport for NSW**

| Source | Endpoint | Auth | Cameras |
|--------|----------|------|---------|
| TfL London | `api.tfl.gov.uk/Place/Type/JamCam` | None | ~900 |
| Austin TX | `data.austintexas.gov/resource/b4k4-adkb.json` | None | ~200 |
| Transport NSW | `api.transport.nsw.gov.au/v1/live/cameras` | API key | ~500 |

Cache TTL: 5 minutes for all sources. Server route: `GET /api/cctv?country=GB&source=tfl`. Image proxy at `GET /api/cctv/image?url=<encoded>` to avoid CORS.

**Rendering:** Imperative `BillboardCollection` with camera icons. Click-to-lock-on with street-level camera view (300m altitude, heading-matched orientation). CCTVPanel shows thumbnail grid with live previews.

---

### 3.9 Street Traffic

**Source: OpenStreetMap Overpass API**

Road geometries fetched for the camera viewport bounding box. Cached 24 hours. Animated vehicle particles simulate traffic flow at 60fps along road polylines. Fallback to static Sydney CBD data if Overpass rate-limited.

---

### 3.10 Historical Snapshots ★ NEW

**Server-side auto-recording system:**

| Property | Value |
|----------|-------|
| Interval | Every 60 seconds (automatic) |
| Storage | In-memory array (Phase 1) → FalkorDB (Phase 2) |
| Retention | 1,440 snapshots (24 hours rolling) |
| Contents | Military flights, ships, FIRMS, earthquakes, GDELT |

**API routes:**
- `POST /api/snapshot` — manually trigger a snapshot
- `GET /api/snapshots?from=X&to=Y&limit=100` — list available snapshots
- `GET /api/snapshot/:timestamp` — retrieve specific snapshot (returns closest match)

---

## 4. Frontend Layer Components (Current)

All layers use imperative CesiumJS primitive collections (not Resium declarative components) for performance. Pattern:

1. `useEffect` creates `BillboardCollection` / `PointPrimitiveCollection` / `PolylineCollection` and adds to `viewer.scene.primitives`
2. Second `useEffect` watches data + visibility, calls `collection.removeAll()` then re-adds all primitives
3. `CallbackProperty` used for tracked entities (smooth camera follow)
4. `NearFarScalar` on all primitives for distance-based scaling
5. `disableDepthTestDistance: Number.POSITIVE_INFINITY` ensures markers render above terrain

| Layer | Lines | Entities | Technique |
|-------|-------|----------|-----------|
| FlightLayer | 660 | 27K+ | BillboardCollection + dead-reckoning |
| MilFlightLayer ★ | 183 | ~500 | BillboardCollection + diamond icons |
| ShipLayer | 529 | 2-4K | BillboardCollection + PointPrimitive |
| SatelliteLayer | 308 | ~100 | PointPrimitive + PolylineCollection orbits |
| FIRMSLayer ★ | 151 | ~1K | PointPrimitive + canvas ring billboards |
| ConflictLayer ★ | 107 | ~500 | PointPrimitive, color by Goldstein |
| EarthquakeLayer | 152 | ~200 | Resium Entities (pulsing ellipses) |
| TrafficLayer | 279 | ~500 roads | PolylineCollection + PointPrimitive |
| CCTVLayer | 158 | ~1.6K | BillboardCollection |

---

## 5. Server API Routes (Current)

Express 5 backend on port 3001. All routes cached via `node-cache`. Vite dev server proxies `/api/*` to `:3001`.

| Route | Method | Source | Cache | Auth |
|-------|--------|--------|-------|------|
| `/api/flights` | GET | FR24 → adsb.fi | 30s | None |
| `/api/flights/live` | GET | adsb.fi | 4s | None |
| `/api/flights/military` ★ | GET | Airplanes.live | 8s | None |
| `/api/satellites` | GET | TLE API → CelesTrak | 2hr | None |
| `/api/ships` | GET | AISStream.io | 60s | API key |
| `/api/firms` ★ | GET | NASA FIRMS | 5min | MAP_KEY (opt) |
| `/api/gdelt` ★ | GET | GDELT | 15min | None |
| `/api/earthquakes` | GET | USGS | 60s | None |
| `/api/cctv` | GET | TfL + Austin + NSW | 5min | NSW key |
| `/api/cctv/image` | GET | Proxy | — | None |
| `/api/traffic/roads` | GET | Overpass | 24hr | None |
| `/api/geolocation` | GET | ip-api.com | — | None |
| `/api/snapshot` ★ | POST | Internal cache | — | None |
| `/api/snapshots` ★ | GET | Internal array | — | None |
| `/api/snapshot/:ts` ★ | GET | Internal array | — | None |
| `/ws` | WebSocket | OpenSky | 10s | OAuth2 |

---

## 6. Environment & Deployment

### Local Development

```bash
git clone <repo>
cd worldview
npm install
cp .env.example .env              # Add VITE_GOOGLE_API_KEY, VITE_CESIUM_ION_TOKEN
cp server/.env.example server/.env # Add OPENSKY, NASA_FIRMS_MAP_KEY, AISSTREAM_API_KEY
npm run dev:all                    # Starts backend (3001) + frontend (5173)
```

### Client-side Environment Variables (.env)

| Variable | Required | Purpose |
|----------|----------|---------|
| `VITE_GOOGLE_API_KEY` | Recommended | Google 3D Photorealistic Tiles (falls back to OSM) |
| `VITE_CESIUM_ION_TOKEN` | Optional | Cesium Ion terrain/imagery services |
| `WINDY_API_KEY` | Reserved | Windy webcam API (not yet active) |
| `NSW_TRANSPORT_API_KEY` | Optional | Transport for NSW CCTV |

### Server-side Environment Variables (server/.env)

| Variable | Required | Purpose |
|----------|----------|---------|
| `OPENSKY_CLIENT_ID` | Optional | OpenSky Network OAuth2 |
| `OPENSKY_CLIENT_SECRET` | Optional | OpenSky Network OAuth2 |
| `NASA_FIRMS_MAP_KEY` | Optional | NASA FIRMS (higher rate limits) |
| `AISSTREAM_API_KEY` | Recommended | AISStream.io WebSocket access |

### Vercel Deployment

Project includes `vercel.json` and `api/index.js` serverless wrapper. All `/api/*` routes rewrite to a single serverless function with 30s timeout and 256MB memory. The AISStream burst-collect pattern (20s WebSocket) fits within this constraint.

```bash
npm run build     # TypeScript compile + Vite production build → dist/
vercel deploy     # Deploy to Vercel
```

**Vercel limitations:** No persistent WebSocket connections. No persistent state between invocations. The snapshot system uses in-memory storage which resets on cold starts — Phase 2 moves this to FalkorDB.

---

## 7. Phase 2: FalkorDB Knowledge Graph Integration

### Why FalkorDB

FalkorDB is the direct successor to RedisGraph (EOL January 2025). It uses sparse matrix algebra (GraphBLAS) for graph operations instead of node-by-node traversal, achieving sub-10ms multi-hop queries at millions of nodes. Key advantages for this use case:

- **Same wire protocol as Redis** (port 6379) — drops into the existing stack
- **OpenCypher query language** — industry-standard graph queries
- **Multi-tenancy** — isolated graph instances per analyst/operation with zero overhead
- **In-memory with persistence** — real-time query performance with durability
- **GraphRAG-SDK** — native LLM integration for natural language querying
- **Graphiti temporal support** — bi-temporal knowledge graph with valid_at/invalid_at timestamps
- **SSPL license** — same as MongoDB, viable for commercial use
- **Single Docker container** — no JVM, no cluster config, no license server

### OSINT Ontology Schema

```cypher
// === NODE TYPES ===

// Aircraft observed via ADS-B
CREATE CONSTRAINT FOR (a:Aircraft) REQUIRE a.hex IS UNIQUE
// Properties: hex, callsign, registration, aircraftType, description,
//             operator, isMilitary, isLADD, dbFlags

// Vessel observed via AIS
CREATE CONSTRAINT FOR (v:Vessel) REQUIRE v.mmsi IS UNIQUE
// Properties: mmsi, name, imo, callSign, shipType, shipCategory,
//             flag, length, width

// Satellite tracked via TLE
CREATE CONSTRAINT FOR (s:Satellite) REQUIRE s.noradId IS UNIQUE
// Properties: noradId, name, intlDesignator, orbitType, constellation

// Thermal anomaly from FIRMS
CREATE CONSTRAINT FOR (f:ThermalAnomaly) REQUIRE f.firmsId IS UNIQUE
// Properties: firmsId, frp, brightness, confidence, daynight,
//             acqDate, acqTime, isPotentialStrike

// Conflict event from GDELT
CREATE CONSTRAINT FOR (e:ConflictEvent) REQUIRE e.gdeltId IS UNIQUE
// Properties: gdeltId, name, url, goldstein, tone, eventType,
//             domain, sourceCountry

// Seismic event from USGS
CREATE CONSTRAINT FOR (q:Earthquake) REQUIRE q.usgsId IS UNIQUE
// Properties: usgsId, magnitude, depth, type, place

// Named location (airport, base, port, city, region)
CREATE CONSTRAINT FOR (l:Location) REQUIRE l.id IS UNIQUE
// Properties: id, name, type (airport|base|port|city|region|strait),
//             lat, lon, country, icao, iata

// Operator / organization
CREATE CONSTRAINT FOR (o:Operator) REQUIRE o.id IS UNIQUE
// Properties: id, name, country, type (military|airline|shipping|government)

// Airspace restriction
CREATE CONSTRAINT FOR (n:Airspace) REQUIRE n.notamId IS UNIQUE
// Properties: notamId, type (TFR|MOA|ADIZ|restricted), ceiling, floor,
//             effectiveFrom, effectiveTo, geometry (GeoJSON)


// === RELATIONSHIP TYPES ===
// All relationships carry: created_at, valid_at, invalid_at (Graphiti temporal)

// Spatial observations (high volume — primary correlation targets)
// (:Aircraft)-[:OBSERVED_AT {lat, lon, alt, heading, speed, timestamp}]->(:Location)
// (:Vessel)-[:TRANSITED {lat, lon, sog, cog, timestamp}]->(:Location)
// (:Satellite)-[:PASSED_OVER {lat, lon, alt, timestamp}]->(:Location)
// (:ThermalAnomaly)-[:DETECTED_AT {timestamp}]->(:Location)
// (:ConflictEvent)-[:REPORTED_AT {timestamp}]->(:Location)
// (:Earthquake)-[:OCCURRED_AT {timestamp}]->(:Location)

// Organizational
// (:Aircraft)-[:OPERATED_BY]->(:Operator)
// (:Vessel)-[:FLAGGED_BY {country}]->(:Operator)

// Airspace
// (:Aircraft)-[:ENTERED_AIRSPACE {timestamp}]->(:Airspace)
// (:Aircraft)-[:EXITED_AIRSPACE {timestamp}]->(:Airspace)

// === CROSS-LAYER CORRELATION RELATIONSHIPS ===
// These are the intelligence products — created by the correlation engine

// Military aircraft near thermal anomaly within time window
// (:Aircraft)-[:PROXIMATE_TO {distance_km, time_delta_min, confidence}]->(:ThermalAnomaly)

// Thermal anomaly correlated with conflict event
// (:ThermalAnomaly)-[:CORRELATED_WITH {distance_km, time_delta_min, confidence}]->(:ConflictEvent)

// Vessel course change near conflict zone
// (:Vessel)-[:DIVERTED_NEAR {old_cog, new_cog, distance_km}]->(:ConflictEvent)

// Aircraft entering restricted airspace
// (:Aircraft)-[:VIOLATED {timestamp}]->(:Airspace)

// Co-location of multiple entity types
// (:Aircraft)-[:CO_LOCATED_WITH {distance_km, timestamp}]->(:Vessel)
```

### Location Node Seeding

Pre-populate the Location graph with known strategic locations:

```cypher
// Major military bases
CREATE (:Location {id: 'base-al-udeid', name: 'Al Udeid Air Base', type: 'base',
  lat: 25.1174, lon: 51.3150, country: 'QA'})
CREATE (:Location {id: 'base-diego-garcia', name: 'Diego Garcia', type: 'base',
  lat: -7.3133, lon: 72.4111, country: 'US'})
CREATE (:Location {id: 'base-incirlik', name: 'Incirlik Air Base', type: 'base',
  lat: 37.0021, lon: 35.4259, country: 'TR'})
CREATE (:Location {id: 'base-ramstein', name: 'Ramstein Air Base', type: 'base',
  lat: 49.4369, lon: 7.6003, country: 'DE'})

// Strategic chokepoints
CREATE (:Location {id: 'strait-hormuz', name: 'Strait of Hormuz', type: 'strait',
  lat: 26.5667, lon: 56.2500, country: 'IR/OM'})
CREATE (:Location {id: 'strait-bab-el-mandeb', name: 'Bab el-Mandeb', type: 'strait',
  lat: 12.5833, lon: 43.3333, country: 'YE/DJ'})
CREATE (:Location {id: 'strait-malacca', name: 'Strait of Malacca', type: 'strait',
  lat: 2.5000, lon: 101.0000, country: 'MY/ID'})

// Key airports (extend from existing airports.ts data)
// ... bulk import from src/data/airports.ts
```

---

## 8. Phase 2: Graphiti Temporal Ingestion Pipeline

### Architecture

A Python sidecar service (FastAPI) consumes entity updates from the Express backend and writes them into FalkorDB as Graphiti episodes. This runs alongside the existing Node.js server.

```
Express Backend (port 3001)
    │
    │ Internal HTTP (poll every N seconds)
    ▼
FastAPI Ingestion Service (port 8000)
    │
    │ Graphiti add_episode()
    ▼
FalkorDB (port 6379)
    │
    │ OpenCypher queries
    ▼
Knowledge Graph
```

### Python Dependencies

```
falkordb>=1.2.0
graphiti-core>=0.17.0
fastapi[standard]>=0.115.0
httpx>=0.27.0
pydantic>=2.0
```

### Ingestion Service Design

```python
# osint_ingestion/main.py

from fastapi import FastAPI
from graphiti_core import Graphiti
from graphiti_core.driver.falkordb_driver import FalkorDriver
from datetime import datetime, timezone
import httpx
import asyncio

app = FastAPI(title="WorldView OSINT Ingestion")

# FalkorDB connection
driver = FalkorDriver(host="localhost", port=6379, database="worldview_osint")
graphiti = Graphiti(graph_driver=driver)

BACKEND_URL = "http://localhost:3001"

async def ingest_military_flights():
    """Poll military flights and write to knowledge graph."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BACKEND_URL}/api/flights/military")
        flights = resp.json()

    for f in flights:
        episode_body = (
            f"Military aircraft {f['callsign'] or f['hex']} "
            f"({f['description'] or f['aircraftType']}) "
            f"operated by {f['operator'] or 'unknown'} "
            f"observed at {f['latitude']:.4f}, {f['longitude']:.4f} "
            f"altitude {f['altitudeFeet']}ft heading {f['heading']}° "
            f"speed {f['velocityKnots']}kt. "
            f"{'LADD-BLOCKED. ' if f.get('isLADD') else ''}"
            f"{'EMERGENCY SQUAWK {}'.format(f['squawk']) if f.get('emergency') else ''}"
        )

        await graphiti.add_episode(
            name=f"mil_flight_{f['hex']}",
            episode_body=episode_body,
            source_description="Airplanes.live ADS-B",
            reference_time=datetime.now(timezone.utc),
            group_id="osint_flights",
        )

async def ingest_firms_hotspots():
    """Poll FIRMS thermal anomalies and write to knowledge graph."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BACKEND_URL}/api/firms")
        hotspots = resp.json()

    for h in hotspots:
        is_strike = (h['daynight'] == 'N' and h['frp'] > 50
                     and h['confidence'] == 'h')

        episode_body = (
            f"Thermal anomaly detected at {h['latitude']:.4f}, {h['longitude']:.4f} "
            f"FRP={h['frp']}MW brightness={h['brightness']}K "
            f"confidence={h['confidence']} "
            f"{'NIGHTTIME ' if h['daynight'] == 'N' else 'DAYTIME '}"
            f"acquired {h['acq_date']} {h['acq_time']}Z. "
            f"{'POTENTIAL STRIKE SIGNATURE. ' if is_strike else ''}"
        )

        await graphiti.add_episode(
            name=f"firms_{h['latitude']}_{h['longitude']}_{h['acq_time']}",
            episode_body=episode_body,
            source_description="NASA FIRMS VIIRS",
            reference_time=datetime.now(timezone.utc),
            group_id="osint_firms",
        )

async def ingest_conflict_events():
    """Poll GDELT conflict events and write to knowledge graph."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BACKEND_URL}/api/gdelt")
        data = resp.json()

    for feature in (data.get('features') or []):
        props = feature.get('properties', {})
        coords = feature.get('geometry', {}).get('coordinates', [0, 0])

        episode_body = (
            f"Conflict event: {props.get('name', 'Unknown')} "
            f"at {coords[1]:.4f}, {coords[0]:.4f}. "
            f"Goldstein={props.get('goldstein', 0)} "
            f"Tone={props.get('tone', 0)} "
            f"Source: {props.get('domain', 'unknown')} "
            f"Country: {props.get('sourcecountry', 'unknown')}. "
            f"URL: {props.get('url', '')}"
        )

        await graphiti.add_episode(
            name=f"gdelt_{props.get('url', 'unknown')[:80]}",
            episode_body=episode_body,
            source_description="GDELT Project",
            reference_time=datetime.now(timezone.utc),
            group_id="osint_gdelt",
        )

async def ingest_vessels():
    """Poll AIS vessel data and write to knowledge graph."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BACKEND_URL}/api/ships?moving=1")
        ships = resp.json()

    for s in ships:
        episode_body = (
            f"Vessel {s['name'] or s['mmsi']} (MMSI: {s['mmsi']}) "
            f"{'IMO: {} '.format(s['imo']) if s.get('imo') else ''}"
            f"flag: {s.get('country', 'unknown')} "
            f"type: {s.get('shipType', 'unknown')} "
            f"at {s['latitude']:.4f}, {s['longitude']:.4f} "
            f"SOG={s['sog']}kt COG={s.get('cog', 'N/A')}° "
            f"heading={s.get('heading', 'N/A')}° "
            f"destination: {s.get('destination', 'N/A')}"
        )

        await graphiti.add_episode(
            name=f"vessel_{s['mmsi']}",
            episode_body=episode_body,
            source_description="AISStream.io",
            reference_time=datetime.now(timezone.utc),
            group_id="osint_maritime",
        )

# Background ingestion loop
async def ingestion_loop():
    """Run all ingestion tasks on their respective intervals."""
    while True:
        tasks = [
            (ingest_military_flights, 15),      # Every 15s
            (ingest_firms_hotspots, 300),        # Every 5min
            (ingest_conflict_events, 900),       # Every 15min
            (ingest_vessels, 60),                 # Every 60s
        ]
        # Run all concurrently
        await asyncio.gather(
            *[task() for task, _ in tasks],
            return_exceptions=True
        )
        await asyncio.sleep(15)  # Shortest interval

@app.on_event("startup")
async def startup():
    await graphiti.build_indices_and_constraints()
    asyncio.create_task(ingestion_loop())

@app.get("/health")
async def health():
    return {"status": "ok", "graph": "worldview_osint"}
```

### Temporal Querying

Graphiti's bi-temporal model gives us point-in-time graph reconstruction for free:

```cypher
// What was the state of the graph at a specific time?
MATCH (n)-[r]->(m)
WHERE r.valid_at <= datetime('2026-03-01T04:30:00Z')
  AND (r.invalid_at IS NULL
       OR r.invalid_at > datetime('2026-03-01T04:30:00Z'))
RETURN n, r, m

// Timeline of a specific aircraft's observations
MATCH (a:Aircraft {hex: 'ae1234'})-[obs:OBSERVED_AT]->(loc:Location)
RETURN loc.name, obs.lat, obs.lon, obs.alt, obs.timestamp
ORDER BY obs.timestamp

// Vessel route history with course changes
MATCH (v:Vessel {mmsi: '123456789'})-[t:TRANSITED]->(loc:Location)
RETURN loc.name, t.sog, t.cog, t.timestamp
ORDER BY t.timestamp
```

---

## 9. Phase 2: Engram Reasoning Audit Trail

### Integration Point

Engram captures AI agent reasoning as versioned Git objects. In the OSINT platform, it provides:

1. **Correlation audit trails** — when the system flags a thermal anomaly + military aircraft proximity as a potential strike, Engram records WHY: which data points were correlated, what thresholds were applied, what confidence was assigned.

2. **Analyst query provenance** — when an analyst asks "What military activity was near the Strait of Hormuz this week?" via GraphRAG, Engram captures the Cypher queries generated, the subgraph traversed, and the LLM synthesis steps.

3. **Intelligence product sourcing** — every conclusion in a generated report traces back to specific data points with timestamps and source APIs.

### Engram Checkpoint Pattern

```python
from engram import Checkpoint

# When correlation engine detects a pattern
async def record_correlation(aircraft, anomaly, distance_km, time_delta):
    checkpoint = Checkpoint(
        agent_id="worldview-correlation-engine",
        action="cross_layer_correlation",
        reasoning={
            "pattern": "aircraft_thermal_proximity",
            "aircraft_hex": aircraft['hex'],
            "aircraft_callsign": aircraft['callsign'],
            "aircraft_operator": aircraft['operator'],
            "anomaly_lat": anomaly['latitude'],
            "anomaly_lon": anomaly['longitude'],
            "anomaly_frp": anomaly['frp'],
            "distance_km": distance_km,
            "time_delta_minutes": time_delta,
            "confidence": calculate_confidence(distance_km, time_delta, anomaly['frp']),
            "thresholds_applied": {
                "max_distance_km": 50,
                "max_time_delta_min": 30,
                "min_frp_mw": 50,
                "required_daynight": "N",
            },
            "data_sources": [
                "Airplanes.live /v2/mil",
                "NASA FIRMS VIIRS_SNPP_NRT",
            ],
        },
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    await checkpoint.commit()

# When GraphRAG answers an analyst query
async def record_query_provenance(query, cypher_generated, subgraph, answer):
    checkpoint = Checkpoint(
        agent_id="worldview-graphrag",
        action="analyst_query",
        reasoning={
            "natural_language_query": query,
            "cypher_queries_generated": cypher_generated,
            "subgraph_nodes_traversed": len(subgraph.nodes),
            "subgraph_edges_traversed": len(subgraph.edges),
            "llm_model": "claude-sonnet-4-5-20250929",
            "answer_summary": answer[:500],
            "sources_cited": extract_sources(subgraph),
        },
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    await checkpoint.commit()
```

### Engram + AgentOps Control Plane

This connects directly to The Attic AI's AgentOps product. The OSINT platform becomes a reference implementation:
- Engram captures reasoning at every decision point
- AgentOps Control Plane provides the governance dashboard
- Government customers get the audit trail they need for intelligence products

---

## 10. Phase 2: Cross-Layer Correlation Engine

### Correlation Rules

The engine runs periodically (every 30s) and executes pattern-matching queries across the knowledge graph:

**Rule 1: Aircraft-Thermal Proximity**
```cypher
// Military aircraft observed within 50km of a high-FRP nighttime thermal anomaly
// within a 30-minute window
MATCH (a:Aircraft {isMilitary: true}),
      (f:ThermalAnomaly {daynight: 'N', confidence: 'h'})
WHERE f.frp > 50
  AND point.distance(
    point({latitude: a.lat, longitude: a.lon}),
    point({latitude: f.latitude, longitude: f.longitude})
  ) < 50000
  AND abs(a.lastSeen - f.timestamp) < 1800000
  AND NOT EXISTS((a)-[:PROXIMATE_TO]->(f))
CREATE (a)-[:PROXIMATE_TO {
  distance_km: point.distance(...) / 1000,
  time_delta_min: abs(a.lastSeen - f.timestamp) / 60000,
  confidence: CASE
    WHEN point.distance(...) < 10000 AND abs(...) < 600000 THEN 'high'
    WHEN point.distance(...) < 25000 AND abs(...) < 1200000 THEN 'medium'
    ELSE 'low'
  END,
  detected_at: datetime()
}]->(f)
```

**Rule 2: Thermal-Conflict Correlation**
```cypher
// Thermal anomaly near a GDELT conflict event within 2 hours
MATCH (f:ThermalAnomaly),
      (e:ConflictEvent {eventType: 'conflict'})
WHERE point.distance(
    point({latitude: f.latitude, longitude: f.longitude}),
    point({latitude: e.latitude, longitude: e.longitude})
  ) < 100000
  AND abs(f.timestamp - e.timestamp) < 7200000
  AND NOT EXISTS((f)-[:CORRELATED_WITH]->(e))
CREATE (f)-[:CORRELATED_WITH {
  distance_km: point.distance(...) / 1000,
  time_delta_min: abs(f.timestamp - e.timestamp) / 60000,
  confidence: 'medium',
  detected_at: datetime()
}]->(e)
```

**Rule 3: Vessel Diversion Detection**
```cypher
// Vessel with significant course change (>30°) near a conflict zone
MATCH (v:Vessel)-[t1:TRANSITED]->(loc1:Location),
      (v)-[t2:TRANSITED]->(loc2:Location),
      (e:ConflictEvent)-[:REPORTED_AT]->(eloc:Location)
WHERE t2.timestamp > t1.timestamp
  AND t2.timestamp - t1.timestamp < 3600000
  AND abs(t2.cog - t1.cog) > 30
  AND point.distance(
    point({latitude: loc1.lat, longitude: loc1.lon}),
    point({latitude: eloc.lat, longitude: eloc.lon})
  ) < 200000
CREATE (v)-[:DIVERTED_NEAR {
  old_cog: t1.cog,
  new_cog: t2.cog,
  course_change_deg: abs(t2.cog - t1.cog),
  distance_to_conflict_km: point.distance(...) / 1000,
  detected_at: datetime()
}]->(e)
```

**Rule 4: Airspace Violation Detection**
```cypher
// Aircraft entering known restricted airspace
MATCH (a:Aircraft),
      (z:Airspace {type: 'TFR'})
WHERE point.withinBBox(
    point({latitude: a.lat, longitude: a.lon}),
    z.bbox_sw, z.bbox_ne
  )
  AND NOT EXISTS((a)-[:ENTERED_AIRSPACE]->(z))
CREATE (a)-[:ENTERED_AIRSPACE {
  timestamp: datetime(),
  altitude: a.alt,
  heading: a.heading
}]->(z)
```

---

## 11. Phase 2: GraphRAG Natural Language Query Interface

### Setup

```python
from falkordb import FalkorDB
from graphrag_sdk import KnowledgeGraph
from graphrag_sdk.ontology import Ontology
from graphrag_sdk.models.litellm import LiteModel
from graphrag_sdk.model_config import KnowledgeGraphModelConfig

db = FalkorDB(host="localhost", port=6379)
graph = db.select_graph("worldview_osint")

# Extract ontology from existing knowledge graph
ontology = Ontology.from_kg_graph(graph)

# Configure with Claude or GPT
model = LiteModel(model_name="anthropic/claude-sonnet-4-5-20250929")
model_config = KnowledgeGraphModelConfig.with_model(model)

kg = KnowledgeGraph(
    name="worldview_osint",
    model_config=model_config,
    ontology=ontology,
    host="localhost",
    port=6379,
)
```

### Example Queries

An analyst types natural language; GraphRAG translates to Cypher, executes against FalkorDB, and synthesizes results:

| Natural Language Query | Generated Cypher Pattern |
|----------------------|-------------------------|
| "What military aircraft were near the Strait of Hormuz in the last 6 hours?" | `MATCH (a:Aircraft {isMilitary:true})-[:OBSERVED_AT]->(l:Location) WHERE l.name CONTAINS 'Hormuz'...` |
| "Show me all thermal anomalies correlated with GDELT conflict events" | `MATCH (f:ThermalAnomaly)-[:CORRELATED_WITH]->(e:ConflictEvent) RETURN f, e...` |
| "Which vessels changed course near active conflict zones today?" | `MATCH (v:Vessel)-[:DIVERTED_NEAR]->(e:ConflictEvent) WHERE e.eventType = 'conflict'...` |
| "Reconstruct the timeline of events in the Persian Gulf between 0200-0600 UTC" | Point-in-time temporal query across all entity types |

### REST API for Frontend

```python
@app.post("/api/query")
async def natural_language_query(request: QueryRequest):
    """Natural language OSINT query endpoint."""
    chat = kg.chat_session()
    response = chat.send_message(request.query)

    # Record provenance via Engram
    await record_query_provenance(
        query=request.query,
        cypher_generated=chat.last_cypher,
        subgraph=chat.last_subgraph,
        answer=response,
    )

    return {"answer": response, "sources": chat.sources}
```

---

## 12. Phase 2: Docker Compose Full Stack

```yaml
version: '3.8'

services:
  # FalkorDB — replaces standalone Redis, serves as graph DB
  falkordb:
    image: falkordb/falkordb:latest
    ports:
      - "6379:6379"   # Redis wire protocol (existing node-cache compatible)
      - "3000:3000"   # FalkorDB Browser UI
    volumes:
      - falkordb_data:/var/lib/falkordb/data
    environment:
      - FALKORDB_ARGS=--requirepass ""
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Express backend — existing Node.js server
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "3001:3001"
    env_file:
      - server/.env
    depends_on:
      falkordb:
        condition: service_healthy

  # Python ingestion service — Graphiti + correlation engine
  ingestion:
    build:
      context: .
      dockerfile: Dockerfile.ingestion
    ports:
      - "8000:8000"
    environment:
      - FALKORDB_HOST=falkordb
      - FALKORDB_PORT=6379
      - BACKEND_URL=http://backend:3001
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      falkordb:
        condition: service_healthy
      backend:
        condition: service_started

  # Vite frontend — React + CesiumJS
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_GOOGLE_API_KEY=${VITE_GOOGLE_API_KEY}
      - VITE_CESIUM_ION_TOKEN=${VITE_CESIUM_ION_TOKEN}
    depends_on:
      - backend
      - ingestion

volumes:
  falkordb_data:
```

---

## 13. Phase 2: Build Order & Milestones

### Sprint 1 (Week 1-2): FalkorDB Foundation

- [ ] Add FalkorDB to Docker Compose, verify Redis wire protocol compatibility with existing node-cache
- [ ] Define OSINT ontology in Cypher (CREATE CONSTRAINT statements)
- [ ] Seed Location nodes (military bases, chokepoints, major airports)
- [ ] Create Python ingestion service scaffold (FastAPI + FalkorDB driver)
- [ ] Implement military flight ingestion (simplest data source)
- [ ] Verify temporal data in FalkorDB Browser UI

**Exit criteria:** Military aircraft observations visible as graph nodes with temporal edges in FalkorDB Browser.

### Sprint 2 (Week 3-4): Full Ingestion + Correlation

- [ ] Add FIRMS thermal anomaly ingestion
- [ ] Add GDELT conflict event ingestion
- [ ] Add AIS vessel ingestion
- [ ] Implement correlation Rule 1 (aircraft-thermal proximity)
- [ ] Implement correlation Rule 2 (thermal-conflict correlation)
- [ ] Add Engram checkpoints at correlation detection points
- [ ] Intel feed integration: push correlation alerts to frontend WebSocket

**Exit criteria:** Cross-layer correlations appearing automatically in the knowledge graph. Engram capturing reasoning for each correlation.

### Sprint 3 (Week 5-6): GraphRAG + Timeline

- [ ] Install GraphRAG-SDK, connect to FalkorDB ontology
- [ ] Build `/api/query` REST endpoint for natural language queries
- [ ] Add query input component to frontend OperationsPanel
- [ ] Build timeline scrubber UI component (leveraging Graphiti temporal queries)
- [ ] Implement point-in-time graph reconstruction for historical replay
- [ ] Connect Engram to query provenance recording

**Exit criteria:** Analyst can type natural language queries and get graph-backed answers. Timeline scrubber replays historical state.

### Sprint 4 (Week 7-8): Polish + Demo

- [ ] Additional correlation rules (vessel diversion, airspace violation)
- [ ] GraphRAG answer rendering in frontend (cited sources, confidence)
- [ ] Engram audit trail viewer component
- [ ] NOTAM/airspace restriction layer (Laminar Data Hub)
- [ ] Performance optimization: batch ingestion, query caching
- [ ] Demo recording for gov customer presentations
- [ ] Documentation: API reference, deployment guide, analyst handbook

**Exit criteria:** Demo-ready platform suitable for government customer presentations. Engram audit trail visible for every automated conclusion.

---

## 14. API Key Registry

| Service | Cost | Required | Registration URL |
|---------|------|----------|-----------------|
| Airplanes.live | **Free** | No key needed | — |
| GDELT | **Free** | No key needed | — |
| USGS Earthquakes | **Free** | No key needed | — |
| CelesTrak | **Free** | No key needed | — |
| adsb.fi | **Free** | No key needed | — |
| NASA FIRMS | **Free** | Optional (higher limits) | `firms.modaps.eosdis.nasa.gov/api` |
| AISStream.io | **Free** | Yes | `aisstream.io` |
| OpenSky Network | **Free** | Yes (OAuth2) | `opensky-network.org` |
| Google Maps | Free tier | Recommended | `console.cloud.google.com` |
| Cesium Ion | Free tier | Optional | `ion.cesium.com` |
| TfL London | **Free** | No key needed | — |
| Austin TX | **Free** | No key needed | — |
| Transport NSW | **Free** | Yes | `opendata.transport.nsw.gov.au` |
| FalkorDB | **Free** (SSPL) | Self-hosted | `docker pull falkordb/falkordb` |
| OpenAI (GraphRAG) | Paid | For Phase 2 | `platform.openai.com` |
| Anthropic (GraphRAG) | Paid | For Phase 2 (alt) | `console.anthropic.com` |

---

## 15. Legal & Ethical Considerations

### ADS-B Data

ADS-B reception is legal (unencrypted 1090 MHz broadcast). The 2024 FAA Reauthorization Act (Section 803) mandates protection of private aircraft owners' PII. The Pilot and Aircraft Privacy Act (PAPA, H.R.4146) is pending — would restrict ADS-B use to air traffic safety only. Key risk: linking flight data to identifiable individuals and publishing movements creates privacy/stalking liability. Time-delay display of sensitive military movements recommended.

### AIS Data

IMO Maritime Safety Committee "condemned" web publication of AIS data in 2004 (non-binding resolution). SOLAS allows military vessels to disable AIS during operations. China Data Security Law (2021) caused ~90% drop in AIS data in Chinese waters. Publishing military vessel positions raises ethical and national security concerns.

### Satellite Imagery

US "shutter control" has never been formally invoked. Kyl-Bingaman Amendment restricts US companies from selling Israel imagery at higher resolution than non-US commercial sources. Open-source OSINT aggregation using public APIs does NOT trigger ITAR/EAR export controls.

### GDPR

Applies to EU residents' data even if publicly available. "Publicly available ≠ freely usable." Anonymize and aggregate social media geotagged content. Source identification in conflict zones could endanger lives.

### Best Practices

- Bellingcat Ethics Committee guidelines + Berkeley Protocol on Digital Open Source Investigations
- Transparency about methods, do-no-harm principle, public interest test
- Time-delayed display of sensitive military movements
- Never link tracking data to identifiable individuals
- Engram audit trail provides accountability for automated analysis
