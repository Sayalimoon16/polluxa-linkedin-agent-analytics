import logging
import os
import smtplib
import subprocess
import sys
import time
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


def send_alert(subject, message_body):
    """
    Send an email alert using SMTP settings from environment variables.
    If SMTP is not configured, the alert is logged instead.
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
            "SMTP not configured. Alert logged but no email was sent: %s",
            subject
        )
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = smtp_user
    message["To"] = alert_email

    message.set_content(message_body)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(message)

    logging.info(
        "Alert sent: %s to %s",
        subject,
        alert_email
    )


def send_failure_notification(error_message):
    send_alert(
        "Polluxa Pipeline Failure",
        f"""Polluxa LinkedIn Agent Analytics pipeline failed.

Time:
{datetime.now(timezone.utc).isoformat()}

Error:
{error_message}
"""
    )


def send_dq_alert(dq_output):
    send_alert(
        "Polluxa Data Quality Breach",
        f"""Polluxa LinkedIn Agent Analytics detected a data-quality threshold breach.

Time:
{datetime.now(timezone.utc).isoformat()}

DQ Result:
{dq_output}
"""
    )


def send_duration_alert(duration_seconds, threshold_seconds):
    send_alert(
        "Polluxa Abnormal Run Duration",
        f"""Polluxa LinkedIn Agent Analytics pipeline exceeded the configured run-duration threshold.

Time:
{datetime.now(timezone.utc).isoformat()}

Run duration:
{duration_seconds:.2f} seconds

Configured threshold:
{threshold_seconds} seconds
"""
    )


def refresh_pipeline():
    logging.info("========== REFRESH STARTED ==========")

    pipeline_start = time.monotonic()

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
            send_dq_alert(dq_output)
            raise RuntimeError(
                "Data quality checks failed."
            )

        # --------------------------------------------------
        # Check abnormal pipeline duration
        # --------------------------------------------------
        duration_seconds = time.monotonic() - pipeline_start
        threshold_seconds = float(
            os.getenv("MAX_RUN_DURATION_SECONDS", "300")
        )

        logging.info(
            "Pipeline duration: %.2f seconds; threshold: %.2f seconds",
            duration_seconds,
            threshold_seconds
        )

        if duration_seconds > threshold_seconds:
            send_duration_alert(
                duration_seconds,
                threshold_seconds
            )

        logging.info("========== REFRESH SUCCESS ==========")

        print("REFRESH PIPELINE SUCCESS")
        print("--------------------------------")
        print("1. Incremental ingestion: SUCCESS")
        print("2. Star schema load: SUCCESS")
        print("3. Data quality checks: SUCCESS")
        print(f"4. Run duration: {duration_seconds:.2f} seconds")

        if duration_seconds > threshold_seconds:
            print(
                f"WARNING: Run duration exceeded "
                f"threshold of {threshold_seconds:.0f} seconds"
            )

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
