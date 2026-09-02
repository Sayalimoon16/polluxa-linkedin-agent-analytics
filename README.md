Polluxa LinkedIn Agent Analytics Platform

End-to-end Data Analyst Assessment project covering ingestion, data
engineering, data quality, risk intelligence, Power BI analytics,
DevOps, CI/CD, observability, and pipeline resilience.

📌 Project Overview

This project implements an end-to-end analytics platform for a LinkedIn
agent workflow.

The solution covers the complete pipeline:

LinkedIn Agent / Source
        ↓
Incremental Ingestion
        ↓
Staging + Dead-Letter Handling
        ↓
Star Schema Database
        ↓
Data Quality Checks
        ↓
Risk & Anomaly Analysis
        ↓
Power BI Analytics
        ↓
Docker + CI/CD + Structured Logging
        ↓
Failure Recovery & End-to-End Validation

The implementation is organized according to the assessment Parts 1--8.

📚 Assessment Coverage

Part                    Area                    Implementation

Part 1                  LinkedIn Agent          Seven-step evidence
Configuration &         pack and declared
Evidence                account-age tier

Part 2                  Data Ingestion &        Incremental ingestion,
Reliability             idempotency, retries,
backoff, rate-limit
handling, dead-letter
records, run metadata

Part 3                  Data Modeling &         Star schema,
Engineering             dimensions, facts,
surrogate keys, data
flow, data dictionary

Part 4                  Data Quality & Pipeline Automated DQ checks, DQ
Reliability             scoring/history,
refresh pipeline,
failure notification

Part 5                  Risk Intelligence &     Statistical anomaly
Capacity                scoring, risk
classification,
capacity/ceiling
analysis

Part 6                  Analytics & Power BI    KPI measures, agent
health, outreach, risk,
and reporting
dashboards

Part 7                  DevOps, CI/CD &         Docker, pinned
Observability           dependencies, CI/CD,
structured logs,
correlation IDs,
alerting

🏗️ Architecture

                    ┌──────────────────────┐
                    │   Source / Agent API  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Incremental Ingestion │
                    │ Retries / Backoff      │
                    │ Idempotency            │
                    └──────────┬───────────┘
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
                 ▼                           ▼
        ┌─────────────────┐        ┌─────────────────┐
        │ Staging Tables  │        │ Dead-Letter     │
        │ Valid Records   │        │ Invalid Records │
        └────────┬────────┘        └─────────────────┘
                 │
                 ▼
        ┌─────────────────────┐
        │     Star Schema     │
        │ Dimensions + Facts  │
        └──────────┬──────────┘
                   │
          ┌────────┴─────────┐
          ▼                  ▼
 ┌─────────────────┐  ┌──────────────────┐
 │ Data Quality    │  │ Risk / Anomaly   │
 │ Checks & Score  │  │ Model            │
 └────────┬────────┘  └────────┬─────────┘
          │                    │
          └──────────┬─────────┘
                     ▼
             ┌─────────────────┐
             │ Power BI Export │
             │ & Dashboard     │
             └─────────────────┘

📁 Repository Structure

polluxa_part2/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── app/
│   ├── __init__.py
│   ├── ingest.py
│   ├── main.py
│   └── source_api.py
│
├── data/
│   └── polluxa_analytics.db
│
├── docs/
│   ├── data_dictionary.md
│   └── data_flow.md
│
├── evidence/
│   ├── part1_evidance/
│   ├── part2_evidance/
│   ├── part3_evidance/
│   ├── part4_evidance/
│   ├── part5_evidence/
│   ├── part6/
│   ├── part7/
│   └── part8/
│
├── powerbi_data/
│   ├── ingestion_runs.csv
│   ├── leads_staging.csv
│   ├── dead_letter.csv
│   ├── pipeline_state.csv
│   ├── dim_agent.csv
│   ├── dim_company.csv
│   ├── dim_date.csv
│   ├── fact_outreach.csv
│   ├── dq_results_history.csv
│   └── risk_model_results.csv
│
├── sql/
│   ├── schema.sql
│   └── dq_history.sql
│
├── tests/
│   ├── test_dead_letter.py
│   ├── test_ingest.py
│   └── test_retry.py
│
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── check_db.py
├── dq_checks.py
├── export_powerbi.py
├── load_star_schema.py
├── part5_risk_model.py
├── refresh_pipeline.py
├── requirements.txt
├── run_refresh.bat
└── run_schema.py

The SQLite database is generated/used by the local pipeline. Database
schema and build scripts are maintained under sql/.

⚙️ Technology Stack

Technology          Purpose

Python 3.11         Application and pipeline implementation
SQLite              Analytical database
SQL                 Schema, transformations, and DQ history
Power BI            Dashboard and analytics
Docker              Containerization
GitHub Actions      CI/CD automation
Pytest              Automated testing
FastAPI / Uvicorn   Source API service
python-dotenv       Externalized configuration
Requests            HTTP/API communication

🔄 Part 2 --- Data Ingestion & Reliability

The ingestion layer is designed around reliable and repeatable pipeline
execution.

Key capabilities

Incremental loading

Idempotent writes

Retry handling

Exponential backoff

Rate-limit handling

Dead-letter handling for malformed records

Pipeline run metadata

Duplicate prevention

Controlled failure recovery

Main implementation

app/ingest.py
app/source_api.py
app/main.py

The ingestion process validates incoming records before writing them
into the analytical pipeline.

Invalid records are isolated into the dead-letter flow instead of
contaminating the valid dataset.

🗄️ Part 3 --- Data Modeling & Engineering

The database follows a dimensional/star-schema approach.

Core dimensions

dim_agent

dim_company

dim_date

Core fact

fact_outreach

Operational / supporting tables

leads_staging

dead_letter

ingestion_runs

pipeline_state

dq_results_history

risk_model_results

Database scripts

sql/schema.sql
sql/dq_history.sql

Documentation

docs/data_flow.md
docs/data_dictionary.md

The model separates analytical dimensions from measurable outreach
activity and preserves operational pipeline metadata.

✅ Part 4 --- Data Quality & Pipeline Reliability

The pipeline performs automated data-quality validation before
downstream analytics are considered complete.

DQ dimensions

Completeness

Uniqueness

Validity

Timeliness

Referential integrity

A composite DQ score is calculated and stored in the DQ history.

DQ outputs

powerbi_data/dq_results_history.csv

The pipeline also records refresh execution status and supports failure
notification/alert behavior.

Pipeline execution

python refresh_pipeline.py

Expected successful flow:

Incremental ingestion: SUCCESS
Star schema load: SUCCESS
Data quality checks: SUCCESS
Run duration: <measured runtime>

🧠 Part 5 --- Risk Intelligence & Capacity

The risk model analyzes account-level behavior and produces an
anomaly/risk score.

Outputs

Account-level anomaly score

Risk classification

Confidence indication

Capacity/limit analysis

Recommended operating limits

Model result history

Implementation:

part5_risk_model.py

Output table:

risk_model_results

The model documents assumptions, confidence, and limitations rather than
presenting statistical outputs as certainty.

📊 Part 6 --- Power BI Analytics

The Power BI report contains five dashboard pages:

Overview

Agents

Outreach

Account Health

Reports

Core KPIs

The dashboard includes explicit DAX measures for:

Invites Sent

Reply Rate

Acceptance Rate

Total Outreach

Total Replies

Conversion Rate

Throughput

Dashboard evidence

evidence/part6/
├── PowerBI_01_Overview.png
├── PowerBI_02_Agents.png
├── PowerBI_03_Outreach.png
├── PowerBI_04_Account_Health.png
└── PowerBI_05_Reports.png

Power BI data is exported from the analytical database into:

powerbi_data/

Campaign ROI limitation

The current source/schema does not provide the campaign cost, revenue,
ROI, or target-segment fields required to calculate a defensible
campaign ROI metric.

Therefore, no ROI value is fabricated. The implementation preserves the
available evidence and documents this data limitation instead.

🐳 Part 7 --- DevOps, CI/CD & Observability

Containerization

The application is containerized using Docker.

Dockerfile
requirements.txt
.env.example

Dependencies are pinned in requirements.txt.

Configuration is externalized rather than hard-coded into the
application.

CI/CD

GitHub Actions workflow:

.github/workflows/ci.yml

The pipeline:

Git Push / Pull Request
        ↓
Checkout
        ↓
Python 3.11
        ↓
Install pinned dependencies
        ↓
Run pytest
        ↓
Tests pass?
     ↙       ↘
   NO         YES
   ↓           ↓
 FAIL      Docker Build
              ↓
       Publish Image

Deployment/image publishing is gated by the automated test result.

Automated tests

Current test suite:

tests/test_dead_letter.py
tests/test_ingest.py
tests/test_retry.py

Final test result:

3 passed

Structured logging

Pipeline logs are machine-parseable JSON and include:

Timestamp

Log level

Message

Correlation ID

A correlation ID is carried across a pipeline run so related events can
be traced together.

Example location:

logs/ingestion.log
logs/refresh_pipeline.log

Alerting

Alerting is implemented for:

Pipeline failure

Data-quality threshold breach

Anomalous run duration

The refresh pipeline includes alert handling for these conditions.

🧪 Part 8 --- Final Validation & Resilience Demo

The final validation demonstrates that the pipeline behaves correctly
under failure and bad-data conditions.

Scenario 1 --- Mid-run Failure Recovery

Test

A controlled API failure was introduced during ingestion.

Expected behavior:

Pipeline fails without corrupting the dataset.

Existing records are not duplicated.

Recovery can be executed safely.

Idempotency prevents duplicate records.

Evidence

evidence/part8/01_Scenario1_Failure_Recovery_No_Duplicates.png

The validation confirmed that the record count and distinct source IDs
remained consistent after the controlled failure and recovery.

Scenario 2 --- Malformed / Bad-Quality Input

Test

A malformed input record was introduced into the source flow.

Expected behavior:

The malformed record is rejected.

Valid records continue through the pipeline.

The invalid record is captured in the dead-letter flow.

The reason for rejection is recorded.

Evidence

evidence/part8/02_Scenario2_Bad_Data_Caught.png

The malformed record was captured as a dead-letter record with the
validation error instead of being loaded as a valid staging record.

Scenario 3 --- End-to-End Refresh

Test

The complete pipeline was executed from source ingestion through the
analytical outputs and Power BI refresh.

Flow:

Source
  ↓
Incremental Ingestion
  ↓
Star Schema Load
  ↓
Data Quality
  ↓
Risk Model
  ↓
Power BI CSV Export
  ↓
Power BI Refresh

Evidence

evidence/part8/03_Scenario3_End_to_End_Refresh_PowerBI.png

The final dashboard screenshot demonstrates the refreshed analytics
after the pipeline completed successfully.

🧾 Part 1 --- LinkedIn Agent Configuration & Evidence

The Part 1 evidence pack contains the seven assessment-relevant
screenshots demonstrating the LinkedIn agent configuration and analytics
workflow.

Evidence                    Description

01_dashboard.png          Polluxa dashboard / analytics overview
02_account_age.png        LinkedIn account-age configuration
03_identity_company.png   Agent identity and company configuration
04_targeting.png          Agent targeting configuration
05_build_search.png       Search/build configuration
06_leads.png              Leads/results evidence
07_analytics.png          Outreach pipeline / analytics evidence

Declared Account Age Tier

1+ Year

📸 Evidence Map

Assessment Part         Evidence Location            Purpose

Part 1                  evidence/part1_evidance/   Seven-step
configuration evidence

Part 2                  evidence/part2_evidance/   Ingestion, database,
and test evidence

Part 3                  evidence/part3_evidance/   Star-schema and
database verification

Part 4                  evidence/part4_evidance/   DQ and scheduled
refresh evidence

Part 5                  evidence/part5_evidence/   Risk-model execution
evidence

Part 6                  evidence/part6/            Power BI dashboard
pages

Part 7                  evidence/part7/            Docker, CI/CD, logging,
and alerting

▶️ Setup & Run

1. Clone the repository

git clone https://github.com/Sayalimoon16/polluxa-linkedin-agent-analytics.git
cd polluxa-linkedin-agent-analytics

2. Create a virtual environment

Windows

python -m venv .venv
.venv\Scripts\Activate.ps1

3. Install dependencies

pip install -r requirements.txt

4. Configure environment variables

Copy:

.env.example

to:

.env

Keep credentials and other sensitive configuration outside source
control.

5. Build / initialize the schema

python run_schema.py

6. Run ingestion

python -m app.ingest

7. Run the full refresh pipeline

python refresh_pipeline.py

8. Run the risk model

python part5_risk_model.py

9. Export Power BI data

python export_powerbi.py

10. Run automated tests

pytest -v

🐳 Docker

Build

docker build -t polluxa-linkedin-agent-analytics .

Run

docker run --rm polluxa-linkedin-agent-analytics

The Docker image uses pinned Python dependencies and externalized
configuration.

🔐 Configuration & Security

Sensitive credentials/configuration should be provided through
environment variables.

The repository uses:

.env

for local secrets and excludes it from version control.

The committed template is:

.env.example

No private credentials should be committed to the repository.

🧪 Validation Commands

Run the following commands to validate the implementation:

pytest -v

python refresh_pipeline.py

python part5_risk_model.py

python export_powerbi.py

For database verification:

python check_db.py

📋 Final Submission Checklist

Requirement                             Status

Source repository                       ✅
README and setup instructions           ✅
Database schema / build scripts         ✅
Power BI report                         ✅
Power BI page screenshots               ✅
Architecture documentation              ✅
Data flow documentation                 ✅
Data dictionary                         ✅
Part 1 seven-step evidence              ✅
Part 2 ingestion/reliability evidence   ✅
Part 3 schema evidence                  ✅
Part 4 DQ/refresh evidence              ✅
Part 5 risk-model evidence              ✅
Part 6 dashboard evidence               ✅
Part 7 Docker evidence                  ✅
Part 7 CI/CD evidence                   ✅
Part 7 structured logging evidence      ✅
Part 7 alerting evidence                ✅
Part 8 failure-recovery evidence        ✅
Part 8 bad-data evidence                ✅
Part 8 end-to-end refresh evidence      ✅

📦 Key Deliverables

README.md
Dockerfile
requirements.txt

.github/workflows/ci.yml

app/
sql/
tests/
docs/
evidence/
powerbi_data/

assemenet.pbix
dq_checks.py
refresh_pipeline.py
part5_risk_model.py
export_powerbi.py
load_star_schema.py
run_schema.py
check_db.py

🎯 Project Outcome

The completed implementation demonstrates an end-to-end analytics
pipeline with:

Reliable incremental ingestion

Idempotent database writes

Retry and failure handling

Dead-letter processing

Dimensional/star-schema modeling

Automated data-quality validation

Risk and anomaly analysis

Explicit Power BI DAX measures

Docker containerization

Automated CI/CD testing

Structured logs with correlation IDs

Pipeline, DQ, and duration alerting

Failure recovery without duplicate records

Bad-data detection

End-to-end Power BI refresh validation

The repository and evidence pack are organized to map the implementation
back to the assessment Parts
