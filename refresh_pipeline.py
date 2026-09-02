import logging
import os
import smtplib
import subprocess
import sys
from email.message import EmailMessage
from datetime import datetime, timezone


logging.basicConfig(
    filename="logs/refresh_pipeline.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)


def run_step(name, command):
    logging.info("Starting step: %s", name)

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    logging.info(
        "%s stdout:\n%s",
        name,
        result.stdout
    )

    if result.stderr:
        logging.warning(
            "%s stderr:\n%s",
            name,
            result.stderr
        )

    if result.returncode != 0:
        raise RuntimeError(
            f"{name} failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    logging.info("Completed step: %s", name)

    return result.stdout


def send_failure_notification(error_message):
    """
    Send an email notification when the refresh pipeline fails.

    SMTP settings are read from environment variables.
    If SMTP is not configured, the failure is still logged.
    """

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    alert_email = os.getenv("ALERT_EMAIL")

    if not all([
        smtp_host,
        smtp_user,
        smtp_password,
        alert_email
    ]):
        logging.warning(
            "SMTP not configured. Failure notification "
            "was logged but no email was sent."
        )
        return

    message = EmailMessage()

    message["Subject"] = "Polluxa Pipeline Failure"
    message["From"] = smtp_user
    message["To"] = alert_email

    message.set_content(
        f"""Polluxa LinkedIn Agent Analytics pipeline failed.

Time:
{datetime.now(timezone.utc).isoformat()}

Error:
{error_message}
"""
    )

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(message)

    logging.info(
        "Failure notification sent to %s",
        alert_email
    )


def refresh_pipeline():
    logging.info("========== REFRESH STARTED ==========")

    try:

        # --------------------------------------------------
        # Step 1: Incremental ingestion
        # --------------------------------------------------
        run_step(
            "Incremental ingestion",
            [sys.executable, "-m", "app.ingest"]
        )

        # --------------------------------------------------
        # Step 2: Load dimensional/star schema
        # --------------------------------------------------
        run_step(
            "Star schema load",
            [sys.executable, "load_star_schema.py"]
        )

        # --------------------------------------------------
        # Step 3: Run data quality checks
        # --------------------------------------------------
        dq_output = run_step(
            "Data quality checks",
            [sys.executable, "dq_checks.py"]
        )

        # --------------------------------------------------
        # Check DQ status
        # --------------------------------------------------
        if "DQ Status: FAIL" in dq_output:
            raise RuntimeError(
                "Data quality checks failed."
            )

        logging.info("========== REFRESH SUCCESS ==========")

        print("REFRESH PIPELINE SUCCESS")
        print("--------------------------------")
        print("1. Incremental ingestion: SUCCESS")
        print("2. Star schema load: SUCCESS")
        print("3. Data quality checks: SUCCESS")

    except Exception as exc:

        error_message = str(exc)

        logging.exception(
            "========== REFRESH FAILED =========="
        )

        print("REFRESH PIPELINE FAILED")
        print("--------------------------------")
        print(error_message)

        send_failure_notification(error_message)

        raise


if __name__ == "__main__":
    refresh_pipeline()