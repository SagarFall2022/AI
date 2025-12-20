import os, glob, hashlib
from dotenv import load_dotenv
from app.settings import Settings
from app.llm_gpt4o import GPT4oClient
from app.embeddings_cohere import CohereEmbedder
from app.extract_pdf import extract_pages
from app.chunking import chunk_text
from app.graph_extract_llm import extract_graph
from app.graph_neo4j import Neo4jCatalogGraph

load_dotenv()
s = Settings()

# ----------------------------
# Optional resume controls
# ----------------------------
# ONLY_DOC="L405.pdf"  (exact filename in data/pdfs/)
ONLY_DOC = os.getenv("ONLY_DOC", "").strip()
# START_PAGE="10"  (skip pages < 10)
START_PAGE = int(os.getenv("START_PAGE", "0"))

llm = GPT4oClient(
    s.AZURE_OPENAI_ENDPOINT,
    s.AZURE_OPENAI_API_KEY,
    s.AZURE_OPENAI_API_VERSION,
    s.AZURE_OPENAI_GPT4O_DEPLOYMENT
)

embedder = CohereEmbedder(
    s.AZURE_COHERE_ENDPOINT,
    s.AZURE_COHERE_API_KEY,
    s.AZURE_COHERE_DEPLOYMENT,
    s.AZURE_COHERE_EMBED_DIM
)

graph = Neo4jCatalogGraph(s.NEO4J_URI, s.NEO4J_USER, s.NEO4J_PASSWORD)

def stable_id(doc_id: str, page_no: int, idx: int, text: str) -> str:
    h = hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()[:10]
    return f"chunk:{doc_id}:{page_no}:{idx}:{h}"

def chunk_already_processed(chunk_id: str) -> bool:
    """
    We treat a chunk as processed if it already has at least one (:Chunk)-[:MENTIONS]->(:Entity) edge.
    This lets you safely re-run ingestion after a crash without duplicating work.
    """
    rows = graph.run(
        """
        MATCH (c:Chunk {id:$cid})
        OPTIONAL MATCH (c)-[:MENTIONS]->(e)
        RETURN count(e) AS n
        """,
        {"cid": chunk_id},
    )
    return bool(rows and rows[0].get("n", 0) > 0)

def chunk_has_embedding(chunk_id: str) -> bool:
    """
    Skip embedding call if embedding already exists on chunk.
    """
    rows = graph.run(
        """
        MATCH (c:Chunk {id:$cid})
        RETURN c.embedding IS NOT NULL AS has
        """,
        {"cid": chunk_id},
    )
    return bool(rows and rows[0].get("has", False))

pdfs = glob.glob("data/pdfs/*.pdf")
if not pdfs:
    print("No PDFs found in data/pdfs/")
    raise SystemExit(1)

for pdf_path in pdfs:
    doc_id = os.path.basename(pdf_path)

    if ONLY_DOC and doc_id != ONLY_DOC:
        print(f"[SKIP DOC] {doc_id} (ONLY_DOC={ONLY_DOC})")
        continue

    print(f"\n[DOC] {doc_id}")
    pages = extract_pages(pdf_path)

    for p in pages:
        page_no = int(p["page_no"])
        if page_no < START_PAGE:
            continue

        merged = (p.get("text", "") + "\n\n" + p.get("tables", "")).strip()
        if not merged:
            continue

        chunks = chunk_text(merged, s.CHUNK_CHARS, s.CHUNK_OVERLAP)

        for idx, ch in enumerate(chunks):
            ch = (ch or "").strip()
            if not ch:
                continue

            cid = stable_id(doc_id, page_no, idx, ch)

            # ✅ If this chunk already has graph edges, skip LLM + ingestion (safe resume)
            if chunk_already_processed(cid):
                print(f"[SKIP] already processed (MENTIONS exists): {cid}")
                continue

            # ✅ Embed only if embedding is missing
            emb = None
            try:
                if not chunk_has_embedding(cid):
                    emb = embedder.embed(ch[:s.MAX_EMBED_CHARS])
            except Exception as e:
                print(f"[WARN] embedding failed for {cid}: {e}")
                continue

            # Upsert doc/page/chunk (embedding only set on CREATE in your graph_neo4j.py)
            try:
                graph.upsert_doc_page_chunk(
                    doc_id=doc_id,
                    page_no=page_no,
                    chunk_id=cid,
                    chunk_text=ch,
                    embedding=emb if emb is not None else [],  # safe placeholder; ON CREATE sets embedding
                )
            except Exception as e:
                print(f"[WARN] upsert_doc_page_chunk failed for {cid}: {e}")
                continue

            # Extract entities/relations per chunk (POC)
            try:
                extracted = extract_graph(llm, ch)
            except Exception as e:
                # This is where your JSONDecodeError happens.
                # We skip and continue, so ingestion doesn't die.
                print(f"[WARN] extract_graph failed for {cid}: {e}")
                continue

            # Ingest extracted graph
            try:
                graph.ingest_extracted_graph(cid, extracted)
            except Exception as e:
                print(f"[WARN] ingest_extracted_graph failed for {cid}: {e}")
                continue

            print(f"[OK] {cid}")

print("\n✅ Neo4j-only ingestion complete.")
print("Next: run scripts/neo4j_schema.cypher once if not done already.")
