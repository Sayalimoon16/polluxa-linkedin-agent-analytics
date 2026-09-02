import sqlite3

def test_idempotent_upsert(tmp_path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE leads_staging (source_id TEXT PRIMARY KEY, name TEXT)")
    conn.execute("INSERT INTO leads_staging VALUES (?, ?)", ("L001", "First"))
    conn.execute("""
        INSERT INTO leads_staging VALUES (?, ?)
        ON CONFLICT(source_id) DO UPDATE SET name=excluded.name
    """, ("L001", "Updated"))
    assert conn.execute("SELECT COUNT(*) FROM leads_staging").fetchone()[0] == 1
    assert conn.execute("SELECT name FROM leads_staging").fetchone()[0] == "Updated"
