from neo4j import GraphDatabase
from typing import List, Dict, Any


class Neo4jCatalogGraph:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def run(self, query: str, params: dict | None = None) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            return session.run(query, params or {}).data()

    # ------------------------------------------------------------------
    # Document → Page → Chunk (vector storage)
    # ------------------------------------------------------------------
    def upsert_doc_page_chunk(
        self,
        doc_id: str,
        page_no: int,
        chunk_id: str,
        chunk_text: str,
        embedding: List[float],
    ):
        """
        Create Document, Page, Chunk and attach embedding.
        Embedding is only set on first creation to avoid re-writing vectors.
        """
        self.run(
            """
            MERGE (d:Document {id:$doc})
            MERGE (p:Page {id:$pid})
            ON CREATE SET p.doc_id=$doc, p.page_no=$page
            MERGE (c:Chunk {id:$cid})
            ON CREATE SET
                c.doc_id=$doc,
                c.page_no=$page,
                c.text=$text,
                c.embedding=$emb
            MERGE (d)-[:HAS_PAGE]->(p)
            MERGE (p)-[:HAS_CHUNK]->(c)
            """,
            {
                "doc": doc_id,
                "pid": f"{doc_id}:{page_no}",
                "page": page_no,
                "cid": chunk_id,
                "text": chunk_text,
                "emb": embedding,
            },
        )

    # ------------------------------------------------------------------
    # Graph ingestion from LLM-extracted entities
    # ------------------------------------------------------------------
    def ingest_extracted_graph(self, chunk_id: str, extracted: dict):
        """
        extracted schema:
        {
          parts: [{number, description}],
          kits: [{number, description, includes: []}],
          systems: [{name}],
          replacements: [{from, to}],
          applies: [{item, system}]
        }
        """

        # ---------------- Parts ----------------
        for p in extracted.get("parts", []):
            num = (p.get("number") or "").strip()
            if not num:
                continue

            desc = (p.get("description") or "").strip()

            self.run(
                """
                MERGE (pt:Part {number:$n})
                ON CREATE SET pt.description=$d
                WITH pt
                MATCH (c:Chunk {id:$cid})
                MERGE (c)-[:MENTIONS]->(pt)
                """,
                {"n": num, "d": desc, "cid": chunk_id},
            )

        # ---------------- Kits + includes ----------------
        for k in extracted.get("kits", []):
            kn = (k.get("number") or "").strip()
            if not kn:
                continue

            kd = (k.get("description") or "").strip()

            # Create kit and link to chunk
            self.run(
                """
                MERGE (kt:Kit {number:$n})
                ON CREATE SET kt.description=$d
                WITH kt
                MATCH (c:Chunk {id:$cid})
                MERGE (c)-[:MENTIONS]->(kt)
                """,
                {"n": kn, "d": kd, "cid": chunk_id},
            )

            # Kit includes parts (MATCH first, then MERGE)
            for inc in k.get("includes", []) or []:
                pn = str(inc).strip()
                if not pn:
                    continue

                self.run(
                    """
                    MATCH (kt:Kit {number:$k})
                    MERGE (pt:Part {number:$p})
                    MERGE (kt)-[:KIT_INCLUDES]->(pt)
                    """,
                    {"k": kn, "p": pn},
                )

        # ---------------- Systems ----------------
        for s in extracted.get("systems", []):
            name = (s.get("name") or "").strip()
            if not name:
                continue

            self.run(
                """
                MERGE (sy:System {name:$n})
                WITH sy
                MATCH (c:Chunk {id:$cid})
                MERGE (c)-[:MENTIONS]->(sy)
                """,
                {"n": name, "cid": chunk_id},
            )

        # ---------------- Replacements ----------------
        for r in extracted.get("replacements", []):
            a = (r.get("from") or "").strip()
            b = (r.get("to") or "").strip()
            if not a or not b:
                continue

            self.run(
                """
                MERGE (pa:Part {number:$a})
                MERGE (pb:Part {number:$b})
                MERGE (pa)-[:REPLACED_BY]->(pb)
                """,
                {"a": a, "b": b},
            )

        # ---------------- Applies to system ----------------
        for a in extracted.get("applies", []):
            item = (a.get("item") or "").strip()
            sysn = (a.get("system") or "").strip()
            if not item or not sysn:
                continue

            # Attach Part or Kit to System safely
            self.run(
                """
                MERGE (sy:System {name:$sys})
                WITH sy
                OPTIONAL MATCH (p:Part {number:$item})
                OPTIONAL MATCH (k:Kit {number:$item})
                FOREACH (_ IN CASE WHEN p IS NULL THEN [] ELSE [1] END |
                  MERGE (p)-[:APPLIES_TO]->(sy)
                )
                FOREACH (_ IN CASE WHEN k IS NULL THEN [] ELSE [1] END |
                  MERGE (k)-[:APPLIES_TO]->(sy)
                )
                """,
                {"sys": sysn, "item": item},
            )

    # ------------------------------------------------------------------
    # Vector search (Neo4j native vector index)
    # ------------------------------------------------------------------
    def vector_search_chunks(self, embedding: List[float], top_k: int = 8):
        return self.run(
            """
            CALL db.index.vector.queryNodes(
              'chunk_embedding_idx',
              $k,
              $emb
            )
            YIELD node, score
            RETURN
              node.id AS id,
              node.doc_id AS doc_id,
              node.page_no AS page_no,
              node.text AS text,
              score
            ORDER BY score DESC
            """,
            {"k": top_k, "emb": embedding},
        )
    

    def entities_for_chunks(self, chunk_ids: list[str]) -> list[dict]:
        """
        Returns mentioned entities for a set of chunk ids.
        """
        return self.run(
            """
            MATCH (c:Chunk)-[:MENTIONS]->(e)
            WHERE c.id IN $cids
            RETURN c.id AS chunk_id,
                   labels(e) AS labels,
                   e.number AS number,
                   e.name AS name
            """,
            {"cids": chunk_ids},
        )

    def expand_entities(
        self,
        part_numbers: list[str],
        kit_numbers: list[str],
        system_names: list[str],
        limit: int = 250
    ) -> list[dict]:
        """
        Expand graph neighborhood around entities without complex Cypher aggregation.

        Returns list of dicts like:
          {"type": "...", ...}
        """
        edges: list[dict] = []

        # --- Kits -> Parts
        if kit_numbers:
            rows = self.run(
                """
                MATCH (k:Kit)-[:KIT_INCLUDES]->(p:Part)
                WHERE k.number IN $kits
                RETURN k.number AS kit, p.number AS part
                LIMIT $lim
                """,
                {"kits": kit_numbers, "lim": limit},
            )
            edges.extend([{"type": "kit_includes", "kit": r["kit"], "part": r["part"]} for r in rows])

        # --- Part replacements (multi-hop up to 5)
        if part_numbers:
            rows = self.run(
                """
                MATCH (p1:Part)-[:REPLACED_BY*1..5]->(p2:Part)
                WHERE p1.number IN $parts
                RETURN p1.number AS from, p2.number AS to
                LIMIT $lim
                """,
                {"parts": part_numbers, "lim": limit},
            )
            edges.extend([{"type": "replaced_by", "from": r["from"], "to": r["to"]} for r in rows])

        # --- Applies to (for parts and kits)
        if part_numbers or kit_numbers or system_names:
            rows = self.run(
                """
                MATCH (x)-[:APPLIES_TO]->(s:System)
                WHERE (
                    (x:Part AND x.number IN $parts) OR
                    (x:Kit  AND x.number IN $kits)  OR
                    (s.name IN $systems)
                )
                RETURN
                  CASE WHEN x:Part THEN 'Part' WHEN x:Kit THEN 'Kit' ELSE labels(x)[0] END AS itemLabel,
                  CASE WHEN x:Part THEN x.number ELSE x.number END AS item,
                  s.name AS system
                LIMIT $lim
                """,
                {"parts": part_numbers, "kits": kit_numbers, "systems": system_names, "lim": limit},
            )
            edges.extend([{"type": "applies_to", "itemLabel": r["itemLabel"], "item": r["item"], "system": r["system"]} for r in rows])

        # de-dup while preserving order
        seen = set()
        out = []
        for e in edges:
            key = tuple(sorted(e.items()))
            if key not in seen:
                seen.add(key)
                out.append(e)

        return out[:limit]


    def chunks_for_entities(self, part_numbers: list[str], kit_numbers: list[str], system_names: list[str], top_n: int = 30) -> list[dict]:
        """
        Fetch supporting chunks that mention the expanded entities.
        """
        return self.run(
            """
            MATCH (c:Chunk)-[:MENTIONS]->(e)
            WHERE ( (e:Part AND e.number IN $parts)
                 OR (e:Kit AND e.number IN $kits)
                 OR (e:System AND e.name IN $systems) )
            RETURN c.id AS id, c.doc_id AS doc_id, c.page_no AS page_no, c.text AS text
            ORDER BY c.doc_id, c.page_no
            LIMIT $n
            """,
            {"parts": part_numbers, "kits": kit_numbers, "systems": system_names, "n": top_n},
        )

