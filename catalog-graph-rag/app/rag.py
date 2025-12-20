from typing import List, Dict, Tuple
import json

RERANK_SYSTEM = """
You are a reranker for catalog chunks.
Given a question and candidate chunks, return JSON:
{
  "ranked_ids": ["chunk_id1","chunk_id2",...]
}
Rules:
- Rank by: direct relevance + ability to answer with evidence.
- Prefer chunks with explicit part/kit numbers, tables, applicability, replacements.
- Return up to 10 ids.
"""

ANSWER_SYSTEM = """
You are a Hendrickson catalog assistant.
Use ONLY the provided evidence (chunks) and graph expansions (edges).
Every key claim MUST include a citation like (doc_id p.page_no).
If not found, say "Not found in ingested catalogs" and suggest what to look for.

Produce a deep answer with this structure:

1) Answer (direct)
2) Graph reasoning path (what relationships you traversed)
3) Results (structured list or table)
4) Evidence (citations inline)
5) Confidence & gaps
"""


def _dedupe_by_page(chunks: List[Dict], max_per_page: int = 2) -> List[Dict]:
    seen = {}
    out = []
    for c in chunks:
        key = (c.get("doc_id"), c.get("page_no"))
        seen[key] = seen.get(key, 0) + 1
        if seen[key] <= max_per_page:
            out.append(c)
    return out


def _format_chunks(chunks: List[Dict], max_chars_each: int = 1200) -> str:
    blocks = []
    for c in chunks:
        blocks.append(
            f"[chunk={c['id']}] ({c['doc_id']} p.{c['page_no']})\n{(c['text'] or '')[:max_chars_each]}"
        )
    return "\n\n---\n\n".join(blocks)


def _extract_entity_lists(entity_rows: List[Dict]) -> Tuple[List[str], List[str], List[str]]:
    parts, kits, systems = set(), set(), set()
    for r in entity_rows:
        labels = r.get("labels") or []
        if "Part" in labels and r.get("number"):
            parts.add(str(r["number"]))
        if "Kit" in labels and r.get("number"):
            kits.add(str(r["number"]))
        if "System" in labels and r.get("name"):
            systems.add(str(r["name"]))
    return sorted(parts), sorted(kits), sorted(systems)


def rerank_chunks(llm, question: str, candidates: List[Dict]) -> List[Dict]:
    """
    LLM rerank: candidates -> top 8-10
    """
    payload = {
        "question": question,
        "candidates": [
            {
                "id": c["id"],
                "doc_id": c["doc_id"],
                "page_no": c["page_no"],
                "text": (c["text"] or "")[:900]
            }
            for c in candidates
        ]
    }
    ranked = llm.json(RERANK_SYSTEM, json.dumps(payload))
    ranked_ids = ranked.get("ranked_ids") or []
    id_to_chunk = {c["id"]: c for c in candidates}
    out = [id_to_chunk[i] for i in ranked_ids if i in id_to_chunk]
    return out


def answer_with_graph_rag(llm, graph, embedder, question: str, top_k: int = 10):
    # 1) Vector search (recall)
    q_emb = embedder.embed(question[:8000])
    raw = graph.vector_search_chunks(q_emb, top_k=max(20, top_k * 2))

    candidates = [{
        "id": r["id"],
        "doc_id": r["doc_id"],
        "page_no": r["page_no"],
        "text": r["text"],
        "score": r.get("score", 0.0)
    } for r in raw]

    # 2) Diversity: avoid too many from same page
    candidates = _dedupe_by_page(candidates, max_per_page=2)

    # 3) Rerank to improve precision
    top = rerank_chunks(llm, question, candidates)[:top_k]

    # 4) Entity extraction from the top chunks
    chunk_ids = [c["id"] for c in top]
    entity_rows = graph.entities_for_chunks(chunk_ids)
    parts, kits, systems = _extract_entity_lists(entity_rows)

    # 5) Graph expansion (multi-hop relationships)
    # NOTE: expand_entities now returns a list of dicts (not {"e": ...})
    edges = graph.expand_entities(parts, kits, systems, limit=250)
    edges_text = "\n".join([json.dumps(e) for e in edges])[:6000]

    # 6) Pull supporting chunks for expanded entities (grounding)
    support = graph.chunks_for_entities(parts, kits, systems, top_n=30)
    support_norm = [{
        "id": s["id"],
        "doc_id": s["doc_id"],
        "page_no": s["page_no"],
        "text": s["text"],
        "score": 0.0
    } for s in support]

    # Merge evidence: top chunks first, then support (dedupe by chunk id)
    merged = []
    seen_ids = set()
    for c in top + support_norm:
        if c["id"] not in seen_ids:
            merged.append(c)
            seen_ids.add(c["id"])

    # Keep bounded
    merged = merged[:25]
    evidence_text = _format_chunks(merged, max_chars_each=1200)

    # 7) Final deep answer
    user = f"""
Question:
{question}

Detected entities (from top chunks):
Parts: {parts[:30]}
Kits: {kits[:30]}
Systems: {systems[:30]}

Graph expansion edges (JSON lines):
{edges_text}

Evidence chunks:
{evidence_text}
"""
    return llm.answer(ANSWER_SYSTEM, user)
