from datetime import date
from pathlib import Path

from invoicer.__main__ import build_invoice
from invoicer.config import load_config
from invoicer.pdf import render_pdf


def test_pdf_builds_from_example_config(tmp_path):
    cfg = load_config(str(Path(__file__).parent.parent / "config.example.yml"))
    inv = build_invoice(cfg, date(2026, 11, 13))
    pdf = render_pdf(inv, cfg, tmp_path / "x.pdf")
    assert pdf.read_bytes()[:4] == b"%PDF"
