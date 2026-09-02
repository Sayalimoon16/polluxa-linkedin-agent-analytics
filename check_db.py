import sqlite3

conn = sqlite3.connect("data/polluxa_analytics.db")

print("TABLES:")
print(conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall())

print("\nRUNS:")
print(conn.execute(
    "SELECT run_id, rows_in, rows_out, status FROM ingestion_runs"
).fetchall())

print("\nSTAGING ROWS:")
print(conn.execute(
    "SELECT COUNT(*) FROM leads_staging"
).fetchone()[0])

print("\nDEAD-LETTER ROWS:")
print(conn.execute(
    "SELECT COUNT(*) FROM dead_letter"
).fetchone()[0])

print("\nWATERMARK:")
print(conn.execute(
    "SELECT * FROM pipeline_state"
).fetchall())

conn.close()