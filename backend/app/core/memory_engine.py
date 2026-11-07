"""AiChat Pro v74 — Enhanced Memory Engine (MemOS-inspired)
4-Layer Memory: Context → SQLite (typed) → Graph → Vector
Memory types: episodic, semantic, procedural, preference, fact, event
Importance scoring, entity extraction, memory decay, graph relationships."""

from __future__ import annotations
import json, re, uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from core.storage import get_conn, now_iso
from core.logging_setup import get_logger

log = get_logger(__name__)

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    _VECTOR_OK = True
except Exception:
    _VECTOR_OK = False

try:
    import networkx as nx
    _GRAPH_OK = True
except ImportError:
    _GRAPH_OK = False

# Memory types (MemOS-inspired)
MEMORY_TYPES = ["episodic","semantic","procedural","preference","fact","event","general"]

# Entity patterns for extraction
_ENTITY_PATTERNS = {
    "person": r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b',
    "place": r'(?:in|at|to|from)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)',
    "item": r'(?:the|a|an)\s+(\w+\s+(?:sword|shield|ring|amulet|potion|scroll|key|book|weapon|armor|gem|stone|crystal|staff|wand|blade|bow|dagger))',
}

class MemoryEngine:
    def __init__(self, max_context: int = 20):
        self.context_window: List[Dict[str, str]] = []
        self.max_context = max_context
        self._graph = nx.DiGraph() if _GRAPH_OK else None
        self._chroma_collection = None
        self._embedder = None
        if _VECTOR_OK:
            try:
                client = chromadb.Client()
                self._chroma_collection = client.get_or_create_collection("memory")
                self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                log.debug("suppressed error", exc_info=True)
                pass
        # Load graph from DB
        if self._graph is not None:
            self._load_graph()

    # ── Layer 1: Context window ─────────────────────────────
    def add_to_context(self, role: str, content: str):
        self.context_window.append({"role": role, "content": content})
        if len(self.context_window) > self.max_context:
            self._auto_summarise()

    def get_context(self) -> List[Dict[str, str]]:
        return list(self.context_window)

    def clear_context(self):
        self.context_window.clear()

    def _auto_summarise(self):
        overflow = self.context_window[:self.max_context // 2]
        combined = " ".join(m["content"] for m in overflow)
        summary = combined[:500]
        self.store_fact(f"[summary] {summary}", source="auto", memory_type="episodic", importance=0.4)
        self.context_window = self.context_window[self.max_context // 2:]

    # ── Layer 2: SQLite facts (typed, scored) ───────────────
    def store_fact(self, fact: str, source: str = "user", memory_type: str = "general",
                   importance: float = 0.5, confidence: float = 1.0,
                   character_name: str = "", tags: List[str] = None):
        """Store a typed memory with importance scoring."""
        # Auto-classify if not specified
        if memory_type == "general":
            memory_type = self._classify_memory(fact)
        # Auto-importance
        if importance == 0.5:
            importance = self._score_importance(fact, source)
        # Extract entities
        entities = self.extract_entities(fact)
        conn = get_conn()
        conn.execute(
            "INSERT INTO memory_facts (fact, source, memory_type, importance, confidence, "
            "entities_json, tags, character_name, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (fact, source, memory_type, importance, confidence,
             json.dumps(entities), json.dumps(tags or []), character_name, now_iso()))
        conn.commit(); conn.close()
        # Graph: add entity relationships
        if entities and self._graph is not None:
            self._add_entities_to_graph(entities, fact)
        # Vector store
        if self._chroma_collection and self._embedder:
            try:
                emb = self._embedder.encode(fact).tolist()
                self._chroma_collection.add(documents=[fact], embeddings=[emb],
                    ids=[f"f_{uuid.uuid4().hex[:12]}"])
            except Exception:
                log.debug("suppressed error", exc_info=True)
                pass

    def get_all_facts(self) -> List[Dict]:
        conn = get_conn()
        rows = conn.execute("SELECT * FROM memory_facts ORDER BY id DESC LIMIT 200").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_facts_by_type(self, memory_type: str) -> List[Dict]:
        conn = get_conn()
        rows = conn.execute("SELECT * FROM memory_facts WHERE memory_type=? ORDER BY importance DESC",
                            (memory_type,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_important_facts(self, min_importance: float = 0.7) -> List[Dict]:
        conn = get_conn()
        rows = conn.execute("SELECT * FROM memory_facts WHERE importance>=? ORDER BY importance DESC",
                            (min_importance,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_fact(self, fact_id: int):
        conn = get_conn()
        conn.execute("DELETE FROM memory_facts WHERE id=?", (fact_id,))
        conn.commit(); conn.close()

    def update_importance(self, fact_id: int, importance: float):
        conn = get_conn()
        conn.execute("UPDATE memory_facts SET importance=?, access_count=access_count+1, last_accessed=? WHERE id=?",
                     (min(1.0, max(0.0, importance)), now_iso(), fact_id))
        conn.commit(); conn.close()

    # ── Layer 3: Memory Graph ───────────────────────────────
    def _load_graph(self):
        """Load graph from DB."""
        if self._graph is None: return
        conn = get_conn()
        try:
            rows = conn.execute("SELECT * FROM memory_graph").fetchall()
            for r in rows:
                self._graph.add_edge(r["source_entity"], r["target_entity"],
                                     relation=r["relation_type"], weight=r["weight"])
        except Exception:
            log.debug("suppressed error", exc_info=True)
            pass
        conn.close()

    def _add_entities_to_graph(self, entities: List[Dict], context: str):
        """Add extracted entities as graph nodes with relationships."""
        if self._graph is None: return
        conn = get_conn()
        for i, e1 in enumerate(entities):
            self._graph.add_node(e1["name"], type=e1.get("type","unknown"))
            for e2 in entities[i+1:]:
                self._graph.add_edge(e1["name"], e2["name"], relation="co_occurs", weight=1.0)
                try:
                    conn.execute("INSERT INTO memory_graph (source_entity, target_entity, relation_type, weight, created_at) VALUES (?,?,?,?,?)",
                        (e1["name"], e2["name"], "co_occurs", 1.0, now_iso()))
                except Exception:
                    log.debug("suppressed error", exc_info=True)
                    pass
        conn.commit(); conn.close()

    def get_related_entities(self, entity_name: str, depth: int = 2) -> List[str]:
        """Get entities related to the given entity within N hops."""
        if self._graph is None: return []
        try:
            neighbors = set()
            current = {entity_name}
            for _ in range(depth):
                next_level = set()
                for n in current:
                    if n in self._graph:
                        next_level.update(self._graph.neighbors(n))
                neighbors.update(next_level)
                current = next_level
            neighbors.discard(entity_name)
            return list(neighbors)[:20]
        except Exception:
            log.debug("suppressed error", exc_info=True)
            return []

    def get_graph_stats(self) -> Dict:
        if self._graph is None: return {"available": False}
        return {"available": True, "nodes": self._graph.number_of_nodes(),
                "edges": self._graph.number_of_edges()}

    # ── Layer 4: Vector search ──────────────────────────────
    def vector_search(self, query: str, n: int = 5) -> List[str]:
        if not self._chroma_collection or not self._embedder:
            return self._fallback_search(query)
        try:
            emb = self._embedder.encode(query).tolist()
            results = self._chroma_collection.query(query_embeddings=[emb], n_results=n)
            return results.get("documents", [[]])[0]
        except Exception:
            log.debug("suppressed error", exc_info=True)
            return self._fallback_search(query)

    def _fallback_search(self, query: str) -> List[str]:
        facts = self.get_all_facts()
        q = query.lower()
        scored = []
        for f in facts:
            text = f.get("fact", "").lower()
            score = sum(1 for word in q.split() if word in text)
            imp = f.get("importance", 0.5) if isinstance(f.get("importance"), (int, float)) else 0.5
            score += imp * 2
            if score > 0: scored.append((f["fact"], score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scored[:5]]

    # ── Entity Extraction ───────────────────────────────────
    def extract_entities(self, text: str) -> List[Dict]:
        """Extract entities from text using pattern matching."""
        entities = []
        seen = set()
        # Named entities (capitalized words)
        for match in re.finditer(r'\b[A-Z][a-z]{2,}(?:\s[A-Z][a-z]+)*\b', text):
            name = match.group()
            if name not in seen and name not in {"The","This","That","They","When","Where","What","How"}:
                seen.add(name)
                entities.append({"name": name, "type": "person"})
        # Items
        for match in re.finditer(r'(?:the|a|an)\s+(\w+\s*(?:sword|shield|ring|amulet|potion|scroll|key|book|weapon|armor|gem|crystal|staff|wand|blade|bow|dagger|axe|hammer))', text.lower()):
            name = match.group(1).strip().title()
            if name not in seen:
                seen.add(name); entities.append({"name": name, "type": "item"})
        # Places (after location prepositions)
        for match in re.finditer(r'(?:in|at|to|from|near)\s+(?:the\s+)?([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)', text):
            name = match.group(1)
            if name not in seen:
                seen.add(name); entities.append({"name": name, "type": "place"})
        return entities[:10]

    # ── Memory Classification ───────────────────────────────
    def _classify_memory(self, text: str) -> str:
        t = text.lower()
        if any(w in t for w in ["happened","went","saw","met","found","fought","killed","traveled"]):
            return "episodic"
        if any(w in t for w in ["is a","are","means","defined","known as","fact:"]):
            return "semantic"
        if any(w in t for w in ["always","usually","habit","routine","prefer","tends to"]):
            return "procedural"
        if any(w in t for w in ["like","love","hate","enjoy","dislike","favorite","prefer"]):
            return "preference"
        if any(w in t for w in ["quest","mission","task","objective","reward"]):
            return "event"
        return "general"

    def _score_importance(self, text: str, source: str) -> float:
        score = 0.5
        if source == "moment": score = 0.9
        if source == "quest": score = 0.8
        if source == "auto": score = 0.3
        # Boost for emotional content
        if any(w in text.lower() for w in ["love","death","kill","betray","marry","born","die","secret"]):
            score = min(1.0, score + 0.2)
        # Boost for named entities
        if re.search(r'\b[A-Z][a-z]{2,}\b', text): score = min(1.0, score + 0.1)
        return round(score, 2)

    # ── Memory Decay ────────────────────────────────────────
    def apply_decay(self, decay_rate: float = 0.01):
        """Reduce importance of old, unaccessed memories."""
        conn = get_conn()
        rows = conn.execute("SELECT id, importance, last_accessed, created_at FROM memory_facts").fetchall()
        now = datetime.now()
        for r in rows:
            last = r["last_accessed"] or r["created_at"]
            try:
                dt = datetime.fromisoformat(last)
                days = (now - dt).days
                if days > 7:
                    new_imp = max(0.1, (r["importance"] or 0.5) - decay_rate * days)
                    if new_imp != r["importance"]:
                        conn.execute("UPDATE memory_facts SET importance=? WHERE id=?", (new_imp, r["id"]))
            except Exception:
                log.debug("suppressed error", exc_info=True)
                pass
        conn.commit(); conn.close()

    # ── Build context for chat ──────────────────────────────
    def build_memory_context(self, query: str = "", character_name: str = "", max_items: int = 8) -> str:
        """Build rich memory context for chat prompt injection."""
        parts = []
        # Important memories first
        important = self.get_important_facts(0.7)[:3]
        if important:
            parts.append("Important: " + "; ".join(f.get("fact","")[:80] for f in important))
        # Character-specific memories
        if character_name:
            conn = get_conn()
            char_mems = conn.execute("SELECT fact FROM memory_facts WHERE character_name=? ORDER BY importance DESC LIMIT 3",
                                     (character_name,)).fetchall()
            conn.close()
            if char_mems:
                parts.append(f"About {character_name}: " + "; ".join(r["fact"][:60] for r in char_mems))
        # Search-relevant memories
        if query:
            relevant = self._fallback_search(query)[:3]
            if relevant:
                parts.append("Relevant: " + "; ".join(r[:60] for r in relevant))
        # Entity graph context
        entities = self.extract_entities(query) if query else []
        for e in entities[:2]:
            related = self.get_related_entities(e["name"], 1)
            if related:
                parts.append(f"{e['name']} connected to: {', '.join(related[:5])}")
        return " | ".join(parts)[:600] if parts else ""

    # ── Pruning ─────────────────────────────────────────────
    def prune(self, keep: int = 200):
        conn = get_conn()
        conn.execute("DELETE FROM memory_facts WHERE id NOT IN "
                     "(SELECT id FROM memory_facts ORDER BY importance DESC, id DESC LIMIT ?)", (keep,))
        conn.commit(); conn.close()
