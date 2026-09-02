CREATE TABLE IF NOT EXISTS dq_results_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checked_at TEXT NOT NULL,
    completeness REAL NOT NULL,
    uniqueness REAL NOT NULL,
    validity REAL NOT NULL,
    timeliness REAL NOT NULL,
    referential_integrity REAL NOT NULL,
    composite_score REAL NOT NULL,
    status TEXT NOT NULL
);