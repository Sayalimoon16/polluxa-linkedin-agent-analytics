import sqlite3
from datetime import datetime, timezone


DB_PATH = "data/polluxa_analytics.db"


def connect():
    return sqlite3.connect(DB_PATH)


def create_history_table(conn):
    conn.execute("""
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
        )
    """)
    conn.commit()


def check_completeness(conn):
    total = conn.execute(
        "SELECT COUNT(*) FROM fact_outreach"
    ).fetchone()[0]

    if total == 0:
        return 0

    valid = conn.execute("""
        SELECT COUNT(*)
        FROM fact_outreach
        WHERE source_id IS NOT NULL
          AND lead_name IS NOT NULL
          AND job_title IS NOT NULL
          AND outreach_status IS NOT NULL
    """).fetchone()[0]

    return valid / total * 100


def check_uniqueness(conn):
    total = conn.execute(
        "SELECT COUNT(*) FROM fact_outreach"
    ).fetchone()[0]

    unique_rows = conn.execute("""
        SELECT COUNT(DISTINCT source_id)
        FROM fact_outreach
    """).fetchone()[0]

    if total == 0:
        return 100

    return unique_rows / total * 100


def check_validity(conn):
    total = conn.execute(
        "SELECT COUNT(*) FROM fact_outreach"
    ).fetchone()[0]

    if total == 0:
        return 0

    valid = conn.execute("""
        SELECT COUNT(*)
        FROM fact_outreach
        WHERE source_id IS NOT NULL
          AND LENGTH(source_id) > 0
          AND lead_name IS NOT NULL
          AND LENGTH(lead_name) > 0
          AND outreach_status IN (
              'connected',
              'pending',
              'replied',
              'rejected'
          )
    """).fetchone()[0]

    return valid / total * 100


def check_timeliness(conn):
    total = conn.execute(
        "SELECT COUNT(*) FROM fact_outreach"
    ).fetchone()[0]

    if total == 0:
        return 0

    valid = conn.execute("""
        SELECT COUNT(*)
        FROM fact_outreach
        WHERE outreach_status IS NOT NULL
    """).fetchone()[0]

    return valid / total * 100


def check_referential_integrity(conn):
    total = conn.execute(
        "SELECT COUNT(*) FROM fact_outreach"
    ).fetchone()[0]

    if total == 0:
        return 0

    valid = conn.execute("""
        SELECT COUNT(*)
        FROM fact_outreach f
        JOIN dim_agent a
            ON f.agent_key = a.agent_key
        JOIN dim_company c
            ON f.company_key = c.company_key
    """).fetchone()[0]

    return valid / total * 100


def calculate_dq_score(results):
    weights = {
        "completeness": 0.25,
        "uniqueness": 0.20,
        "validity": 0.20,
        "timeliness": 0.15,
        "referential_integrity": 0.20,
    }

    score = sum(
        results[name] * weight
        for name, weight in weights.items()
    )

    return round(score, 2)


def save_dq_history(conn, results, score, status):
    checked_at = datetime.now(timezone.utc).isoformat()

    conn.execute("""
        INSERT INTO dq_results_history (
            checked_at,
            completeness,
            uniqueness,
            validity,
            timeliness,
            referential_integrity,
            composite_score,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        checked_at,
        results["completeness"],
        results["uniqueness"],
        results["validity"],
        results["timeliness"],
        results["referential_integrity"],
        score,
        status,
    ))

    conn.commit()


def run_dq_checks():
    conn = connect()

    try:
        # Create history table if it does not exist
        create_history_table(conn)

        results = {
            "completeness": check_completeness(conn),
            "uniqueness": check_uniqueness(conn),
            "validity": check_validity(conn),
            "timeliness": check_timeliness(conn),
            "referential_integrity": check_referential_integrity(conn),
        }

        score = calculate_dq_score(results)

        status = "PASS" if score >= 95 else "FAIL"

        # Save every DQ run
        save_dq_history(conn, results, score, status)

        print("\nDATA QUALITY RESULTS")
        print("--------------------")

        for name, value in results.items():
            print(f"{name}: {value:.2f}%")

        print(f"\nComposite DQ Score: {score:.2f}%")
        print(f"DQ Status: {status}")
        print("DQ history saved successfully.")

        return results, score, status

    finally:
        conn.close()


if __name__ == "__main__":
    run_dq_checks()