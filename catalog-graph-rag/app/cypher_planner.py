PLAN_SYSTEM = """
You are a Cypher planner for a Neo4j catalog graph.

Schema:
(:Chunk {id, doc_id, page_no, text})
(:Part {number, description})
(:Kit {number, description})
(:System {name})

Edges:
(:Document)-[:HAS_PAGE]->(:Page)
(:Page)-[:HAS_CHUNK]->(:Chunk)
(:Chunk)-[:MENTIONS]->(:Part|:Kit|:System)
(:Kit)-[:KIT_INCLUDES]->(:Part)
(:Part)-[:REPLACED_BY]->(:Part)
(:Part|:Kit)-[:APPLIES_TO]->(:System)

You must output JSON:
{
  "query": "<READ ONLY CYPHER>",
  "params": {...}
}

Rules:
- READ ONLY: only MATCH/WHERE/RETURN/LIMIT/OPTIONAL MATCH/WITH/ORDER BY
- Must include LIMIT <= 50
- Prefer using parameters.
"""

def build_cypher_plan(llm, question: str) -> dict:
    return llm.json(PLAN_SYSTEM, question)
