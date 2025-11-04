
# ServiceNow + Slack AI Copilot — Architecture

> High-level architecture and request lifecycles for **Smart Intake**, **AI Triage**, and **Realtime Sync**.  
> Tech: **Slack**, **n8n**, **OpenAI**, **Qdrant**, **ServiceNow**

---

## 1) System Architecture (High-Level)

```mermaid
flowchart LR
  subgraph Slack["Slack Workspace"]
    SC[Slash /incident]:::sl
    ST[Message / Triage]:::sl
  end

  subgraph n8n["n8n Orchestrator"]
    WI["Webhook: /incident-intake"]:::n8
    WT["Webhook: /slack/triage"]:::n8
    WSN["Webhook: /servicenow/incidents/update"]:::n8
    NORM["Normalize text + Slack meta"]:::n8
    EMB["OpenAI Embeddings (text-embedding-3-small)"]:::ai
    QSEARCH1["Qdrant Search (≥ 0.80)"]:::vec
    QSEARCH2["Qdrant Search (≥ 0.60)"]:::vec
    DUP["GPT-4o-mini: Duplicate Check"]:::ai
    DRAFT["GPT-4o-mini: Draft Incident Fields"]:::ai
    CREATE["ServiceNow: Create Incident"]:::sn
    UPQ["Qdrant Upsert (vectors + payload)"]:::vec
    TRIAGE["GPT-4o-mini: Summarize & Next Steps"]:::ai
  end

  subgraph OpenAI["OpenAI"]
    OAI1[Embeddings]:::ai
    OAI2[GPT-4o-mini]:::ai
  end

  subgraph Qdrant["Qdrant Vector DB (collection: incidents)"]
    QCOL[(Vectors + Payload)]:::vec
  end

  subgraph SN["ServiceNow"]
    SNINC[Incident Table]:::sn
  end

  SC --> WI
  WI --> NORM --> EMB --> QSEARCH1 --> DUP
  DUP -- "duplicate=true" --> SC
  DUP -- "duplicate=false" --> DRAFT --> CREATE --> UPQ --> SC

  ST --> WT --> NORM --> EMB --> QSEARCH2 --> TRIAGE --> ST

  WSN --> EMB --> UPQ
  WSN -- "operation=delete" --> QCOL

  EMB <--> OAI1
  DUP <--> OAI2
  DRAFT <--> OAI2
  TRIAGE <--> OAI2
  QSEARCH1 <--> QCOL
  QSEARCH2 <--> QCOL
  CREATE <--> SNINC

classDef sl fill:#36C5F0,stroke:#111,color:#fff
classDef n8 fill:#111827,stroke:#111,color:#fff
classDef ai fill:#7C3AED,stroke:#111,color:#fff
classDef vec fill:#F59E0B,stroke:#111,color:#111
classDef sn fill:#10B981,stroke:#111,color:#111
```
*Notes:*  
- **Smart Intake:** Qdrant similarity threshold **0.80** before incident creation.  
- **AI Triage:** Qdrant similarity threshold **0.60** for contextual answers.  
- **Realtime Sync:** SN event → re-embed & upsert, or delete from Qdrant.

---

## 2) Smart Intake — Sequence

```mermaid
sequenceDiagram
  participant U as Slack User
  participant S as Slack
  participant W as n8n /incident-intake
  participant E as OpenAI Embeddings
  participant Q as Qdrant (incidents)
  participant G as GPT-4o-mini (Duplicate/Draft)
  participant N as ServiceNow

  U->>S: /incident "issue details"
  S->>W: POST payload (response_url)
  W->>W: Normalize(text, channel, user)
  W->>E: Create embedding
  E-->>W: Vector
  W->>Q: Search similar (≥ 0.80)
  Q-->>W: Top hits
  W->>G: Duplicate Check (LLM)
  alt duplicate = true
    W-->>S: Ephemeral "Possible duplicate" (link to incident)
  else duplicate = false
    W->>G: Draft Incident JSON (LLM)
    G-->>W: short_description, description, priority...
    W->>N: Create incident
    N-->>W: sys_id, number
    W->>E: Embed canonical draft
    E-->>W: Vector
    W->>Q: Upsert (vector + payload)
    W-->>S: Ephemeral "Created" + link
  end
```

---

## 3) AI Triage — Sequence

```mermaid
sequenceDiagram
  participant U as Slack User
  participant S as Slack
  participant W as n8n /slack/triage
  participant E as OpenAI Embeddings
  participant Q as Qdrant (incidents)
  participant G as GPT-4o-mini (Summarize)

  U->>S: Message "triage question"
  S->>W: POST payload (response_url)
  W->>W: Normalize(query)
  W->>E: Create embedding
  E-->>W: Vector
  W->>Q: Search similar (≥ 0.60)
  Q-->>W: Top hits
  alt hits exist
    W->>G: Summarize & suggest next steps
    G-->>W: Actionable guidance + related incidents
    W-->>S: Ephemeral triage result (blocks)
  else no hits
    W-->>S: "No close match, please use /incident"
  end
```

---

## 4) Realtime Sync — Data View

**Event:** ServiceNow incident change or delete → `POST /servicenow/incidents/update`  
- **Delete:** remove the point from **Qdrant**.  
- **Change:** rebuild canonical text → re-embed → upsert vector + payload.

---

### Embed in README
```markdown
[View Architecture](docs/ARCHITECTURE.md)
```
