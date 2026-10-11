"""
Deterministic return-window assessment.

Uses the synthetic order delivery date and a fixed
reference date. Does not approve or reject returns.
"""

from datetime import date


def assess_return_window(
    delivery_date,
    reference_date="2026-09-30",
    return_window_days=30,
):
    if not delivery_date:
        return {
            "status": "unknown",
            "reason": "No delivery date is available.",
        }

    delivered = date.fromisoformat(str(delivery_date))
    reference = date.fromisoformat(str(reference_date))

    elapsed_days = (reference - delivered).days

    if elapsed_days < 0:
        return {
            "status": "unknown",
            "reason": (
                "The recorded delivery date is in the future."
            ),
        }

    within_window = elapsed_days <= return_window_days

    return {
        "status": (
            "within_window"
            if within_window
            else "outside_window"
        ),
        "elapsed_days": elapsed_days,
        "return_window_days": return_window_days,
        "days_over_limit": max(
            0,
            elapsed_days - return_window_days,
        ),
        "reference_date": reference.isoformat(),
        "delivery_date": delivered.isoformat(),
    }
