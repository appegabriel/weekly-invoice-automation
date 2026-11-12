"""Render the invoice PDF (layout of the approved 202611001 invoice)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .calc import Amounts, fmt_aud, fmt_date, fmt_period

NAVY = colors.HexColor("#1F3864")
GREY = colors.HexColor("#555555")
RULE = colors.HexColor("#D0D0D0")


@dataclass(frozen=True)
class Invoice:
    number: str
    invoice_date: date
    due_date: date
    period_start: date
    period_end: date
    amounts: Amounts

    @property
    def period(self) -> str:
        return fmt_period(self.period_start, self.period_end)


def _styles():
    s = {}
    s["title"] = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=24, leading=28, textColor=NAVY)
    s["body"] = ParagraphStyle("body", fontName="Helvetica", fontSize=9, leading=12)
    s["bold"] = ParagraphStyle("bold", parent=s["body"], fontName="Helvetica-Bold")
    s["right"] = ParagraphStyle("right", parent=s["body"], alignment=TA_RIGHT)
    s["head"] = ParagraphStyle("head", fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=NAVY, spaceBefore=10)
    s["small"] = ParagraphStyle("small", fontName="Helvetica", fontSize=7.5, leading=10, textColor=GREY)
    return s


def _p(text, style):
    return Paragraph(escape(str(text)), style)


def render_pdf(inv: Invoice, cfg: dict, out_path: Path) -> Path:
    s = _styles()
    sup, cli, pay = cfg["supplier"], cfg["client"], cfg["payment"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(out_path), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=14 * mm, bottomMargin=16 * mm,
                            title=f"Invoice {inv.number}", author=sup["name"])
    width = doc.width
    story = []

    # Header: supplier on the left, invoice facts on the right.
    left = [_p("INVOICE", s["title"]), Spacer(1, 2), _p(sup["name"], s["bold"]), _p(f"ABN {sup['abn']}", s["body"]),
            _p(sup["address"], s["body"]), _p(sup["email"], s["body"]), _p(sup["phone"], s["body"])]
    facts = [("Invoice no.", inv.number), ("Invoice date", fmt_date(inv.invoice_date)),
             ("Due date", fmt_date(inv.due_date)), ("Service period", inv.period)]
    right = Table([[_p(k, s["bold"]), _p(v, s["body"])] for k, v in facts], colWidths=[24 * mm, 42 * mm])
    right.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]))
    header = Table([[left, right]], colWidths=[width - 68 * mm, 68 * mm])
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story += [header, Spacer(1, 8)]

    # Bill to.
    contact = " · ".join(x for x in (cli.get("address"), cli.get("phone"), cli.get("email")) if x)
    story += [_p("BILL TO", s["head"]), _p(cli["name"], s["bold"]), _p(f"ABN {cli['abn']}", s["body"]),
              _p(contact, s["body"]), Spacer(1, 8)]

    # Line items. Superannuation always gets its own line.
    a = inv.amounts
    billing = cfg["billing"]
    pct = f"{(a.super_rate * 100).normalize():f}%"
    rows = [
        [_p("Description", ParagraphStyle("th", parent=s["bold"], textColor=colors.white)),
         _p("Amount (AUD)", ParagraphStyle("thr", parent=s["bold"], textColor=colors.white, alignment=TA_RIGHT))],
        [_p(f"{billing['service_description']}, {inv.period}", s["body"]), _p(fmt_aud(a.services), s["right"])],
        [_p(f"Superannuation ({pct})", s["body"]), _p(fmt_aud(a.superannuation), s["right"])],
        [_p("Total due", ParagraphStyle("tot", parent=s["bold"], fontSize=11, leading=14)),
         _p(fmt_aud(a.total), ParagraphStyle("totr", parent=s["bold"], fontSize=11, leading=14, alignment=TA_RIGHT))],
    ]
    items = Table(rows, colWidths=[width - 40 * mm, 40 * mm])
    items.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("LINEBELOW", (0, 1), (-1, 1), 0.5, RULE),
        ("LINEABOVE", (0, 3), (-1, 3), 1.5, NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story += [items, Spacer(1, 6),
              _p("No GST has been charged. Supplier is not registered for GST.", s["small"])]

    if cfg.get("services_provided"):
        bullets = [ListItem(_p(t, s["body"]), leftIndent=12) for t in cfg["services_provided"]]
        story += [Spacer(1, 6), _p("SERVICES PROVIDED", s["head"]),
                  ListFlowable(bullets, bulletType="bullet", start="•", leftIndent=12, bulletFontSize=8)]

    story += [Spacer(1, 6), _p("PAYMENT DETAILS", s["head"]),
              _p(f"Account name: {pay['account_name']}", s["body"]), _p(f"BSB: {pay['bsb']}", s["body"]),
              _p(f"Account no.: {pay['account_number']}", s["body"]), _p(f"Reference: {inv.number}", s["body"]),
              Spacer(1, 6), _p(f"Payment terms: {pay['terms']} ({fmt_date(inv.due_date)})", s["small"])]

    doc.build(story)
    return out_path
