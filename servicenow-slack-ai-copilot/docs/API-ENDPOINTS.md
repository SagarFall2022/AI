# API Endpoints

| Endpoint | Source | Method | Purpose |
|-----------|---------|--------|----------|
| `/incident-intake` | Slack `/incident` | POST | Create incident or mark duplicate |
| `/slack/triage` | Slack Message Action | POST | Retrieve similar incidents + summary |
| `/servicenow/incidents/update` | ServiceNow Outbound REST | POST | Sync updates to Qdrant |

---

## `/incident-intake`
**Request Sample**
```json
{
  "text": "VPN down for remote users",
  "channel": "C123",
  "user": "U123",
  "response_url": "https://hooks.slack.com/actions/..."
}
```

**Response**

Duplicate: "Possible duplicate found"

Created: "Incident INC001234 created"

---

## `/slack/triage`
**Request Sample**
```json
{
  "text": "Any update on VPN outage?",
  "channel": "C123",
  "user": "U123",
  "response_url": "https://hooks.slack.com/actions/..."
}
```
**Response**

Slack ephemeral blocks with summary + related incidents.

---