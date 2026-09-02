import sqlite3
from datetime import datetime

DB_PATH = "data/polluxa_analytics.db"


def get_date_key(date_string):
    date = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
    return int(date.strftime("%Y%m%d"))


def load_star_schema():
    conn = sqlite3.connect(DB_PATH)

    try:
        # --------------------------------------------------------
        # Read staging records
        # --------------------------------------------------------
        records = conn.execute("""
            SELECT
                source_id,
                name,
                job_title,
                company,
                status,
                updated_at,
                loaded_at
            FROM leads_staging
            ORDER BY updated_at
        """).fetchall()

        print(f"Staging records found: {len(records)}")

        for (
            source_id,
            name,
            job_title,
            company,
            status,
            updated_at,
            loaded_at
        ) in records:

            # ----------------------------------------------------
            # DIM COMPANY
            # ----------------------------------------------------
            if company:
                conn.execute("""
                    INSERT INTO dim_company(company_name)
                    VALUES (?)
                    ON CONFLICT(company_name) DO NOTHING
                """, (company,))

                company_row = conn.execute("""
                    SELECT company_key
                    FROM dim_company
                    WHERE company_name = ?
                """, (company,)).fetchone()

                company_key = company_row[0]
            else:
                company_key = None

            # ----------------------------------------------------
            # DIM AGENT
            #
            # The mock source does not provide a separate agent_id,
            # so source_id is used as the stable agent identifier
            # for this assessment dataset.
            # ----------------------------------------------------
            agent_id = source_id
            agent_name = name

            agent_row = conn.execute("""
                SELECT agent_key
                FROM dim_agent
                WHERE agent_id = ?
                  AND is_current = 1
            """, (agent_id,)).fetchone()

            if agent_row:
                agent_key = agent_row[0]
            else:
                conn.execute("""
                    INSERT INTO dim_agent (
                        agent_id,
                        agent_name,
                        agent_status,
                        account_tier,
                        effective_from,
                        effective_to,
                        is_current
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    agent_id,
                    agent_name,
                    status,
                    None,
                    updated_at,
                    None,
                    1
                ))

                agent_key = conn.execute("""
                    SELECT agent_key
                    FROM dim_agent
                    WHERE agent_id = ?
                      AND is_current = 1
                """, (agent_id,)).fetchone()[0]

            # ----------------------------------------------------
            # DIM DATE
            # ----------------------------------------------------
            date_key = get_date_key(updated_at)
            date = datetime.fromisoformat(
                updated_at.replace("Z", "+00:00")
            )

            conn.execute("""
                INSERT INTO dim_date (
                    date_key,
                    full_date,
                    year,
                    quarter,
                    month,
                    month_name,
                    day
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(date_key) DO NOTHING
            """, (
                date_key,
                date.strftime("%Y-%m-%d"),
                date.year,
                ((date.month - 1) // 3) + 1,
                date.month,
                date.strftime("%B"),
                date.day
            ))

            # ----------------------------------------------------
            # FACT OUTREACH
            # ----------------------------------------------------
            conn.execute("""
                INSERT INTO fact_outreach (
                    source_id,
                    agent_key,
                    company_key,
                    lead_name,
                    job_title,
                    outreach_status,
                    updated_at,
                    loaded_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    agent_key = excluded.agent_key,
                    company_key = excluded.company_key,
                    lead_name = excluded.lead_name,
                    job_title = excluded.job_title,
                    outreach_status = excluded.outreach_status,
                    updated_at = excluded.updated_at,
                    loaded_at = excluded.loaded_at
            """, (
                source_id,
                agent_key,
                company_key,
                name,
                job_title,
                status,
                updated_at,
                loaded_at
            ))

        conn.commit()

        # --------------------------------------------------------
        # Verification
        # --------------------------------------------------------
        print("\nStar schema load successful!")
        print(
            "dim_agent:",
            conn.execute("SELECT COUNT(*) FROM dim_agent").fetchone()[0]
        )
        print(
            "dim_company:",
            conn.execute("SELECT COUNT(*) FROM dim_company").fetchone()[0]
        )
        print(
            "dim_date:",
            conn.execute("SELECT COUNT(*) FROM dim_date").fetchone()[0]
        )
        print(
            "fact_outreach:",
            conn.execute("SELECT COUNT(*) FROM fact_outreach").fetchone()[0]
        )

    finally:
        conn.close()


if __name__ == "__main__":
    load_star_schema()