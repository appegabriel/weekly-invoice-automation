"""Command line entry point.

    python -m invoicer                     # build this week's PDF into out/ (no e-mail)
    python -m invoicer --date 2026-11-06   # build the invoice of a specific Friday
    python -m invoicer --send              # build and e-mail it (needs SMTP_* env vars)

SEND_MODE=test (default) e-mails only email.test_to; SEND_MODE=live e-mails the client.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .calc import compute_amounts, fmt_aud, invoice_number, service_period
from .config import SetupError, load_config
from .mailer import build_message, send
from .pdf import Invoice, render_pdf

SMTP_SECRETS = ("SMTP_USER", "SMTP_PASSWORD")


def build_invoice(cfg: dict, invoice_date: date) -> Invoice:
    b = cfg["billing"]
    start, end = service_period(invoice_date)
    amounts = compute_amounts(b["annual_salary"], b.get("superannuation_rate", 0.12))
    return Invoice(invoice_number(invoice_date), invoice_date, invoice_date, start, end, amounts)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="invoicer")
    ap.add_argument("--config", help="YAML file (default: $INVOICE_CONFIG or config.yml)")
    ap.add_argument("--date", help="invoice date YYYY-MM-DD (default: today in the configured timezone)")
    ap.add_argument("--out", default="out", help="output folder")
    ap.add_argument("--send", action="store_true", help="e-mail the invoice")
    args = ap.parse_args(argv)

    if args.send:
        missing = [name for name in SMTP_SECRETS if not os.environ.get(name)]
        if missing:
            raise SetupError(f"Sending needs these secrets: {', '.join(missing)}")

    cfg = load_config(args.config)
    tz = ZoneInfo(cfg["billing"].get("timezone", "Australia/Sydney"))
    inv_date = date.fromisoformat(args.date) if args.date else datetime.now(tz).date()
    inv = build_invoice(cfg, inv_date)

    sup = cfg["supplier"]["name"]
    client = cfg["client"].get("short_name", "Invoice")
    pdf = render_pdf(inv, cfg, Path(args.out) / f"{inv.number} {sup} - {client}.pdf")
    # Keep logs free of amounts and personal data (public repo logs are public).
    print(f"Built invoice {inv.number} for {inv.period}")

    if args.send:
        e = cfg["email"]
        live = os.environ.get("SEND_MODE", "test") == "live"
        to = e["to"] if live else e["test_to"]
        fields = dict(number=inv.number, supplier=sup, period=inv.period, total=fmt_aud(inv.amounts.total))
        msg = build_message(os.environ["SMTP_USER"], to, e.get("cc", []) if live else [],
                            e["subject"].format(**fields), e["body"].format(**fields), pdf)
        send(msg)
        print(f"Sent invoice {inv.number} ({'live' if live else 'test'} mode)")
    return 0


def cli(argv=None) -> int:
    """Run main() without leaking personal data into public CI logs.

    Exception messages can echo config values (a YAML error quotes the offending line,
    for example), and the Actions logs of a public repository are public. So in GitHub
    Actions only the error type is printed; locally the full traceback is kept.
    """
    try:
        return main(argv)
    except SetupError as exc:
        print(f"Setup error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        if os.environ.get("GITHUB_ACTIONS") != "true":
            raise
        print(f"Invoice run failed: {type(exc).__name__}. Details are hidden to keep personal data "
              "out of public logs; run it locally with the same config to see them.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(cli())
