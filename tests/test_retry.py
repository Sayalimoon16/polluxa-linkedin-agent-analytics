import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import time
from unittest.mock import Mock

import app.ingest as ingest


def test_retry_on_429(monkeypatch):
    responses = [
        Mock(status_code=429, headers={"Retry-After": "0"}),
        Mock(status_code=200, headers={}),
    ]

    responses[1].json.return_value = {
        "data": [
            {
                "id": "test-1",
                "name": "Test Lead",
                "updated_at": "2026-08-22T10:00:00+00:00"
            }
        ]
    }

    def fake_get(*args, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr(ingest.requests, "get", fake_get)
    monkeypatch.setattr(time, "sleep", lambda x: None)

    result = ingest.fetch_with_retry(
        "http://test-api/api/leads",
        {"Authorization": "Bearer test"},
        {}
    )

    assert "data" in result
    assert len(result["data"]) == 1