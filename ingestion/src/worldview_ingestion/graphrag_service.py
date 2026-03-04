"""GraphRAG natural language query service.

Wraps graphrag_sdk to provide:
- Ontology extraction from the live FalkorDB graph
- Chat session management with TTL cleanup
- Query execution with provenance recording
"""

import logging
import os
import time
import uuid
from datetime import datetime, timezone

from .config import Settings
from .db import get_graph

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
                "The graph contains ONLY these node types:\n"
                "- Aircraft (military flights: hex, callsign, operator, isMilitary, isLADD, lastLat/Lon/Alt/Heading/Speed/Seen)\n"
                "- Vessel (AIS ship tracking: mmsi, name, shipType, country, lastLat/Lon/Sog/Cog/Seen)\n"
                "- ThermalAnomaly (NASA FIRMS hotspots: frp, brightness, confidence, daynight, acq_date/time)\n"
                "- ConflictEvent (GDELT events: name, eventType, goldstein, tone, domain, sourceCountry)\n"
                "- Location (291 seeded: airports, military bases, chokepoints, ports)\n"
                "- Operator (military operators: name, type)\n"
                "- CorrelationAlert (cross-layer correlations: ruleType, confidence, summary)\n"
                "- QueryAudit (analyst query history)\n\n"
                "Relationships: OBSERVED_AT (Aircraft/Vessel->Location with temporal edges), "
                "OPERATED_BY (Aircraft->Operator), DETECTED_NEAR (ThermalAnomaly->Location), "
                "REPORTED_NEAR (ConflictEvent->Location), PROXIMATE_TO (Aircraft->ThermalAnomaly), "
                "CORRELATED_WITH (ThermalAnomaly->ConflictEvent).\n\n"
                "IMPORTANT: Satellites, earthquakes, CCTV cameras, and traffic data are NOT in the graph. "
                "If asked about these, explain they are rendered in the frontend only, not stored in the knowledge graph.\n"
                "Generate exactly ONE Cypher query. Never generate multiple queries.\n\n"
                "Graph ontology:\n{ontology}"
            )

            qa_instruction = (
                "You are an OSINT intelligence analyst assistant for the WorldView platform. "
                "Answer questions based on the FalkorDB knowledge graph data. "
                "The graph tracks: military aircraft (Airplanes.live), naval vessels (AISStream AIS), "
                "NASA FIRMS thermal anomalies, GDELT conflict events, and cross-layer correlations.\n"
                "Satellites, earthquakes, CCTV, and traffic are displayed on the globe but NOT stored "
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
    _NON_GRAPH_KEYWORDS = {
        "satellite": "Satellites are tracked via TLE/SGP4 propagation in the browser only, not stored in the knowledge graph.",
        "orbit": "Satellite orbital data is propagated client-side via SGP4, not stored in the knowledge graph.",
        "earthquake": "Earthquake data is fetched directly from USGS in the browser, not stored in the knowledge graph.",
        "seismic": "Seismic data is fetched directly from USGS in the browser, not stored in the knowledge graph.",
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

    def query(self, question: str, session_id: str | None = None) -> dict:
        """Execute a natural language query against the knowledge graph."""
        if not self._initialized or not self._kg:
            return {
                "answer": "GraphRAG is not initialized. Check LLM_API_KEY configuration.",
                "error": True,
                "session_id": session_id or "",
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
            return {
                "answer": f"Query failed: {e}",
                "error": True,
                "session_id": session_id,
                "query": question,
                "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
            }

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
