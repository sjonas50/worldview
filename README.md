<p align="center">
  <img src="https://img.shields.io/badge/WORLDVIEW-OSINT%20Intelligence%20Platform-00D4FF?style=for-the-badge&labelColor=0A0A0A" alt="WorldView" />
</p>

<h1 align="center">WORLDVIEW — Real-Time OSINT Intelligence Platform</h1>

<p align="center">
  A real-time global OSINT intelligence platform built on a 3D CesiumJS globe with a FalkorDB knowledge graph.<br/>
  9 live data layers — military flights, commercial aviation, naval vessels, satellites, thermal anomalies, conflict events, earthquakes, traffic, and CCTV — with cross-layer correlation and a tactical command interface.
</p>

https://github.com/user-attachments/assets/b2bd05d2-f7be-49c8-a8c6-452b6b60cb34

<p align="center">
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white" alt="React 19" />
  <img src="https://img.shields.io/badge/TypeScript-5.9-3178C6?logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/CesiumJS-1.138-6CADDF?logo=cesium&logoColor=white" alt="CesiumJS" />
  <img src="https://img.shields.io/badge/FalkorDB-Knowledge%20Graph-FF6B6B?logo=redis&logoColor=white" alt="FalkorDB" />
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Vite-7-646CFF?logo=vite&logoColor=white" alt="Vite 7" />
  <img src="https://img.shields.io/badge/Express-5-000000?logo=express&logoColor=white" alt="Express 5" />
</p>

---

## Overview

WorldView is a full-stack OSINT intelligence platform that aggregates 9 real-time data sources onto an interactive 3D globe, backed by a FalkorDB knowledge graph with automated cross-layer correlation. The system detects patterns across data layers — such as military aircraft near thermal anomalies or conflict events correlated with FIRMS hotspots — and surfaces intelligence alerts through the tactical UI.

### Data Layers

| Layer | Source | Update Rate | Description |
|---|---|---|---|
| **Military Flights** | Airplanes.live | 10 s | Unfiltered military aircraft incl. LADD-blocked, emergency squawks |
| **Commercial Flights** | FlightRadar24 + adsb.fi | 5–20 s | ~27,000 global aircraft with altitude bands, routes, dead-reckoning |
| **Naval / AIS** | AISStream.io WebSocket | 30 s | Global vessel tracking — cargo, tanker, military, fishing |
| **Satellites** | CelesTrak TLE + SGP4 | 2 s propagation | Real-time orbital position with orbit paths and ground tracks |
| **FIRMS Thermal** | NASA VIIRS | 5 min | Thermal anomalies / fire detection — strike signature analysis |
| **Conflict Events** | GDELT Project | 15 min | Geolocated conflict/military/diplomatic events with Goldstein scale |
| **Earthquakes** | USGS GeoJSON | 60 s | Past 24 hours, magnitude-scaled pulsing markers |
| **Traffic** | OpenStreetMap Overpass | On-demand | Road network overlay with animated vehicle simulation |
| **CCTV** | TfL, Austin TX, Transport NSW | 5 min | Live camera feeds from London, Austin, and New South Wales |

### Knowledge Graph (FalkorDB)

The ingestion service continuously writes OSINT data into a FalkorDB knowledge graph, enabling:

- **Temporal observation tracking** — Aircraft, vessel, and anomaly positions stored as graph edges with timestamps
- **Cross-layer correlation** — Automated detection of intelligence-relevant patterns:
  - Rule 1: Military aircraft within 50km of high-FRP nighttime thermal anomaly (30-min window)
  - Rule 2: Thermal anomaly within 100km of GDELT conflict event (2-hour window)
- **Correlation audit trail** — Every detected pattern stored with confidence level, thresholds applied, and source data
- **291 seeded locations** — 18 military bases, 12 strategic chokepoints, 261 airports

---

## Tech Stack

### Frontend
- **React 19** + **TypeScript 5.9** — Strict mode, functional components
- **CesiumJS 1.138** via **Resium** — 3D globe with imperative rendering for 27K+ entities
- **Tailwind CSS v4** — Custom tactical colour tokens (`wv-*`)
- **Vite 7** — Dev server with HMR, Cesium plugin, API proxy
- **GLSL post-processing** — CRT scanlines, night vision (NVG), thermal (FLIR)

### Backend
- **Express 5** — API proxy with node-cache, WebSocket, credential management
- **FastAPI** (Python 3.12) — OSINT ingestion service with 5 independent polling loops
- **FalkorDB** — Graph database (OpenCypher) for knowledge graph + correlation engine
- **Docker Compose** — FalkorDB + ingestion service (Express/Vite run natively)

### Rendering
- **Imperative Cesium primitives** — `BillboardCollection`, `PointPrimitiveCollection`, `PolylineCollection` for 60fps at scale
- **Dead-reckoning** — Aircraft and vessel positions extrapolated between API updates
- **SGP4 propagation** — Real-time satellite positioning from TLE orbital elements
- **CallbackProperty** — Smooth entity tracking without React re-renders

---

## Getting Started

### Prerequisites

- **Node.js** >= 18
- **Docker Desktop** (for FalkorDB + ingestion service)
- **npm** >= 9

### Installation

```bash
git clone https://github.com/sjonas50/worldview.git
cd worldview
npm install
```

### Environment Setup

Copy the example files and add your API keys:

```bash
cp .env.example .env
cp server/.env.example server/.env
```

**`.env`** — Client-side:

| Variable | Required? | Purpose |
|---|---|---|
| `VITE_GOOGLE_API_KEY` | Optional | Google Maps 3D Photorealistic Tiles (falls back to OSM) |
| `VITE_CESIUM_ION_TOKEN` | Optional | Cesium Ion terrain/imagery |
| `NSW_TRANSPORT_API_KEY` | Optional | Transport for NSW CCTV cameras |

**`server/.env`** — Server-side:

| Variable | Required? | Purpose |
|---|---|---|
| `NASA_FIRMS_MAP_KEY` | Optional | NASA FIRMS thermal anomaly data (higher rate limits) |
| `AISSTREAM_API_KEY` | Optional | AISStream.io global AIS ship tracking |
| `OPENSKY_CLIENT_ID` | Optional | OpenSky Network OAuth2 |
| `OPENSKY_CLIENT_SECRET` | Optional | OpenSky Network OAuth2 |

> All layers degrade gracefully when keys are missing. Flights, earthquakes, satellites, and GDELT work without any API keys.

### Running

```bash
# Start FalkorDB + ingestion service (Docker)
docker compose up -d

# Start Express backend + Vite frontend
npm run dev:all
```

| Service | URL | Description |
|---|---|---|
| **Frontend** | http://localhost:5173 | 3D globe + tactical UI |
| **Express API** | http://localhost:3001 | Backend proxy |
| **Ingestion API** | http://localhost:8000 | Health, stats, correlations |
| **FalkorDB Browser** | http://localhost:3000 | Graph visualisation (select `worldview_osint`) |

### Useful Cypher Queries (FalkorDB Browser)

```cypher
-- Aircraft observations near military bases
MATCH (a:Aircraft)-[r:OBSERVED_AT]->(l:Location) RETURN a, r, l LIMIT 20

-- Top operators by aircraft count
MATCH (o:Operator)<-[:OPERATED_BY]-(a) RETURN o.name, count(a) ORDER BY count(a) DESC

-- Cross-layer correlations
MATCH (a:Aircraft)-[r:PROXIMATE_TO]->(t:ThermalAnomaly) RETURN a.hex, t.id, r.confidence

-- Correlation audit trail
MATCH (alert:CorrelationAlert) RETURN alert.summary, alert.confidence ORDER BY alert.detectedAt DESC
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Browser (localhost:5173)                       │
│  React 19 + CesiumJS 3D Globe + 9 Data Layers + Tactical UI    │
└──────────────────────────────┬──────────────────────────────────┘
                               │ /api/* proxy
┌──────────────────────────────▼──────────────────────────────────┐
│                Express Proxy Server (:3001)                       │
│  node-cache (TTL) │ WebSocket │ REST endpoints (12+ routes)     │
└────────┬─────────────────────────────────────────┬──────────────┘
         │                                         │ /api/correlations proxy
    ┌────▼────────────────────┐          ┌─────────▼──────────────┐
    │    External APIs         │          │  Ingestion Service      │
    │  FlightRadar24, adsb.fi │          │  FastAPI (:8000)        │
    │  Airplanes.live         │◄─────────│  5 polling loops        │
    │  NASA FIRMS, GDELT      │  HTTP    │  Correlation engine     │
    │  AISStream.io, USGS     │  polls   │  Audit trail alerts     │
    │  CelesTrak, TfL, etc.  │          └─────────┬──────────────┘
    └─────────────────────────┘                    │
                                         ┌─────────▼──────────────┐
                                         │  FalkorDB (:6379)       │
                                         │  Knowledge Graph        │
                                         │  Aircraft, Vessel,      │
                                         │  ThermalAnomaly,        │
                                         │  ConflictEvent,         │
                                         │  CorrelationAlert       │
                                         │  Browser UI (:3000)     │
                                         └────────────────────────┘
```

### Knowledge Graph Ontology

**Nodes:** Aircraft, Vessel, ThermalAnomaly, ConflictEvent, Location, Operator, CorrelationAlert

**Relationships:**
- `(Aircraft)-[:OBSERVED_AT]->(Location)` — temporal position edges
- `(Vessel)-[:OBSERVED_AT]->(Location)` — temporal position edges
- `(Aircraft)-[:OPERATED_BY]->(Operator)` — military operator
- `(ThermalAnomaly)-[:DETECTED_NEAR]->(Location)` — nearest base/airport/chokepoint
- `(ConflictEvent)-[:REPORTED_NEAR]->(Location)` — nearest seeded location
- `(Aircraft)-[:PROXIMATE_TO]->(ThermalAnomaly)` — correlation Rule 1
- `(ThermalAnomaly)-[:CORRELATED_WITH]->(ConflictEvent)` — correlation Rule 2
- `(CorrelationAlert)-[:GENERATED_FROM]->(entity)` — audit trail

---

## Features

### Entity Tracking
Click any entity on the globe to lock the camera. Press **ESC** to unlock.

### Optics Modes (GLSL Post-Processing)

| Mode | Effect |
|---|---|
| **Standard** | No post-processing |
| **CRT** | Scanlines, chromatic aberration, barrel distortion, vignette |
| **NVG** | Green phosphor, noise grain, bloom |
| **FLIR** | White-hot thermal palette, Sobel edge detection |

### Intel Feed
Real-time event stream from all data sources plus correlation alerts. Colour-coded by source type with tactical labels (ACFT, MIL, AIS, FIRE, GDLT, CORR).

### Dual Flight Data Strategy
Global coverage from FlightRadar24 (7 zones, 20s), enriched with high-frequency regional data from adsb.fi (250nm radius, 5s). Deduplicated by ICAO24 with route cross-referencing.

---

## API Endpoints

### Express Backend (:3001)

| Method | Endpoint | Cache | Description |
|---|---|---|---|
| `GET` | `/api/flights` | 30s | Global aircraft (FR24 + adsb.fi fallback) |
| `GET` | `/api/flights/live` | 4s | Regional high-freq aircraft |
| `GET` | `/api/flights/military` | 8s | Military aircraft (Airplanes.live) |
| `GET` | `/api/ships` | 60s | AIS vessels (burst WebSocket) |
| `GET` | `/api/firms` | 5min | NASA FIRMS thermal anomalies |
| `GET` | `/api/gdelt` | 15min | GDELT conflict events (GeoJSON) |
| `GET` | `/api/satellites` | 2hr | TLE orbital data |
| `GET` | `/api/earthquakes` | 60s | USGS seismic feed |
| `GET` | `/api/cctv` | 5min | Aggregated CCTV cameras |
| `GET` | `/api/correlations` | — | Proxy to ingestion service |

### Ingestion Service (:8000)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | FalkorDB connectivity + aircraft count |
| `GET` | `/stats` | All node/edge counts |
| `GET` | `/correlations` | Recent correlation alerts |

---

## Project Structure

```
worldview/
├── server/                           # Express backend proxy
│   ├── index.js                      # 12+ API routes, WebSocket, AIS burst, caching
│   └── .env                          # Server secrets
├── ingestion/                        # Python OSINT ingestion service
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── src/worldview_ingestion/
│       ├── main.py                   # FastAPI app, 5 polling loops, /health, /stats, /correlations
│       ├── config.py                 # Pydantic Settings
│       ├── db.py                     # FalkorDB connection
│       ├── schema.py                 # Indices + constraints (idempotent)
│       ├── models.py                 # Pydantic models (MilFlight, Vessel, FIRMSHotspot, etc.)
│       ├── utils.py                  # Haversine distance, nearest-location lookup
│       ├── ingestors/
│       │   ├── mil_flights.py        # Military aircraft → Aircraft nodes
│       │   ├── vessels.py            # AIS ships → Vessel nodes
│       │   ├── firms.py              # FIRMS hotspots → ThermalAnomaly nodes
│       │   └── gdelt.py              # GDELT events → ConflictEvent nodes
│       ├── correlations/
│       │   └── engine.py             # Rule 1 + Rule 2 + CorrelationAlert audit trail
│       └── seed/
│           └── locations.py          # 291 locations (bases, chokepoints, airports)
├── src/
│   ├── App.tsx                       # Root state management, 10 data hooks
│   ├── components/
│   │   ├── globe/                    # CesiumJS viewer + entity click handler
│   │   ├── layers/                   # 9 rendering layers (imperative Cesium primitives)
│   │   └── ui/                       # OperationsPanel, IntelFeed, StatusBar, CCTVPanel, etc.
│   ├── hooks/                        # 10 data hooks (flights, ships, satellites, FIRMS, etc.)
│   └── shaders/                      # GLSL post-processing (CRT, NVG, FLIR)
├── docker-compose.yml                # FalkorDB + ingestion service
├── .env                              # Client-side env vars
└── package.json
```

---

## Obtaining API Keys

| Service | Cost | Registration |
|---|---|---|
| Google Maps 3D Tiles | Free tier ($200/mo) | [console.cloud.google.com](https://console.cloud.google.com/) |
| Cesium Ion | Free tier | [ion.cesium.com](https://ion.cesium.com/) |
| NASA FIRMS | Free | [firms.modaps.eosdis.nasa.gov](https://firms.modaps.eosdis.nasa.gov/api/area/) |
| AISStream.io | Free | [aisstream.io](https://aisstream.io/) |
| OpenSky Network | Free | [opensky-network.org](https://opensky-network.org/) |
| Transport for NSW | Free | [opendata.transport.nsw.gov.au](https://opendata.transport.nsw.gov.au/) |

Services that require **no API key**: Airplanes.live, FlightRadar24, adsb.fi, USGS, GDELT, CelesTrak, TfL London, Austin TX, Overpass API.

---

## Security

> **No API keys, tokens, or credentials are included in this repository.**

All sensitive values are loaded from `.env` files excluded via `.gitignore`. If you fork or clone this repo, you must supply your own API keys. If you discover a credential leak, please open an issue immediately.

---

## Licence

This project is for **educational and demonstration purposes only**. External API usage is subject to each provider's terms of service. No commercial use is intended.

Built by The Attic AI.
