"""
AiChat Pro — Knowledge Base
Index PDF/DOCX/TXT files, store in SQLite, optional embedding search via
sentence-transformers, fallback keyword search.
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import List, Dict
from core.storage import get_conn, now_iso
from shared_config import KNOWLEDGE_DIR

try:
    from sentence_transformers import SentenceTransformer
    import json as _json
    _EMBED_OK = True
except Exception:
    _EMBED_OK = False

_embedder = None

def _get_embedder():
    global _embedder
    if _EMBED_OK and _embedder is None:
        try:
            _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            pass
    return _embedder


def index_file(filepath: str) -> bool:
    path = Path(filepath)
    if not path.exists():
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    if not text.strip():
        return False

    emb_json = None
    embedder = _get_embedder()
    if embedder:
        try:
            emb = embedder.encode(text[:2000]).tolist()
            emb_json = _json.dumps(emb)
        except Exception:
            pass

    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO knowledge_documents "
            "(path, title, content, embedding_json, indexed_at) VALUES (?,?,?,?,?)",
            (str(path), path.name, text, emb_json, now_iso()))
        conn.commit()
    except Exception:
        pass
    conn.close()
    return True


def index_folder(folder: str = None):
    folder = folder or str(KNOWLEDGE_DIR)
    count = 0
    for root, _, files in os.walk(folder):
        for fname in files:
            if fname.lower().endswith((".txt", ".md", ".csv", ".json")):
                if index_file(os.path.join(root, fname)):
                    count += 1
    return count


def search_knowledge(query: str, n: int = 5) -> List[Dict]:
    embedder = _get_embedder()
    if embedder:
        return _vector_search(query, n, embedder)
    return _keyword_search(query, n)


def _keyword_search(query: str, n: int) -> List[Dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, title, content FROM knowledge_documents "
        "WHERE content LIKE ? LIMIT ?",
        (f"%{query}%", n)).fetchall()
    conn.close()
    results = []
    for r in rows:
        snippet = _extract_snippet(r["content"], query)
        results.append({"title": r["title"], "snippet": snippet})
    return results


def _vector_search(query: str, n: int, embedder) -> List[Dict]:
    import json as _json
    try:
        q_emb = embedder.encode(query).tolist()
    except Exception:
        return _keyword_search(query, n)
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, title, content, embedding_json FROM knowledge_documents "
        "WHERE embedding_json IS NOT NULL").fetchall()
    conn.close()
    scored = []
    for r in rows:
        try:
            doc_emb = _json.loads(r["embedding_json"])
            sim = _cosine(q_emb, doc_emb)
            scored.append((sim, r))
        except Exception:
            continue
    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for sim, r in scored[:n]:
        snippet = _extract_snippet(r["content"], query)
        results.append({"title": r["title"], "snippet": snippet, "score": round(sim, 3)})
    return results


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return dot / (na * nb + 1e-9)


def _extract_snippet(text: str, query: str, window: int = 200) -> str:
    idx = text.lower().find(query.lower())
    if idx == -1:
        return text[:window]
    start = max(0, idx - window // 2)
    end = min(len(text), idx + window // 2)
    return "..." + text[start:end] + "..."


def list_indexed() -> List[Dict]:
    conn = get_conn()
    rows = conn.execute("SELECT id, title, path, indexed_at FROM knowledge_documents ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_document(doc_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM knowledge_documents WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()
