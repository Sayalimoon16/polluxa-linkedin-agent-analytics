Polluxa LinkedIn Agent Analytics Platform
End-to-end Data Analytics platform for LinkedIn Agent performance, outreach analytics, data quality, risk intelligence, capacity monitoring, Power BI reporting, and DevOps observability.

Assessment Coverage
This repository follows the Polluxa Data Analyst Assessment Parts 1–8.

Part 1  LinkedIn Agent Configuration & Evidence
↓
Part 2  API Engineering & Reliable Ingestion
↓
Part 3  Star Schema & Data Architecture
↓
Part 4  Data Quality & Scheduled Automation
↓
Part 5  Risk & Anomaly Modeling
↓
Part 6  Power BI Analytics
↓
Part 7  Docker + CI/CD + Observability
↓
Part 8  Final Evidence, Repository & Demonstration
Repository Structure
polluxa_part2/
├── app/
│   ├── init.py
│   ├── main.py
│   ├── ingest.py
│   └── source_api.py
├── data/
├── sql/
├── tests/
├── docs/
│   ├── data_flow.md
│   └── data_dictionary.md
├── evidence/
├── logs/
├── .github/
│   └── workflows/
├── .env.example
├── requirements.txt
├── Dockerfile
└── README.md
Part 1 — LinkedIn Agent Configuration & Evidence
Selected evidence:

01_dashboard.png — Polluxa dashboard / analytics overview
02_account_age.png — LinkedIn account age selection
03_identity_company.png — Agent identity and company setup
04_targeting.png — Agent targeting configuration
05_build_search.png — LinkedIn Automation search/build configuration
06_leads.png — Leads/results evidence
07_analytics.png — Outreach pipeline / analytics evidence
The source archive contained 14 screenshots; seven were selected as the strongest assessment-relevant evidence. Account-age evidence is 02_account_age.png.

Part 2 — API Engineering & Data Pipeline
Implemented:

Environment-based configuration
Incremental loading using an updated_at watermark
Idempotent UPSERT using source_id
Exponential backoff
HTTP 429 / Retry-After handling
Dead-letter capture for malformed records
Persistent run metadata
Source API
The assessment does not provide a public Polluxa API endpoint/schema. Therefore, this project uses a local mock Source API with the contract required by the ingestion service. Replace the source URL/response mapping only when an authorized API is provided.

Verification
Automated tests:

Idempotent UPSERT     PASSED
HTTP 429 retry        PASSED
Dead-letter handling  PASSED

3 passed
Incremental verification:

First run:       5 rows in, 5 rows out
Subsequent run:  0 rows in, 0 rows out
Fresh Docker verification:

5 rows in, 5 rows out
Part 3 — Data Architecture & Star Schema
Analytical model:

dim_agent
dim_company
dim_date
fact_outreach
Fact grain: one fact_outreach row represents one source LinkedIn outreach/lead record identified by source_id.

dim_agent supports SCD Type 2 using:

effective_from
effective_to
is_current
Data flow:

Source API → Ingestion Service → leads_staging
→ Transformation → Star Schema → Analytics / BI
Documentation:

docs/data_flow.md
docs/data_dictionary.md
Verified table counts:

dim_agent       5
dim_company     5
dim_date        1
fact_outreach   5
Part 4 — Data Quality & Automation
Quality checks cover:

Completeness
Uniqueness
Validity
Timeliness
Referential integrity
A composite DQ score and threshold are used, with DQ results retained for history.

Scheduled refresh components:

refresh_pipeline.py
run_refresh.bat
Windows Task Scheduler configuration
Part 5 — Advanced Analytics & Risk Modeling
The risk model uses:

Beta-Binomial smoothing
Wilson 95% confidence intervals
Weighted anomaly scoring
Acceptance-collapse detection
Reply-decay detection
Ghosting/pending signals
Account-capacity recommendations
Results are stored in risk_model_results.

Output includes agent, account tier, anomaly score, risk level, acceptance/reply/ rejection/ghost rates, recommended daily invites/messages, confidence, notes, recommendation, and calculation timestamp.

Configured account-age ceilings:

Account Age	Daily Invites	Daily Messages
< 1 Month	5	10
1 Month	10	15
2–6 Months	15	25
6–12 Months	25	40
1+ Year	30	60
Because the current dataset is small, confidence is limited. The model does not fabricate missing outcomes.

Part 6 — Power BI Analytics
Power BI contains five pages:

Overview
Agents
Outreach
Account Health
Reports
Explicit DAX measures include:

Invites Sent
Acceptance Rate
Reply Rate
Total Outreach
Total Replies
Conversion Rate
Throughput
Account Health covers agent status, utilisation, ghost accounts, paused accounts, and agent-level health.

Risk Intelligence uses Part 5 results including:

Agent name
Risk level
Anomaly score
Confidence
Recommended daily invites
Recommended daily messages
Campaign ROI Limitation
The current supplied analytical schema does not contain campaign, target-segment, cost, revenue, or ROI fields. Therefore Campaign ROI values are not fabricated.

A genuine Campaign ROI analysis requires the source data to provide campaign and target-segment identifiers plus the required financial/performance fields.

Part 7 — DevOps, CI/CD & Observability
Docker
Container configuration:

Dockerfile
Base image:

python:3.11-slim
Build:

docker build -t polluxa-part2:1.0 .
Run:

docker run --rm   -e SOURCE_API_URL=http://host.docker.internal:8000
-e DATABASE_PATH=/tmp/test.db `
polluxa-part2:1.0
Verified result:

rows_in: 5
rows_out: 5
Pinned Dependencies
requirements.txt:

fastapi==0.116.1
uvicorn[standard]==0.35.0
requests==2.32.4
python-dotenv==1.1.1
pytest==8.4.1
Externalised Configuration
Runtime configuration is supplied through environment variables. .env.example is provided as a template.

Never commit .env, passwords, LinkedIn session cookies, API keys, or other secrets.

Structured Logging
Logs are machine-parseable JSON and contain:

timestamp
level
message
correlation_id
A unique correlation ID is carried across events for the same pipeline run.

Verified events include pipeline start, watermark retrieval, API success, records fetched, watermark update, successful completion, and database close.

Evidence:

Part_7_Structured_Logs_Correlation_ID.png
CI/CD
GitHub Actions workflow is implemented in:

.github/workflows/
Target flow:

Git Push
↓
Install dependencies
↓
Automated tests
↓
Test result gate
↓
Deployment stage
Deployment must not proceed when automated tests fail.

Alerting
Required observability alerts cover:

Pipeline failure
DQ threshold breach
Anomalous run duration
Alert configuration must be externalised and must not contain hard-coded secrets.

Part 8 — Final Deliverables & Demo
Final repository package includes:

Source repository
Database schema/build scripts
Power BI PBIX and screenshots
Architecture documentation
Data flow
Data dictionary
Part 1 evidence pack
Docker configuration
CI/CD configuration
Structured logs
Alerting configuration
Automated tests
Live demonstration scenarios:

Mid-run failure recovery without duplicate records
Malformed/bad-quality input caught by the pipeline
End-to-end refresh from source through database/risk/DQ to Power BI
Local Setup
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
Start the local Source API:

uvicorn app.source_api --reload --port 8000
Run ingestion:

.venv\Scripts\activate
python -m app.ingest
Run tests:

pytest -q
Docker Log Evidence
Persist container logs to the host:

docker run --rm   -v "C:\Users\HP\Downloads\polluxa_part2_starter\polluxa_part2\logs:/app/logs"
-e SOURCE_API_URL=http://host.docker.internal:8000   -e DATABASE_PATH=/tmp/test.db
polluxa-part2:1.0
Then:

Get-Content .\logs\ingestion.log -Tail 20
Evidence Map
Part 1 → selected agent screenshots
Part 2 → database/tests/dead-letter/429/incremental evidence
Part 3 → schema/data-flow/data-dictionary evidence
Part 4 → DQ/scheduled-refresh evidence
Part 5 → risk-model evidence
Part 6 → Power BI page screenshots
Part 7 → Docker/logging/CI-CD/alerting evidence
Part 8 → final repository + evidence + live demo
Current Status
Part	Area	Status
1	Agent configuration & evidence	Completed
2	API ingestion & reliability	Completed
3	Star schema & documentation	Completed
4	DQ & scheduled automation	Implemented
5	Risk & anomaly model	Completed
6	Power BI analytics	Implemented
6	Campaign ROI	Limitation documented
7	Docker	Completed
7	Pinned dependencies	Completed
7	Externalised configuration	Implemented
7	Structured JSON logging	Completed
7	Correlation IDs	Completed
7	CI/CD	Completed
7	Alerting	Completed
8	Final packaging	Pending finalisation
Security
Never commit passwords.
Never commit LinkedIn session cookies.
Never commit API keys or tokens.
Use environment variables for secrets.
Keep .env local.
Commit only .env.example with placeholders.
Data Integrity Principle
This project does not fabricate unavailable business data. Where the supplied source schema does not contain fields required for an assessment output, the limitation is explicitly documented.

About

End-to-end LinkedIn Agent Analytics Platform for data ingestion, star-schema modeling, data quality checks, risk intelligence, Power BI analytics, CI/CD, structured logging, and observability.

Resources
Readme
Activity
Stars
0 stars
Watchers
0 watching
Forks
0 forks
Releases
No releases published
Create a new release
Packages
1
(1)
polluxa-linkedin-agent-analytics
Contributors
1
(1)
@Sayalimoon16
Sayalimoon16
Languages
Python
99.2%
Other
0.8%
Footer