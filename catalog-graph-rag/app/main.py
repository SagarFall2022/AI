from fastapi import FastAPI
from dotenv import load_dotenv
from pydantic import BaseModel
from app.settings import Settings
from app.llm_gpt4o import GPT4oClient
from app.embeddings_cohere import CohereEmbedder
from app.graph_neo4j import Neo4jCatalogGraph
from app.rag import answer_with_graph_rag
from fastapi.middleware.cors import CORSMiddleware
from app.html_formatter import FORMATTER_SYSTEM, sanitize_html, basic_fallback_html

class AskRequest(BaseModel):
    question: str
    top_k: int = 10

class AskHtmlResponse(BaseModel):
    html: str
    answer_text: str



load_dotenv()
s = Settings()

app = FastAPI(title="Neo4j-only Graph RAG")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

@app.post("/ask")
def ask(req: dict):
    q = req["question"]
    top_k = int(req.get("top_k", s.TOP_K))
    ans = answer_with_graph_rag(llm, graph, embedder, q, top_k)
    return {"answer": ans}

@app.post("/ask_html", response_model=AskHtmlResponse)
def ask_html(req: AskRequest):
    q = req.question.strip()
    top_k = req.top_k

    # 1) get the normal deep answer text (already grounded)
    answer_text = answer_with_graph_rag(llm, graph, embedder, q, top_k)

    # 2) format into HTML using GPT-4o (no new facts allowed)
    try:
        user = f"Question:\n{q}\n\nRAG Answer:\n{answer_text}"
        html = llm.answer(FORMATTER_SYSTEM, user)
        html = sanitize_html(html)
    except Exception:
        html = basic_fallback_html(q, answer_text)

    return AskHtmlResponse(html=html, answer_text=answer_text)
