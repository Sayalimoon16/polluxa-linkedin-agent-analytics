import sqlite3
from datetime import datetime, timezone
from math import sqrt


DB_PATH = "data/polluxa_analytics.db"


# ============================================================
# PART 1 ACCOUNT AGE CONFIGURATION
# ============================================================

# Assessment Part 1 declared tier
DECLARED_ACCOUNT_AGE_TIER = "1+ Year"

ACCOUNT_AGE_LIMITS = {
    "< 1 Month": {
        "daily_invites": 5,
        "daily_messages": 10,
    },
    "1 Month": {
        "daily_invites": 10,
        "daily_messages": 20,
    },
    "2–6 Months": {
        "daily_invites": 15,
        "daily_messages": 30,
    },
    "6–12 Months": {
        "daily_invites": 20,
        "daily_messages": 40,
    },
    "1+ Year": {
        "daily_invites": 30,
        "daily_messages": 60,
    },
}


# ============================================================
# DATABASE
# ============================================================

def connect():
    return sqlite3.connect(DB_PATH)


# ============================================================
# STATISTICAL HELPERS
# ============================================================

def beta_binomial_smoothed_rate(successes, total):
    """
    Beta(1,1) prior smoothing.
    """
    if total == 0:
        return 0.0

    return (successes + 1) / (total + 2)


def wilson_interval(successes, total, z=1.96):
    """
    Wilson 95% confidence interval.
    """

    if total == 0:
        return 0.0, 0.0

    p = successes / total

    denominator = 1 + (z ** 2 / total)

    centre = (
        p + (z ** 2 / (2 * total))
    ) / denominator

    margin = (
        z
        * sqrt(
            (p * (1 - p) / total)
            + (z ** 2 / (4 * total ** 2))
        )
        / denominator
    )

    lower = max(0.0, centre - margin)
    upper = min(1.0, centre + margin)

    return lower * 100, upper * 100


# ============================================================
# ACCOUNT ANALYSIS
# ============================================================

def analyse_account(conn, agent_key, agent_name):

    rows = conn.execute("""
        SELECT outreach_status
        FROM fact_outreach
        WHERE agent_key = ?
    """, (agent_key,)).fetchall()

    total = len(rows)

    if total == 0:
        return None

    statuses = [
        row[0].lower()
        for row in rows
        if row[0] is not None
    ]

    connected = statuses.count("connected")
    replied = statuses.count("replied")
    pending = statuses.count("pending")
    rejected = statuses.count("rejected")

    # --------------------------------------------------------
    # Raw acceptance rate
    # --------------------------------------------------------

    acceptance_raw = (
        connected / total * 100
        if total
        else 0
    )

    # --------------------------------------------------------
    # Beta-Binomial smoothed acceptance rate
    # --------------------------------------------------------

    acceptance_smoothed = (
        beta_binomial_smoothed_rate(
            connected,
            total
        ) * 100
    )

    # --------------------------------------------------------
    # Reply rate
    # --------------------------------------------------------

    reply_rate = (
        replied / total * 100
        if total
        else 0
    )

    # --------------------------------------------------------
    # Ghosting / pending proxy
    # --------------------------------------------------------

    ghost_rate = (
        pending / total * 100
        if total
        else 0
    )

    # --------------------------------------------------------
    # Rejection rate
    # --------------------------------------------------------

    rejection_rate = (
        rejected / total * 100
        if total
        else 0
    )

    # --------------------------------------------------------
    # Wilson confidence interval
    # --------------------------------------------------------

    ci_low, ci_high = wilson_interval(
        connected,
        total
    )

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    if total < 5:
        confidence = "Low"
    elif total < 30:
        confidence = "Medium"
    else:
        confidence = "High"

    # --------------------------------------------------------
    # Weighted anomaly score
    #
    # Lower acceptance = higher anomaly
    # Lower reply = higher anomaly
    # Pending = higher anomaly
    # Rejection = higher anomaly
    # --------------------------------------------------------

    anomaly_score = (
        (100 - acceptance_smoothed) * 0.40
        + (100 - reply_rate) * 0.20
        + ghost_rate * 0.20
        + rejection_rate * 0.20
    )

    anomaly_score = round(
        min(100, max(0, anomaly_score)),
        2
    )

    # --------------------------------------------------------
    # Risk classification
    # --------------------------------------------------------

    if anomaly_score >= 70:
        risk_level = "HIGH"
    elif anomaly_score >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # --------------------------------------------------------
    # Capacity recommendation
    # --------------------------------------------------------

    tier_limits = ACCOUNT_AGE_LIMITS.get(
        DECLARED_ACCOUNT_AGE_TIER
    )

    if tier_limits is None:

        recommended_invites = None
        recommended_messages = None

        capacity_basis = (
            "Part 1 Account Age tier not available."
        )

    else:

        if risk_level == "HIGH":
            multiplier = 0.50

        elif risk_level == "MEDIUM":
            multiplier = 0.75

        else:
            multiplier = 1.00

        recommended_invites = int(
            tier_limits["daily_invites"] * multiplier
        )

        recommended_messages = int(
            tier_limits["daily_messages"] * multiplier
        )

        capacity_basis = (
            f"Part 1 tier: {DECLARED_ACCOUNT_AGE_TIER}; "
            f"risk multiplier: {multiplier:.2f}"
        )

    # --------------------------------------------------------
    # Notes
    # --------------------------------------------------------

    notes = []

    if total < 5:
        notes.append(
            "Small sample: anomaly estimate has low "
            "statistical confidence."
        )

    if connected == total:
        notes.append(
            "All observed records are connected; "
            "no acceptance-rate collapse is observable "
            "in the current sample."
        )

    if replied == 0:
        notes.append(
            "No replied records observed; "
            "reply-decay trend cannot be established "
            "without historical periods."
        )

    if pending == 0:
        notes.append(
            "No pending records observed; "
            "no ghosting proxy signal is present "
            "in the current sample."
        )

    if rejected == 0:
        notes.append(
            "No rejected records observed."
        )

    notes.append(
        "Historical invite/message volumes and multiple "
        "time periods are required to establish true "
        "decay/collapse trends."
    )

    return {
        "agent_key": agent_key,
        "agent_name": agent_name,

        "observed_records": total,

        "acceptance_rate": acceptance_raw,
        "acceptance_smoothed": acceptance_smoothed,

        "reply_rate": reply_rate,
        "ghost_rate": ghost_rate,
        "rejection_rate": rejection_rate,

        "score": anomaly_score,
        "risk_level": risk_level,
        "confidence": confidence,

        "confidence_interval_95": (
            ci_low,
            ci_high
        ),

        "recommended_invites": recommended_invites,
        "recommended_messages": recommended_messages,

        "capacity_basis": capacity_basis,

        "notes": " ".join(notes),
    }


# ============================================================
# SAVE RESULTS
# ============================================================

def save_result(conn, result):

    lower, upper = result["confidence_interval_95"]

    conn.execute("""
        INSERT INTO risk_model_results (
            calculated_at,
            agent_key,
            agent_name,
            account_tier,
            total_records,
            acceptance_rate,
            acceptance_smoothed,
            reply_rate,
            ghost_rate,
            rejection_rate,
            anomaly_score,
            risk_level,
            confidence,
            confidence_lower,
            confidence_upper,
            recommended_daily_invites,
            recommended_daily_messages,
            recommendation_basis,
            notes
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, (
        datetime.now(timezone.utc).isoformat(),

        result["agent_key"],
        result["agent_name"],
        DECLARED_ACCOUNT_AGE_TIER,

        result["observed_records"],

        result["acceptance_rate"],
        result["acceptance_smoothed"],

        result["reply_rate"],
        result["ghost_rate"],
        result["rejection_rate"],

        result["score"],
        result["risk_level"],
        result["confidence"],

        lower,
        upper,

        result["recommended_invites"],
        result["recommended_messages"],

        result["capacity_basis"],
        result["notes"],
    ))


# ============================================================
# MAIN
# ============================================================

def run_risk_model():

    conn = connect()

    try:

        print()
        print("PART 5 — ADVANCED ANALYTICS & RISK MODELING")
        print("=" * 55)

        print()
        print("STATISTICAL BASIS")
        print("- Beta-Binomial smoothing with Beta(1,1) prior")
        print("- Wilson 95% confidence interval for observed rates")
        print("- Weighted outcome-based anomaly score")
        print("- Small samples are explicitly assigned low confidence")

        print()
        print("RISK SIGNALS")
        print("- Acceptance-rate collapse")
        print("- Reply-rate decay")
        print("- Pending/ghosting proxy")
        print("- Rejection rate")

        print()
        print("CAPACITY BASIS")
        print("- Recommendations never exceed Part 1 ceilings")
        print("- Medium risk: 75% of applicable ceiling")
        print("- High risk: 50% of applicable ceiling")
        print("- Low risk: full applicable ceiling")

        print()
        print("IMPORTANT LIMITATION")
        print(
            "- The current fact table contains only outreach "
            "status events; historical invite/message volumes "
            "and multiple time periods are required to establish "
            "true decay/collapse trends."
        )

        print()
        print(
            f"Declared Part 1 Account Age tier: "
            f"{DECLARED_ACCOUNT_AGE_TIER}"
        )

        agents = conn.execute("""
            SELECT
                agent_key,
                agent_name
            FROM dim_agent
            ORDER BY agent_name
        """).fetchall()

        print()
        print(f"Accounts analysed: {len(agents)}")

        for agent_key, agent_name in agents:

            result = analyse_account(
                conn,
                agent_key,
                agent_name
            )

            if result is None:
                continue

            print()
            print("-" * 55)

            print(
                f"Account: {result['agent_name']}"
            )

            print(
                f"Observed records: "
                f"{result['observed_records']}"
            )

            print(
                f"Acceptance rate: "
                f"{result['acceptance_rate']:.1f}%"
            )

            print(
                f"Smoothed acceptance rate: "
                f"{result['acceptance_smoothed']:.1f}%"
            )

            print(
                f"Reply rate: "
                f"{result['reply_rate']:.1f}%"
            )

            print(
                f"Ghosting proxy: "
                f"{result['ghost_rate']:.1f}%"
            )

            print(
                f"Rejection rate: "
                f"{result['rejection_rate']:.1f}%"
            )

            print(
                f"Anomaly score: "
                f"{result['score']:.2f}/100"
            )

            print(
                f"Risk level: "
                f"{result['risk_level']}"
            )

            print(
                f"Confidence: "
                f"{result['confidence']}"
            )

            lower, upper = result["confidence_interval_95"]

            print(
                f"Acceptance 95% CI: "
                f"{lower:.2f}% – {upper:.0f}%"
            )

            print(
                f"Recommended daily invites: "
                f"{result['recommended_invites']}"
            )

            print(
                f"Recommended daily messages: "
                f"{result['recommended_messages']}"
            )

            print(
                f"Basis: "
                f"{result['capacity_basis']}"
            )

            print(
                f"Notes: "
                f"{result['notes']}"
            )

            save_result(conn, result)

        conn.commit()

        print()
        print("=" * 55)
        print("PART 5 MODEL EXECUTION SUCCESS")
        print("Results saved to: risk_model_results")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    run_risk_model()