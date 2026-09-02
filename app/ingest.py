import json
import logging
import os
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

SOURCE_API_URL = os.getenv("SOURCE_API_URL", "http://127.0.0.1:8000")
SOURCE_API_KEY = os.getenv("SOURCE_API_KEY", "change-me")
DB_PATH = os.getenv("DATABASE_PATH", "data/polluxa_analytics.db")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))

Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
Path("logs").mkdir(exist_ok=True)


# ---------------------------------------------------------
# Structured JSON Logging
# ---------------------------------------------------------

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", None)
        }

        return json.dumps(log_entry)


logger = logging.getLogger("polluxa_ingestion")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("logs/ingestion.log")
file_handler.setFormatter(JsonFormatter())

logger.handlers.clear()
logger.addHandler(file_handler)


# ---------------------------------------------------------
# Database Connection
# ---------------------------------------------------------

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------
# Database Initialization
# ---------------------------------------------------------

def init_db(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS ingestion_runs (
        run_id TEXT PRIMARY KEY,
        started_at TEXT NOT NULL,
        ended_at TEXT,
        rows_in INTEGER DEFAULT 0,
        rows_out INTEGER DEFAULT 0,
        status TEXT NOT NULL,
        error_message TEXT
    );

    CREATE TABLE IF NOT EXISTS leads_staging (
        source_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        job_title TEXT,
        company TEXT,
        status TEXT,
        updated_at TEXT NOT NULL,
        loaded_at TEXT NOT NULL,
        raw_json TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS dead_letter (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        payload TEXT NOT NULL,
        error_message TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS pipeline_state (
        pipeline_name TEXT PRIMARY KEY,
        watermark TEXT
    );
    """)
    conn.commit()


# ---------------------------------------------------------
# Watermark
# ---------------------------------------------------------

def get_watermark(conn):
    row = conn.execute(
        "SELECT watermark FROM pipeline_state WHERE pipeline_name='leads'"
    ).fetchone()

    return row[0] if row else None


def save_watermark(conn, watermark):
    conn.execute("""
        INSERT INTO pipeline_state(pipeline_name, watermark)
        VALUES('leads', ?)
        ON CONFLICT(pipeline_name)
        DO UPDATE SET watermark=excluded.watermark
    """, (watermark,))

    conn.commit()


# ---------------------------------------------------------
# API Request With Retry
# ---------------------------------------------------------

def fetch_with_retry(url, headers, params, correlation_id=None):
    delay = 1

    for _ in range(MAX_RETRIES):

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

        if response.status_code == 200:
            logger.info(
                "API request successful",
                extra={"correlation_id": correlation_id}
            )
            return response.json()

        if response.status_code == 429 or response.status_code >= 500:

            retry_after = response.headers.get("Retry-After")

            sleep_for = float(retry_after) if retry_after else delay

            logger.warning(
                f"Retryable HTTP {response.status_code}; sleeping {sleep_for:.1f}s",
                extra={"correlation_id": correlation_id}
            )

            time.sleep(sleep_for)

            delay = min(delay * 2, 60)

            continue

        response.raise_for_status()

    raise RuntimeError("API failed after maximum retries")


# ---------------------------------------------------------
# Main Ingestion Pipeline
# ---------------------------------------------------------

def run_ingestion():

    # One correlation ID for the complete pipeline run
    correlation_id = str(uuid.uuid4())

    # Keep run_id aligned with correlation_id
    run_id = correlation_id

    started = datetime.now(timezone.utc).isoformat()

    conn = connect()
    init_db(conn)

    conn.execute(
        """
        INSERT INTO ingestion_runs(
            run_id,
            started_at,
            status
        )
        VALUES(?,?,?)
        """,
        (
            run_id,
            started,
            "RUNNING"
        )
    )

    conn.commit()

    rows_in = 0
    rows_out = 0

    logger.info(
        "Pipeline run started",
        extra={
            "correlation_id": correlation_id
        }
    )

    try:

        # -------------------------------------------------
        # Get Watermark
        # -------------------------------------------------

        watermark = get_watermark(conn)

        logger.info(
            f"Watermark retrieved: {watermark}",
            extra={
                "correlation_id": correlation_id
            }
        )

        # -------------------------------------------------
        # Fetch Source Data
        # -------------------------------------------------

        payload = fetch_with_retry(
            f"{SOURCE_API_URL}/api/leads",
            {
                "Authorization": f"Bearer {SOURCE_API_KEY}"
            },
            {
                "updated_since": watermark,
                "limit": BATCH_SIZE
            },
            correlation_id
        )

        records = payload.get("data", [])

        rows_in = len(records)

        logger.info(
            f"Records fetched: {rows_in}",
            extra={
                "correlation_id": correlation_id
            }
        )

        max_updated = watermark

        # -------------------------------------------------
        # Process Records
        # -------------------------------------------------

        for record in records:

            try:

                if any(
                    not record.get(k)
                    for k in ["id", "name", "updated_at"]
                ):
                    raise ValueError("Missing required field")

                now = datetime.now(timezone.utc).isoformat()

                conn.execute(
                    """
                    INSERT INTO leads_staging
                    (
                        source_id,
                        name,
                        job_title,
                        company,
                        status,
                        updated_at,
                        loaded_at,
                        raw_json
                    )
                    VALUES (?,?,?,?,?,?,?,?)

                    ON CONFLICT(source_id)
                    DO UPDATE SET

                        name=excluded.name,
                        job_title=excluded.job_title,
                        company=excluded.company,
                        status=excluded.status,
                        updated_at=excluded.updated_at,
                        loaded_at=excluded.loaded_at,
                        raw_json=excluded.raw_json
                    """,
                    (
                        record["id"],
                        record["name"],
                        record.get("job_title"),
                        record.get("company"),
                        record.get("status"),
                        record["updated_at"],
                        now,
                        json.dumps(record)
                    )
                )

                rows_out += 1

                if (
                    max_updated is None
                    or record["updated_at"] > max_updated
                ):
                    max_updated = record["updated_at"]

            except Exception as exc:

                conn.execute(
                    """
                    INSERT INTO dead_letter(
                        run_id,
                        payload,
                        error_message,
                        created_at
                    )
                    VALUES(?,?,?,?)
                    """,
                    (
                        run_id,
                        json.dumps(record),
                        str(exc),
                        datetime.now(timezone.utc).isoformat()
                    )
                )

                logger.error(
                    f"Record moved to dead-letter: {exc}",
                    extra={
                        "correlation_id": correlation_id
                    }
                )

        conn.commit()

        # -------------------------------------------------
        # Save Watermark
        # -------------------------------------------------

        if (
            max_updated
            and max_updated != watermark
        ):
            save_watermark(
                conn,
                max_updated
            )

            logger.info(
                f"Watermark updated: {max_updated}",
                extra={
                    "correlation_id": correlation_id
                }
            )

        # -------------------------------------------------
        # Mark Run Successful
        # -------------------------------------------------

        ended = datetime.now(timezone.utc).isoformat()

        conn.execute(
            """
            UPDATE ingestion_runs
            SET
                ended_at=?,
                rows_in=?,
                rows_out=?,
                status='SUCCESS'
            WHERE run_id=?
            """,
            (
                ended,
                rows_in,
                rows_out,
                run_id
            )
        )

        conn.commit()

        logger.info(
            f"Pipeline run completed successfully; "
            f"rows_in={rows_in}, rows_out={rows_out}",
            extra={
                "correlation_id": correlation_id
            }
        )

        return {
            "run_id": run_id,
            "rows_in": rows_in,
            "rows_out": rows_out
        }

    except Exception as exc:

        conn.rollback()

        ended = datetime.now(timezone.utc).isoformat()

        conn.execute(
            """
            UPDATE ingestion_runs
            SET
                ended_at=?,
                rows_in=?,
                rows_out=?,
                status='FAILED',
                error_message=?
            WHERE run_id=?
            """,
            (
                ended,
                rows_in,
                rows_out,
                str(exc),
                run_id
            )
        )

        conn.commit()

        logger.exception(
            "Pipeline run failed",
            extra={
                "correlation_id": correlation_id
            }
        )

        raise

    finally:

        conn.close()

        logger.info(
            "Database connection closed",
            extra={
                "correlation_id": correlation_id
            }
        )


# ---------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------

if __name__ == "__main__":
    print(run_ingestion())