"""Pure business rules: dates, invoice number and amounts. No I/O here."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def money(value) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def fmt_aud(value: Decimal) -> str:
    return f"${value:,.2f}"


def fmt_date(d: date) -> str:
    return f"{d.day} {d:%B %Y}"


def fmt_period(start: date, end: date) -> str:
    """'2 – 5 November 2026', or across months '30 October – 2 November 2026'."""
    if start == end:
        return fmt_date(start)
    if (start.year, start.month) == (end.year, end.month):
        return f"{start.day} – {fmt_date(end)}"
    if start.year == end.year:
        return f"{start.day} {start:%B} – {fmt_date(end)}"
    return f"{fmt_date(start)} – {fmt_date(end)}"


def invoice_number(invoice_date: date) -> str:
    """YYYYMM + 3-digit sequence = which invoice-weekday of the month it is.

    6 Nov 2026 is the first Friday of November -> 202611001.
    Deterministic, so no database is needed to remember the last number.
    """
    seq = (invoice_date.day - 1) // 7 + 1
    return f"{invoice_date:%Y%m}{seq:03d}"


def service_period(invoice_date: date) -> tuple[date, date]:
    """Pay cycle is Friday to Thursday: the full week that ends the day before
    the Friday invoice (invoice 13 Nov 2026 -> 6 - 12 Nov 2026)."""
    end = invoice_date - timedelta(days=(invoice_date.weekday() - 3) % 7 or 7)
    return end - timedelta(days=6), end


@dataclass(frozen=True)
class Amounts:
    services: Decimal
    super_rate: Decimal
    superannuation: Decimal
    total: Decimal


def weekly_fee(annual_salary, weeks_per_year=52) -> Decimal:
    """Full weekly fee = annual salary / 52. Invoices never show hours."""
    return money(Decimal(str(annual_salary)) / Decimal(str(weeks_per_year)))


def compute_amounts(annual_salary, super_rate, weeks_per_year=52) -> Amounts:
    super_rate_d = Decimal(str(super_rate))
    services = weekly_fee(annual_salary, weeks_per_year)
    superannuation = money(services * super_rate_d)
    return Amounts(services, super_rate_d, superannuation, services + superannuation)
