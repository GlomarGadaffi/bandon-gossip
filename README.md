# bandon-gossip

talk to the logs. AI agent that queries BigQuery datasets via natural language. uses Google Agents Development Kit (ADK) with Gemini LLM to translate user queries into SQL, execute, and explain results.

## integration

```python
from agent import create_bigquery_agent

agent = create_bigquery_agent(
    access_token=user_oauth_token,
    project_id="my-gcp-project",
    default_dataset="logs",
    model="gemini-3-pro-preview"
)

response = agent.query("how many errors did we have yesterday by service?")
```

## features

- **natural language queries** — "show me p95 latency for service X in the last hour"
- **automatic SQL generation** — Gemini models understand BigQuery schema and syntax
- **multi-table joins** — agent can navigate complex data models
- **explanation** — LLM explains the SQL it generated and the results

## architecture

- **Google ADK** — Agent Development Kit with BigQuery toolset
- **Gemini LLM** — models understand data semantics, not just SQL syntax
- **BigQuery** — underlying data warehouse
- **OAuth** — user credentials for secure access control

## use cases

**incident response**: "what endpoints hit 404 in the last 10 minutes?"
**performance analysis**: "which queries took >1s yesterday?"
**compliance**: "export all events matching regulatory retention policy"
**exploratory**: "what's the distribution of response codes by region?"

## notes

requires GCP project, BigQuery dataset, and user OAuth token. LLM call costs scale with query complexity and data volume. default model is `gemini-3-pro-preview` (`agent.py`).
