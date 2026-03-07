"""GraphRAG natural language query service.

Wraps graphrag_sdk to provide:
- Ontology extraction from the live FalkorDB graph
- Chat session management with TTL cleanup
- Query execution with provenance recording
"""

import asyncio
import logging
import os
import re
import time
import uuid
from datetime import datetime, timezone

from .config import Settings
from .db import get_graph
from .regions import ALIASES, REGIONS, resolve_region
from .satellite_passes import compute_passes

logger = logging.getLogger("worldview-ingestion")

# Session storage: session_id -> (chat_session, last_used_timestamp)
_sessions: dict[str, tuple] = {}
SESSION_TTL = 900  # 15 minutes


class GraphRAGService:
    """Singleton service for GraphRAG query processing."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._kg = None
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize the KnowledgeGraph with ontology from the live graph."""
        if not self.settings.graphrag_enabled:
            logger.info("GraphRAG disabled via config")
            return False

        if not self.settings.llm_api_key:
            logger.warning("GraphRAG: No LLM_API_KEY configured, skipping init")
            return False

        try:
            from graphrag_sdk import KnowledgeGraph
            from graphrag_sdk.ontology import Ontology
            from graphrag_sdk.models.litellm import LiteModel
            from graphrag_sdk.model_config import KnowledgeGraphModelConfig

            # Set the appropriate API key env var for LiteLLM
            model_name = self.settings.llm_model
            if model_name.startswith("anthropic/"):
                os.environ["ANTHROPIC_API_KEY"] = self.settings.llm_api_key
            elif model_name.startswith("openai/"):
                os.environ["OPENAI_API_KEY"] = self.settings.llm_api_key
            else:
                os.environ["OPENAI_API_KEY"] = self.settings.llm_api_key

            # Extract ontology from existing graph
            graph = get_graph(
                self.settings.falkordb_host,
                self.settings.falkordb_port,
                self.settings.falkordb_graph,
            )
            ontology = Ontology.from_kg_graph(graph)
            logger.info(
                "GraphRAG: Extracted ontology with %d entities, %d relations",
                len(ontology.entities),
                len(ontology.relations),
            )

            # Configure LLM
            model = LiteModel(model_name=model_name)
            model_config = KnowledgeGraphModelConfig.with_model(model)

            # Domain context for Cypher generation and Q&A
            cypher_instruction = (
                "You are querying a WorldView OSINT knowledge graph. "
                "The graph contains these node types:\n"
                "- Aircraft (military flights: hex, callsign, operator, isMilitary, isLADD, lastLat/Lon/Alt/Heading/Speed/Seen)\n"
                "- Flight (commercial flights: icao24, callsign, registration, aircraftType, operator, airline, originAirport, destAirport, lastLat/Lon/Alt/Heading/Speed/Seen)\n"
                "- Vessel (AIS ship tracking: mmsi, name, shipType, country, lastLat/Lon/Sog/Cog/Seen)\n"
                "- Earthquake (USGS: id, mag, place, time, longitude, latitude, depth, type, status, tsunami, sig)\n"
                "- ThermalAnomaly (NASA FIRMS hotspots: frp, brightness, confidence, daynight, acq_date/time)\n"
                "- ConflictEvent (GDELT events: name, eventType, goldstein, tone, domain, sourceCountry)\n"
                "- Location (291 seeded: airports, military bases, chokepoints, ports)\n"
                "- Operator (military operators: name, type)\n"
                "- CorrelationAlert (cross-layer correlations: ruleType, confidence, summary)\n"
                "- QueryAudit (analyst query history)\n\n"
                "Relationships: OBSERVED_AT (Aircraft/Flight/Vessel->Location with temporal edges), "
                "OPERATED_BY (Aircraft->Operator), DETECTED_NEAR (ThermalAnomaly->Location), "
                "REPORTED_NEAR (ConflictEvent->Location), OCCURRED_NEAR (Earthquake->Location), "
                "PROXIMATE_TO (Aircraft->ThermalAnomaly), "
                "CORRELATED_WITH (ThermalAnomaly->ConflictEvent).\n\n"
                "IMPORTANT: Satellites, CCTV cameras, and traffic data are NOT in the graph. "
                "If asked about these, explain they are rendered in the frontend only.\n"
                "When querying for 'flights' or 'aircraft near' a location, check BOTH Aircraft and Flight nodes.\n"
                "Generate exactly ONE Cypher query. Never generate multiple queries.\n\n"
                "Graph ontology:\n{ontology}"
            )

            qa_instruction = (
                "You are an OSINT intelligence analyst assistant for the WorldView platform. "
                "Answer questions based on the FalkorDB knowledge graph data. "
                "The graph tracks: military aircraft (Airplanes.live), commercial flights (FR24/adsb.fi), "
                "naval vessels (AISStream AIS), earthquakes (USGS), "
                "NASA FIRMS thermal anomalies, GDELT conflict events, and cross-layer correlations.\n"
                "Satellites, CCTV, and traffic are displayed on the globe but NOT stored "
                "in the knowledge graph — if asked, clarify this distinction.\n"
                "Be concise and tactical in your responses."
            )

            # Create KnowledgeGraph instance
            self._kg = KnowledgeGraph(
                name=self.settings.falkordb_graph,
                model_config=model_config,
                ontology=ontology,
                host=self.settings.falkordb_host,
                port=self.settings.falkordb_port,
                cypher_system_instruction=cypher_instruction,
                qa_system_instruction=qa_instruction,
            )

            self._initialized = True
            logger.info("GraphRAG initialized with model=%s", model_name)
            return True

        except Exception as e:
            logger.error("GraphRAG initialization failed: %s", e)
            self._initialized = False
            return False

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    # Data types NOT in the knowledge graph (frontend-only)
    # Note: "satellite" and "orbit" are handled by _check_satellite_pass_query()
    # Note: Earthquakes and commercial flights are now ingested into the graph
    _NON_GRAPH_KEYWORDS = {
        "cctv": "CCTV camera feeds are fetched directly from TfL/Austin/NSW APIs in the browser, not stored in the knowledge graph.",
        "camera": "CCTV camera data is fetched directly in the browser, not stored in the knowledge graph.",
        "traffic": "Traffic data is fetched from OpenStreetMap Overpass in the browser, not stored in the knowledge graph.",
    }

    def _check_non_graph_query(self, question: str) -> str | None:
        """Return a helpful response if the query is about non-graph data."""
        q_lower = question.lower()
        for keyword, explanation in self._NON_GRAPH_KEYWORDS.items():
            if keyword in q_lower:
                return (
                    f"{explanation} "
                    "The knowledge graph contains: military aircraft, naval vessels (AIS), "
                    "NASA FIRMS thermal anomalies, GDELT conflict events, and cross-layer correlations."
                )
        return None

    def _check_satellite_pass_query(self, question: str) -> str | None:
        """Detect satellite pass queries, compute passes, return formatted answer.

        Returns formatted markdown answer, or None if not a satellite query.
        """
        q_lower = question.lower()

        # Must mention satellites
        sat_keywords = ("satellite", "orbit", "overfly", "overflight")
        if not any(kw in q_lower for kw in sat_keywords):
            return None

        # Check for pass/overfly concept or a known region
        pass_keywords = (
            "pass", "over", "above", "coverage", "overfl",
            "flew", "fly", "visible", "track", "monitor",
        )
        has_pass_concept = any(kw in q_lower for kw in pass_keywords)

        # Try to find a region in the query
        detected_region: str | None = None
        for region_key in REGIONS:
            readable = region_key.replace("_", " ")
            if readable in q_lower or region_key in q_lower:
                detected_region = region_key
                break
        if detected_region is None:
            for alias, canonical in ALIASES.items():
                if alias in q_lower:
                    detected_region = canonical
                    break

        if detected_region is None or not has_pass_concept:
            region_list = ", ".join(sorted(REGIONS.keys())[:12])
            return (
                "I can compute satellite passes over strategic regions using SGP4 propagation. "
                "Try asking: 'What satellites passed over [region] in the last [N] hours?'\n\n"
                f"Available regions: {region_list}, ..."
            )

        # Parse time window
        hours = 24.0
        direction = "past"

        past_match = re.search(
            r"(?:last|past|previous)\s+(\d+\.?\d*)\s*(?:hour|hr|h|day)",
            q_lower,
        )
        if past_match:
            val = float(past_match.group(1))
            if "day" in past_match.group(0):
                val *= 24
            hours = val
            direction = "past"

        future_match = re.search(
            r"(?:next|coming|upcoming|future)\s+(\d+\.?\d*)\s*(?:hour|hr|h|day)",
            q_lower,
        )
        if future_match:
            val = float(future_match.group(1))
            if "day" in future_match.group(0):
                val *= 24
            hours = val
            direction = "future"

        # Detect satellite group
        group = "active"
        if "weather" in q_lower:
            group = "weather"
        elif "gps" in q_lower:
            group = "gps"
        elif "starlink" in q_lower:
            group = "starlink"
        elif "station" in q_lower or "iss" in q_lower:
            group = "stations"
        elif "military" in q_lower:
            group = "military"

        hours = min(max(hours, 0.5), 72.0)

        # Run async computation from sync context (we're in asyncio.to_thread)
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(
                compute_passes(
                    region=detected_region,
                    hours=hours,
                    direction=direction,
                    group=group,
                    max_results=50,
                )
            )
            loop.close()
        except Exception as e:
            logger.error("Satellite pass computation failed: %s", e)
            return f"Satellite pass computation failed: {e}"

        if result.get("error"):
            return f"Error: {result['error']}"

        # Format answer
        total = result["total_passes"]
        sats_checked = result["satellites_checked"]
        window_start = result["window_start"][:19]
        window_end = result["window_end"][:19]
        region_name = detected_region.replace("_", " ").title()
        dir_label = "passed over" if direction == "past" else "will pass over"

        lines = [
            f"**{total} satellite passes** {dir_label} "
            f"**{region_name}** ({sats_checked} satellites checked, "
            f"{window_start} to {window_end} UTC).\n"
        ]

        if total == 0:
            lines.append(
                "No passes detected in this window. "
                "Try a longer window or different satellite group."
            )
        else:
            for i, p in enumerate(result["passes"][:15], 1):
                enter = p["enter_time"][11:19]
                exit_t = p["exit_time"][11:19]
                lines.append(
                    f"{i}. **{p['name']}** (NORAD {p['norad_id']}) "
                    f"— {enter} to {exit_t} UTC "
                    f"({p['duration_minutes']} min, "
                    f"alt {p['peak_altitude_km']} km)"
                )
            if total > 15:
                lines.append(
                    f"\n... and {total - 15} more passes. "
                    "Use `/api/satellite-passes` for full results."
                )

        perf = result.get("performance", {})
        lines.append(
            f"\n_Computed in {perf.get('compute_seconds', '?')}s "
            f"({perf.get('total_propagations', '?'):,} propagations)_"
        )

        return "\n".join(lines)

    def query(self, question: str, session_id: str | None = None) -> dict:
        """Execute a natural language query against the knowledge graph."""
        if not self._initialized or not self._kg:
            return {
                "answer": "GraphRAG is not initialized. Check LLM_API_KEY configuration.",
                "error": True,
                "session_id": session_id or "",
            }

        # Check for satellite pass queries (on-demand SGP4 computation)
        sat_answer = self._check_satellite_pass_query(question)
        if sat_answer:
            timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
            session_id = session_id or f"sess_{uuid.uuid4().hex[:12]}"
            self._record_provenance(question, sat_answer, session_id)
            return {
                "answer": sat_answer,
                "session_id": session_id,
                "query": question,
                "timestamp": timestamp,
                "error": False,
            }

        # Check for queries about data not in the graph
        non_graph_answer = self._check_non_graph_query(question)
        if non_graph_answer:
            timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
            session_id = session_id or f"sess_{uuid.uuid4().hex[:12]}"
            self._record_provenance(question, non_graph_answer, session_id)
            return {
                "answer": non_graph_answer,
                "session_id": session_id,
                "query": question,
                "timestamp": timestamp,
                "error": False,
            }

        # Get or create chat session
        if session_id and session_id in _sessions:
            chat, _ = _sessions[session_id]
            _sessions[session_id] = (chat, time.time())
        else:
            session_id = session_id or f"sess_{uuid.uuid4().hex[:12]}"
            chat = self._kg.chat_session()
            _sessions[session_id] = (chat, time.time())

        try:
            response = chat.send_message(question)
            answer = (
                response.get("response", str(response))
                if isinstance(response, dict)
                else str(response)
            )

            # Record provenance
            self._record_provenance(question, answer, session_id)

            return {
                "answer": answer,
                "session_id": session_id,
                "query": question,
                "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                "error": False,
            }
        except Exception as e:
            logger.error("GraphRAG query error: %s", e)
            error_str = str(e).lower()

            # Provide helpful fallback for common errors
            if "no results" in error_str or "empty" in error_str:
                fallback = self._empty_result_fallback(question)
            elif "unknown" in error_str and "label" in error_str:
                fallback = (
                    "The query referenced a data type not yet in the graph. "
                    "Available: Aircraft, Flight, Vessel, Earthquake, ThermalAnomaly, "
                    "ConflictEvent, Location, Operator, CorrelationAlert."
                )
            else:
                fallback = f"Query failed: {e}"

            return {
                "answer": fallback,
                "error": True,
                "session_id": session_id,
                "query": question,
                "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
            }

    def _empty_result_fallback(self, question: str) -> str:
        """When a query returns empty results, check graph stats and suggest alternatives."""
        try:
            graph = get_graph(
                self.settings.falkordb_host,
                self.settings.falkordb_port,
                self.settings.falkordb_graph,
            )
            result = graph.query(
                """
                OPTIONAL MATCH (a:Aircraft) WITH count(a) AS aircraft
                OPTIONAL MATCH (fl:Flight) WITH aircraft, count(fl) AS flights
                OPTIONAL MATCH (v:Vessel) WITH aircraft, flights, count(v) AS vessels
                OPTIONAL MATCH (e:Earthquake) WITH aircraft, flights, vessels, count(e) AS earthquakes
                OPTIONAL MATCH (t:ThermalAnomaly) WITH aircraft, flights, vessels, earthquakes, count(t) AS hotspots
                OPTIONAL MATCH (c:ConflictEvent) WITH aircraft, flights, vessels, earthquakes, hotspots, count(c) AS events
                RETURN aircraft, flights, vessels, earthquakes, hotspots, events
                """
            )
            row = result.result_set[0] if result.result_set else [0] * 6
            counts = {
                "military aircraft": row[0],
                "commercial flights": row[1],
                "vessels": row[2],
                "earthquakes": row[3],
                "thermal anomalies": row[4],
                "conflict events": row[5],
            }
            available = [f"{v} {k}" for k, v in counts.items() if v > 0]
            if available:
                return (
                    f"No results found for your query. The graph currently contains: "
                    f"{', '.join(available)}. Try rephrasing your question to query these data types."
                )
        except Exception:
            pass
        return "No results found. The data may not have been ingested yet — try again after a few minutes."

    def _record_provenance(self, query: str, answer: str, session_id: str):
        """Create a QueryAudit node for provenance tracking."""
        try:
            graph = get_graph(
                self.settings.falkordb_host,
                self.settings.falkordb_port,
                self.settings.falkordb_graph,
            )
            audit_id = f"qa_{uuid.uuid4().hex[:12]}"
            timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

            graph.query(
                """
                CREATE (q:QueryAudit {
                    id: $id,
                    query: $query,
                    answer: $answer,
                    sessionId: $sessionId,
                    timestamp: $timestamp,
                    model: $model
                })
                """,
                {
                    "id": audit_id,
                    "query": query,
                    "answer": answer[:2000],
                    "sessionId": session_id,
                    "timestamp": timestamp,
                    "model": self.settings.llm_model,
                },
            )
        except Exception as e:
            logger.warning("Failed to record query provenance: %s", e)

    def cleanup_sessions(self):
        """Remove expired sessions."""
        now = time.time()
        expired = [
            sid for sid, (_, ts) in _sessions.items() if now - ts > SESSION_TTL
        ]
        for sid in expired:
            del _sessions[sid]
        if expired:
            logger.debug("GraphRAG: cleaned up %d expired sessions", len(expired))
