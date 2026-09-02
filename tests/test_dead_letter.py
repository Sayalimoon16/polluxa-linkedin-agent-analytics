import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sqlite3
import app.ingest as ingest


def test_invalid_record_goes_to_dead_letter(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"

    monkeypatch.setattr(ingest, "DB_PATH", str(db_path))

    def fake_fetch(*args, **kwargs):
        return {
            "data": [
                {
                    "id": "bad-1",
                    "name": "",
                    "updated_at": "2026-08-22T11:00:00+00:00"
                }
            ]
        }

    monkeypatch.setattr(ingest, "fetch_with_retry", fake_fetch)

    result = ingest.run_ingestion()

    assert result["rows_in"] == 1
    assert result["rows_out"] == 0

    conn = sqlite3.connect(db_path)

    dead_letter_count = conn.execute(
        "SELECT COUNT(*) FROM dead_letter"
    ).fetchone()[0]

    assert dead_letter_count == 1

    conn.close()