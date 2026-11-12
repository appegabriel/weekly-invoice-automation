from datetime import date
from decimal import Decimal

from invoicer.calc import compute_amounts, fmt_period, invoice_number, service_period


def test_second_invoice_of_november_2026():
    """13 Nov 2026: full week 6-12 Nov, $52,000 / 52 = $1,000.00 + 12% super = $1,120.00."""
    d = date(2026, 11, 13)
    assert invoice_number(d) == "202611002"
    start, end = service_period(d)
    assert fmt_period(start, end) == "6 – 12 November 2026"
    a = compute_amounts("52000", "0.12")
    assert a.services == Decimal("1000.00")
    assert a.superannuation == Decimal("120.00")
    assert a.total == Decimal("1120.00")


def test_number_sequence_within_month():
    assert invoice_number(date(2026, 11, 6)) == "202611001"
    assert invoice_number(date(2026, 11, 27)) == "202611004"
    assert invoice_number(date(2027, 1, 1)) == "202701001"


def test_period_across_months_and_years():
    assert fmt_period(*service_period(date(2026, 12, 4))) == "27 November – 3 December 2026"
    assert fmt_period(*service_period(date(2027, 1, 1))) == "25 – 31 December 2026"
