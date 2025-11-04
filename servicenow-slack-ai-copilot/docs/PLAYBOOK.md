# Playbook – How the Copilot Works

## 1️. Smart Intake
1. Slack user runs `/incident`.
2. n8n normalizes payload.
3. OpenAI Embeddings → Qdrant search ≥ 0.80.
4. GPT-4o-mini → duplicate decision.  
   - Duplicate → Slack message with links.  
   - New → draft fields + create incident in ServiceNow.
5. Index new incident in Qdrant.

## 2️. AI Triage
1. Slack user asks question.
2. n8n creates embedding → Qdrant search ≥ 0.60.
3. GPT-4o-mini summarizes context + next steps.
4. Slack ephemeral message returned.

## 3️. Realtime Sync
1. ServiceNow fires outbound REST on update/delete.
2. n8n receives payload → delete or re-embed + upsert Qdrant.

---

### Core Models
- `text-embedding-3-small`
- `gpt-4o-mini`

### Thresholds
- Intake similarity ≥ 0.80  
- Triage similarity ≥ 0.60
