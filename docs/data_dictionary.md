# Polluxa LinkedIn Agent Analytics — Data Dictionary

## dim_agent

| Column | Data Type | Description |
|---|---|---|
| agent_key | INTEGER | Surrogate key uniquely identifying an agent dimension record. |
| agent_id | TEXT | Stable source-system identifier for the agent/account record. |
| agent_name | TEXT | Name associated with the agent/account. |
| agent_status | TEXT | Current status of the agent/account. |
| account_tier | TEXT | Account tier classification. |
| effective_from | TEXT | Timestamp from which the dimension record is effective. |
| effective_to | TEXT | Timestamp until which the dimension record is effective. NULL means the record is currently active. |
| is_current | INTEGER | Indicates whether the dimension record is the current version. 1 = current, 0 = historical. |

## dim_company

| Column | Data Type | Description |
|---|---|---|
| company_key | INTEGER | Surrogate key uniquely identifying a company dimension record. |
| company_name | TEXT | Name of the company associated with the outreach record. |

## dim_date

| Column | Data Type | Description |
|---|---|---|
| date_key | INTEGER | Surrogate/date key in YYYYMMDD format. |
| full_date | TEXT | Calendar date represented by the record. |
| year | INTEGER | Calendar year. |
| quarter | INTEGER | Calendar quarter from 1 to 4. |
| month | INTEGER | Calendar month from 1 to 12. |
| month_name | TEXT | Calendar month name. |
| day | INTEGER | Day of the month. |

## fact_outreach

| Column | Data Type | Description |
|---|---|---|
| outreach_key | INTEGER | Surrogate key uniquely identifying the fact record. |
| source_id | TEXT | Source-system identifier for the LinkedIn lead/outreach record. |
| agent_key | INTEGER | Foreign key referencing `dim_agent`. |
| company_key | INTEGER | Foreign key referencing `dim_company`. |
| lead_name | TEXT | Name of the LinkedIn lead/contact. |
| job_title | TEXT | Job title of the lead/contact. |
| outreach_status | TEXT | Status of the LinkedIn outreach/connection record. |
| updated_at | TEXT | Source-system timestamp indicating when the record was last updated. |
| loaded_at | TEXT | Timestamp when the record was loaded into the analytics database. |

## leads_staging

| Column | Data Type | Description |
|---|---|---|
| source_id | TEXT | Source-system identifier for the lead record. |
| name | TEXT | Name of the lead/contact. |
| job_title | TEXT | Job title of the lead/contact. |
| company | TEXT | Company associated with the lead. |
| status | TEXT | Current source-system status of the lead. |
| updated_at | TEXT | Source-system record update timestamp used for incremental ingestion. |
| loaded_at | TEXT | Timestamp when the staging record was loaded. |
| raw_json | TEXT | Original source record stored as JSON for traceability. |

## ingestion_runs

| Column | Data Type | Description |
|---|---|---|
| run_id | TEXT | Unique identifier for an ingestion execution. |
| started_at | TEXT | Timestamp when the ingestion run started. |
| ended_at | TEXT | Timestamp when the ingestion run ended. |
| rows_in | INTEGER | Number of records received from the source API. |
| rows_out | INTEGER | Number of records successfully written to staging. |
| status | TEXT | Execution status such as RUNNING, SUCCESS, or FAILED. |
| error_message | TEXT | Error details when an ingestion run fails. |

## dead_letter

| Column | Data Type | Description |
|---|---|---|
| id | INTEGER | Auto-generated identifier for the dead-letter record. |
| run_id | TEXT | Ingestion run that produced the rejected record. |
| payload | TEXT | Original malformed record stored as JSON. |
| error_message | TEXT | Validation or processing error associated with the rejected record. |
| created_at | TEXT | Timestamp when the dead-letter record was created. |

## pipeline_state

| Column | Data Type | Description |
|---|---|---|
| pipeline_name | TEXT | Name of the pipeline whose state is being stored. |
| watermark | TEXT | Latest successfully processed source `updated_at` timestamp used for incremental loading. |

## Star Schema Relationships

- `fact_outreach.agent_key` → `dim_agent.agent_key`
- `fact_outreach.company_key` → `dim_company.company_key`
- `updated_at` can be used to associate fact records with `dim_date`.
- `source_id` provides source-system traceability and idempotent record identification.

## Slowly Changing Dimension Strategy

`dim_agent` is designed to support **SCD Type 2**.

When tracked agent attributes change:

1. The previous record is retained.
2. `effective_to` is populated for the old version.
3. `is_current` is changed to `0`.
4. A new dimension record is inserted with a new `agent_key`.
5. The new record receives the new attribute values.
6. The new record has `is_current = 1` and a new `effective_from`.

This preserves historical versions while allowing current-state reporting.