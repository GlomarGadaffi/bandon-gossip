"""BigQuery Agent definition using Google ADK."""

import os

from google.adk.agents import LlmAgent
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig
from google.oauth2.credentials import Credentials

from bigquery_agent.sources import SOURCE_CATALOG, get_source


def create_bigquery_agent(
    access_token: str,
    project_id: str,
    default_dataset: str | None = None,
    source_key: str | None = None,
    model: str = "gemini-3-pro-preview",
) -> LlmAgent:
    """Create a BigQuery agent using an OAuth access token.

    Args:
        access_token: Google OAuth2 access token from the browser.
        project_id: Google Cloud project ID chosen by the user.
        default_dataset: Default BigQuery dataset. If None, agent will discover.
        source_key: Key from SOURCE_CATALOG selecting the sensor pipeline context.
            When provided, injects the matching domain prompt and suggested dataset.
            When None, the agent operates in generic mode across all sources.
        model: The Gemini model to use.

    Returns:
        Configured LlmAgent with BigQuery tools.
    """
    credentials = Credentials(token=access_token)

    credentials_config = BigQueryCredentialsConfig(
        credentials=credentials,
    )

    tool_config = BigQueryToolConfig(
        compute_project_id=project_id,
    )

    bigquery_toolset = BigQueryToolset(
        credentials_config=credentials_config,
        bigquery_tool_config=tool_config,
    )

    # Resolve the active dataset: explicit > source suggestion > none
    source_config = get_source(source_key) if source_key else None
    active_dataset = default_dataset or (source_config.suggested_dataset if source_config else None)

    dataset_clause = ""
    if active_dataset:
        dataset_clause = (
            f"\n- Default Dataset: {active_dataset}\n"
            f"When writing SQL queries, prefer the fully qualified table name: "
            f"`{project_id}.{active_dataset}.table_name`\n"
        )

    if source_config:
        domain_section = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DOMAIN CONTEXT — {source_config.display_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{source_config.domain_prompt}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        source_note = (
            f"You are specialized for the **{source_config.display_name}** log source. "
            "Use the domain context above to write precise SQL queries. "
            "Start with the table and schema already known — do not waste a tool call "
            "listing schemas unless the user asks about a table not covered above."
        )
    else:
        domain_section = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AVAILABLE LOG SOURCES IN THIS ECOSYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{chr(10).join(f"  {k:20s}  {v.display_name}" for k, v in SOURCE_CATALOG.items())}

The primary cross-channel table is `{project_id}.mirkwood.emission_events`.
All sensor pipelines normalize into that table via the Mirkwood normalizer.
For cross-source correlation queries start there. For deep per-source queries,
ask the user to select a specific log source from the list above.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        source_note = (
            "No specific log source is selected — you have access to all tables. "
            "For cross-channel questions, use mirkwood.emission_events. "
            "For per-source questions, use the native dataset for that pipeline."
        )

    instruction = f"""You are a helpful data analyst agent with access to Google BigQuery.
You analyze sensor and RF intelligence data from the GlomarGadaffi ecosystem of field
collection tools spanning Meshtastic mesh radio, P25 trunked radio, BLE scanning,
WiFi attack detection, LoRa RF discovery, SIP/VoIP, LTE cellular, and ADS-B.

CONFIGURATION:
- Project ID: {project_id}{dataset_clause}
{source_note}
{domain_section}
GENERAL QUERY GUIDELINES:
- Always use fully-qualified table names: `{project_id}.dataset.table`
- When writing BigQuery SQL, use Standard SQL (not legacy SQL)
- JSON fields (metadata, tags, secondary_ids) are STRING columns containing JSON.
  Extract scalar values with JSON_VALUE(col, '$.key').
  Extract arrays with JSON_VALUE_ARRAY(col) or UNNEST(JSON_VALUE_ARRAY(col)).
- Timestamps are UTC. Use TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL N HOUR/DAY)
  for relative time windows.
- PARTITIONED tables (e.g. meshnarc.packets on DATE(rx_timestamp)) perform best
  when you filter on the partition column — always include a time filter.
- If a query fails, read the error message, adjust the SQL, and retry.
- Present results in a clear, readable format. Summarize counts/trends in prose
  before showing raw table output for large result sets.
- Always explain what you queried and why before showing results."""

    agent = LlmAgent(
        model=model,
        name="BigQueryAgent",
        description="An AI agent that queries GlomarGadaffi sensor data in Google BigQuery.",
        instruction=instruction,
        tools=[bigquery_toolset],
    )

    return agent
