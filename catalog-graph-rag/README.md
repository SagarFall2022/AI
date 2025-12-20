# Catalog Graph RAG — Neo4j + GPT-4o + Cohere POC

A compact Retrieval-Augmented Generation (RAG) demo that builds a Neo4j catalog graph from PDF catalogs, indexes text chunks as vectors (Cohere), and answers catalog questions with grounded evidence and an optional HTML formatter.

---

## Quick links

- App entry / API: [catalog-graph-rag/app/main.py](catalog-graph-rag/app/main.py) — see [`ask`](catalog-graph-rag/app/main.py) and [`ask_html`](catalog-graph-rag/app/main.py) endpoints  
- RAG core logic: [`answer_with_graph_rag`](catalog-graph-rag/app/rag.py) in [catalog-graph-rag/app/rag.py](catalog-graph-rag/app/rag.py)  
- Graph storage & queries: [`Neo4jCatalogGraph`](catalog-graph-rag/app/graph_neo4j.py) in [catalog-graph-rag/app/graph_neo4j.py](catalog-graph-rag/app/graph_neo4j.py)  
- Embedder: [`CohereEmbedder`](catalog-graph-rag/app/embeddings_cohere.py) in [catalog-graph-rag/app/embeddings_cohere.py](catalog-graph-rag/app/embeddings_cohere.py)  
- LLM client: [`GPT4oClient`](catalog-graph-rag/app/llm_gpt4o.py) in [catalog-graph-rag/app/llm_gpt4o.py](catalog-graph-rag/app/llm_gpt4o.py)  
- HTML formatter / sanitizer: [`sanitize_html`](catalog-graph-rag/app/html_formatter.py) in [catalog-graph-rag/app/html_formatter.py](catalog-graph-rag/app/html_formatter.py)  
- Graph extraction LLM wrapper: [`extract_graph`](catalog-graph-rag/app/graph_extract_llm.py) in [catalog-graph-rag/app/graph_extract_llm.py](catalog-graph-rag/app/graph_extract_llm.py)  
- Ingestion helper script: [catalog-graph-rag/scripts/new_ingest_pdfs.py](catalog-graph-rag/scripts/new_ingest_pdfs.py) (see helpers like [`stable_id`](catalog-graph-rag/scripts/new_ingest_pdfs.py) and [`chunk_already_processed`](catalog-graph-rag/scripts/new_ingest_pdfs.py))  
- Config template: [catalog-graph-rag/.env.example](catalog-graph-rag/.env.example) — mapped to [`Settings`](catalog-graph-rag/app/settings.py)  
- Frontend UI samples: [catalog-graph-rag/index-new.html](catalog-graph-rag/index-new.html) and [catalog-graph-rag/index.html](catalog-graph-rag/index.html)  
- Requirements: [catalog-graph-rag/requirements.txt](catalog-graph-rag/requirements.txt)

---

## Features

- Extracts text + tables from PDFs ([`extract_pages`](catalog-graph-rag/app/extract_pdf.py)).  
- Chunks text and creates stable chunk ids; safe resume if graph edges exist ([`stable_id`](catalog-graph-rag/scripts/new_ingest_pdfs.py)).  
- Embeds content via Cohere and stores vectors on Neo4j nodes ([`CohereEmbedder`](catalog-graph-rag/app/embeddings_cohere.py), [`upsert_doc_page_chunk`](catalog-graph-rag/app/graph_neo4j.py)).  
- LLM-based graph extraction (parts/kits/systems/replacements) via [`extract_graph`](catalog-graph-rag/app/graph_extract_llm.py).  
- Grounded question answering that combines vector recall, LLM rerank, graph expansion, and a final LLM answer ([`answer_with_graph_rag`](catalog-graph-rag/app/rag.py)).  
- Optionally returns formatted HTML using the HTML formatter (`sanitize_html`, [catalog-graph-rag/app/html_formatter.py]).

---

## Quickstart

1. Create venv & install:
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   pip install -r catalog-graph-rag/requirements.txt
   ```

2. Copy & populate environment:
   ```bash
   cp catalog-graph-rag/.env.example catalog-graph-rag/.env
   # Edit catalog-graph-rag/.env to add Azure/Cohere/Neo4j creds
   ```
   Settings map to [`Settings`](catalog-graph-rag/app/settings.py).

3. Ingest PDFs into Neo4j (ensure Neo4j is running):
   ```bash
   python catalog-graph-rag/scripts/new_ingest_pdfs.py
   ```
   The script uses [`stable_id`](catalog-graph-rag/scripts/new_ingest_pdfs.py), performs embedding, upsert via [`Neo4jCatalogGraph.upsert_doc_page_chunk`](catalog-graph-rag/app/graph_neo4j.py), and ingests extracted graph edges.

4. Start API:
   ```bash
   uvicorn app.main:app --app-dir catalog-graph-rag --reload --port 8000
   ```
   - Ask JSON API: POST /ask → uses [`answer_with_graph_rag`](catalog-graph-rag/app/rag.py)  
   - Ask HTML API: POST /ask_html → returns formatted HTML via [`sanitize_html`](catalog-graph-rag/app/html_formatter.py) and [`GPT4oClient`](catalog-graph-rag/app/llm_gpt4o.py)

5. Frontend:
   - Open [catalog-graph-rag/index-new.html](catalog-graph-rag/index-new.html) or serve via any static server.

---

## Development notes & safety

- Cypher planner and guard exist to keep runtime queries read-only:
  - Planner: [catalog-graph-rag/app/cypher_planner.py](catalog-graph-rag/app/cypher_planner.py)  
  - Guard: [catalog-graph-rag/app/cypher_guard.py](catalog-graph-rag/app/cypher_guard.py) — enforces MATCH/RETURN/LIMIT-only rules.

- The ingestion script is resilient:
  - Skips chunks already processed (`chunk_already_processed`) and skips failed LLM parses while continuing ingestion.

- HTML returned by the formatter is sanitized with a minimal allowlist in [`sanitize_html`](catalog-graph-rag/app/html_formatter.py). For production, replace with a hardened sanitizer (e.g., bleach).

---

## Troubleshooting

- No PDFs found? Ensure files are in [catalog-graph-rag/data/pdfs/].  
- Embedding errors: verify Cohere credentials in [catalog-graph-rag/.env.example] → [`CohereEmbedder`](catalog-graph-rag/app/embeddings_cohere.py).  
- Neo4j auth/URI: update [catalog-graph-rag/.env.example] → [`Settings`](catalog-graph-rag/app/settings.py).  
- LLM JSON parsing: extraction uses [`extract_graph`](catalog-graph-rag/app/graph_extract_llm.py); ingestion continues on JSON decode errors (warnings printed).

---

## Useful symbols & files (one more time)

- Files:
  - [catalog-graph-rag/app/main.py](catalog-graph-rag/app/main.py)  
  - [catalog-graph-rag/app/rag.py](catalog-graph-rag/app/rag.py)  
  - [catalog-graph-rag/app/graph_neo4j.py](catalog-graph-rag/app/graph_neo4j.py)  
  - [catalog-graph-rag/app/embeddings_cohere.py](catalog-graph-rag/app/embeddings_cohere.py)  
  - [catalog-graph-rag/app/llm_gpt4o.py](catalog-graph-rag/app/llm_gpt4o.py)  
  - [catalog-graph-rag/app/html_formatter.py](catalog-graph-rag/app/html_formatter.py)  
  - [catalog-graph-rag/app/graph_extract_llm.py](catalog-graph-rag/app/graph_extract_llm.py)  
  - [catalog-graph-rag/scripts/new_ingest_pdfs.py](catalog-graph-rag/scripts/new_ingest_pdfs.py)  
  - [catalog-graph-rag/.env.example](catalog-graph-rag/.env.example)

- Symbols:
  - [`answer_with_graph_rag`](catalog-graph-rag/app/rag.py)  
  - [`Neo4jCatalogGraph`](catalog-graph-rag/app/graph_neo4j.py)  
  - [`CohereEmbedder`](catalog-graph-rag/app/embeddings_cohere.py)  
  - [`GPT4oClient`](catalog-graph-rag/app/llm_gpt4o.py)  
  - [`sanitize_html`](catalog-graph-rag/app/html_formatter.py)  
  - [`extract_graph`](catalog-graph-rag/app/graph_extract_llm.py)  
  - [`stable_id`](catalog-graph-rag/scripts/new_ingest_pdfs.py)  
  - [`chunk_already_processed`](catalog-graph-rag/scripts/new_ingest_pdfs.py)  
  - [`Settings`](catalog-graph-rag/app/settings.py)

---