<div align="center">

# ServiceNow + Slack AI Copilot  
### End-to-End Incident Automation with OpenAI + Qdrant + n8n

</div>

This repository contains a single **n8n workflow export** implementing:

1. **Smart Intake** – Slack `/incident` → dedup → Draft an Incident using AI → create ServiceNow incident → index in Qdrant  
2. **AI Triage** – Slack query → retrieve similar incidents → summarize & suggest actions  
3. **Realtime Sync** – ServiceNow incident updates → delete or upsert in Qdrant

---

## Quick Start

```bash
git https://github.com/SagarFall2022/AI.git
cd servicenow-slack-ai-copilot
cp .env.example .env

Fill in .env with API keys and URLs.

Open n8n → Import from File → n8n/exports/smart-intake-triage-sync.json.

Connect credentials (OpenAI, Qdrant, ServiceNow).

Expose webhooks:

/incident-intake (Slack Intake)

/slack/triage (Slack Triage)

/servicenow/incidents/update (ServiceNow sync)
```