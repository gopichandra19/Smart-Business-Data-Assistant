"""Time period resolver - deterministic business time interpretation."""

from datetime import date, timedelta
from typing import Optional
import re


def resolve_time_period(period: str, reference_date: Optional[date] = None) -> dict:
    """
    Resolve a natural-language time period to concrete date boundaries.

    Supports: today, yesterday, this/last week, this/last month,
    this/last quarter, this/last year, Q1-Q4 YYYY, YYYY-MM, etc.

    Returns: {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "label": "..."}
    """
    ref = reference_date or date.today()
    period_lower = period.lower().strip()

    # Today / Yesterday
    if period_lower == "today":
        return _result(ref, ref, "Today")

    if period_lower == "yesterday":
        yesterday = ref - timedelta(days=1)
        return _result(yesterday, yesterday, "Yesterday")

    # This/Last Week
    if period_lower in ("this week", "current week"):
        start = ref - timedelta(days=ref.weekday())
        return _result(start, ref, "This Week")

    if period_lower == "last week":
        end = ref - timedelta(days=ref.weekday() + 1)
        start = end - timedelta(days=6)
        return _result(start, end, "Last Week")

    # This/Last Month
    if period_lower in ("this month", "current month"):
        start = ref.replace(day=1)
        return _result(start, ref, "This Month")

    if period_lower == "last month":
        first_of_month = ref.replace(day=1)
        end = first_of_month - timedelta(days=1)
        start = end.replace(day=1)
        return _result(start, end, "Last Month")

    # This/Last Quarter
    if period_lower in ("this quarter", "current quarter"):
        q_start = _quarter_start(ref)
        return _result(q_start, ref, f"This Quarter (Q{_get_quarter(ref)})")

    if period_lower in ("last quarter", "previous quarter"):
        q_start = _quarter_start(ref)
        prev_q_end = q_start - timedelta(days=1)
        prev_q_start = _quarter_start(prev_q_end)
        q_num = _get_quarter(prev_q_start)
        return _result(prev_q_start, prev_q_end, f"Last Quarter (Q{q_num} {prev_q_start.year})")

    # This/Last Year
    if period_lower in ("this year", "current year", "ytd"):
        start = ref.replace(month=1, day=1)
        return _result(start, ref, f"Year to Date ({ref.year})")

    if period_lower == "last year":
        start = date(ref.year - 1, 1, 1)
        end = date(ref.year - 1, 12, 31)
        return _result(start, end, f"Last Year ({ref.year - 1})")

    # Last N months
    match = re.match(r"last (\d+) months?", period_lower)
    if match:
        months = int(match.group(1))
        start = _subtract_months(ref, months)
        return _result(start, ref, f"Last {months} Month{'s' if months > 1 else ''}")

    # Last N days
    match = re.match(r"last (\d+) days?", period_lower)
    if match:
        days = int(match.group(1))
        start = ref - timedelta(days=days)
        return _result(start, ref, f"Last {days} Days")

    # Specific quarter (e.g., Q3 2026, Q3, q3 2025)
    match = re.match(r"q([1-4])\s*(\d{4})?", period_lower)
    if match:
        q = int(match.group(1))
        year = int(match.group(2)) if match.group(2) else ref.year
        start = date(year, (q - 1) * 3 + 1, 1)
        if q == 4:
            end = date(year, 12, 31)
        else:
            end = date(year, q * 3 + 1, 1) - timedelta(days=1)
        return _result(start, end, f"Q{q} {year}")

    # Specific year
    match = re.match(r"^(\d{4})$", period_lower)
    if match:
        year = int(match.group(1))
        return _result(date(year, 1, 1), date(year, 12, 31), str(year))

    # Specific month (YYYY-MM)
    match = re.match(r"(\d{4})-(\d{2})", period_lower)
    if match:
        year, month = int(match.group(1)), int(match.group(2))
        start = date(year, month, 1)
        if month == 12:
            end = date(year, 12, 31)
        else:
            end = date(year, month + 1, 1) - timedelta(days=1)
        return _result(start, end, f"{start.strftime('%B %Y')}")

    # Default: last 90 days
    start = ref - timedelta(days=90)
    return _result(start, ref, f"Last 90 Days (default for: '{period}')")


def _result(start: date, end: date, label: str) -> dict:
    return {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "label": label,
    }


def _get_quarter(d: date) -> int:
    return (d.month - 1) // 3 + 1


def _quarter_start(d: date) -> date:
    q = _get_quarter(d)
    return date(d.year, (q - 1) * 3 + 1, 1)


def _subtract_months(d: date, months: int) -> date:
    month = d.month - months
    year = d.year
    while month <= 0:
        month += 12
        year -= 1
    try:
        return d.replace(year=year, month=month)
    except ValueError:
        # Handle edge cases like Feb 30
        return d.replace(year=year, month=month, day=28)
