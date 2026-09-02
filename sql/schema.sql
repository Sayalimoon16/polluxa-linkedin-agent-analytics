-- ============================================================
-- Polluxa LinkedIn Agent Analytics - Part 3
-- Star Schema
-- ============================================================

PRAGMA foreign_keys = ON;

-- ============================================================
-- DIMENSION: Agent
-- One row represents one LinkedIn outreach agent/account.
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_agent (
    agent_key INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL UNIQUE,
    agent_name TEXT NOT NULL,
    agent_status TEXT,
    account_tier TEXT,
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    is_current INTEGER NOT NULL DEFAULT 1
);

-- ============================================================
-- DIMENSION: Company
-- One row represents one target company.
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_company (
    company_key INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL UNIQUE
);

-- ============================================================
-- DIMENSION: Date
-- One row represents one calendar date.
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date TEXT NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    day INTEGER NOT NULL
);

-- ============================================================
-- FACT: Outreach
-- Grain:
-- One row represents one LinkedIn outreach/lead record.
-- ============================================================

CREATE TABLE IF NOT EXISTS fact_outreach (
    outreach_key INTEGER PRIMARY KEY AUTOINCREMENT,

    source_id TEXT NOT NULL UNIQUE,

    agent_key INTEGER,
    company_key INTEGER,

    lead_name TEXT NOT NULL,
    job_title TEXT,
    outreach_status TEXT,

    updated_at TEXT NOT NULL,
    loaded_at TEXT NOT NULL,

    FOREIGN KEY (agent_key)
        REFERENCES dim_agent(agent_key),

    FOREIGN KEY (company_key)
        REFERENCES dim_company(company_key)
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_fact_outreach_agent
    ON fact_outreach(agent_key);

CREATE INDEX IF NOT EXISTS idx_fact_outreach_company
    ON fact_outreach(company_key);

CREATE INDEX IF NOT EXISTS idx_fact_outreach_updated_at
    ON fact_outreach(updated_at);

CREATE INDEX IF NOT EXISTS idx_dim_agent_current
    ON dim_agent(agent_id, is_current);