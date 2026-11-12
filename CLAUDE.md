# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is
A weekly invoice generator for a contractor (Gabriel Brito Appe) billing one small-business
client. Every Friday morning (Sydney time) GitHub Actions builds the PDF invoice and e-mails
it. The owner of this repo writes in Portuguese; reply in Portuguese, but keep code,
comments, commit messages and the invoice itself in English.

## Layout
- `invoicer/calc.py` – pure rules: invoice number, service period, amounts. No I/O.
- `invoicer/pdf.py` – PDF layout (reportlab). Mirrors the invoice the client approved.
- `invoicer/mailer.py` – SMTP sending (Gmail + App Password by default).
- `invoicer/config.py` – loads the YAML config; `SetupError` = messages safe for public logs.
- `invoicer/__main__.py` – CLI: `python -m invoicer [--date] [--send]`; `cli()` hides
  exception details in GitHub Actions.
- `config.example.yml` – fake data showing every config field.
- `.github/workflows/weekly-invoice.yml` – Friday schedule + manual run button.
- `.github/workflows/keepalive.yml` – empty commit + issue after 45 days without commits
  (GitHub disables schedules in public repos after 60 quiet days).
- `tests/` – pytest. `test_second_invoice_of_november_2026` is the golden test (fake salary).

## Business rules (do not change without the owner asking)
- Invoice number = `YYYYMM` + 3-digit index of the Friday in the month (6 Nov 2026 -> 202611001).
- Invoice date = due date = the Friday ("Due on receipt").
- Service period = the full pay cycle Friday to Thursday before the invoice Friday.
- Fee = `billing.annual_salary` / 52 per week. The real figure lives only in the secret.
- NEVER show or calculate hours on an invoice. The owner was explicit about this.
- Superannuation (12% of services) is ALWAYS its own line on the invoice.
- Not registered for GST: no GST line, title is "INVOICE" (not "Tax Invoice").
- Money uses `Decimal` with ROUND_HALF_UP to the cent. Never floats for money.

## Privacy (public portfolio repo)
- The client's name never goes into git (owner's decision, to avoid any legal exposure).
  Public files say "a small business" / "the client"; the name lives only in the config.
- Real ABNs, bank details, addresses, e-mail addresses and the real salary never go into git.
  They live in the `INVOICE_CONFIG` GitHub secret (a full YAML like config.example.yml).
- `config.yml`, `START-HERE.md` and `*.pdf` are git-ignored. Do not commit generated invoices.
- Workflow logs are public: never print amounts, addresses or bank details.
- Commits use the GitHub noreply address (repo-local git config), never a personal e-mail.

## Commands
```bash
pip install -r requirements.txt
python -m pytest -q
cp config.example.yml config.yml && python -m invoicer --date 2026-11-13   # PDF in out/
```

## Sending modes
Repo variable `SEND_MODE`: `test` (default) sends only to `email.test_to`;
`live` sends to `email.to` with `email.cc` copied.
