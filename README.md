# Weekly invoice automation

Every Friday at 7 am (Sydney time) a GitHub Actions job builds my weekly contractor
invoice as a PDF and e-mails it to the client. No server, no database, no manual
steps, and no personal or client data in this repository.

> A real tool I use for my own contract work with a small business, and my first
> portfolio project in process automation.

## The problem
Every week I prepared the same invoice by hand: update the number, the dates and the
service period, recalculate the fee and the superannuation, export to PDF, write the
e-mail. About 20 minutes a week (around 17 hours a year), and easy to get a number or
a date wrong on a document that the client's accountant checks.

## The process, before and after
| Step | Before (manual) | After (automated) |
|---|---|---|
| Invoice number | Look up the last invoice and add one | Derived from the date: `YYYYMM` + which Friday of the month |
| Service period | Count back to the previous Friday | Calculated: the Friday-to-Thursday pay cycle before the invoice |
| Amounts | Calculator | Annual fee / 52, superannuation on its own line, exact to the cent |
| PDF | Edit a template and export it | Generated from the layout the client approved |
| E-mail | Write it, attach the PDF, send | Sent at 7 am every Friday, with me in copy |

## How it works
```
GitHub Actions (cron: Friday 7 am Sydney)        Keepalive (weekly)
        │                                         └─ empty commit + issue after 45 quiet days
        ▼
python -m invoicer --send
        ├─ config.py  → reads the INVOICE_CONFIG secret (never stored in git)
        ├─ calc.py    → number, period, amounts (Decimal, rounded to the cent)
        ├─ pdf.py     → invoice PDF (reportlab)
        └─ mailer.py  → e-mail with the PDF attached (Gmail SMTP)
```

## Business rules
- The weekly fee is the annual fee divided by 52. The invoice never shows hours.
- Superannuation (12 %) is always its own line, as the client's accountant asked.
- Not registered for GST: no GST line, and the title is "INVOICE", not "Tax Invoice".
- The invoice is dated and due on the Friday it is sent.

## Design choices
- **Stateless invoice numbers.** The number comes from the date (e.g. `202611001` is the
  first Friday of November 2026), so no database is needed to remember the last one.
- **Rules isolated and tested.** `calc.py` has no I/O; a golden test checks number,
  period and amounts for a known week, using fake figures.
- **Personal data stays out of the code.** Names, ABNs, bank details, e-mail addresses and
  the real fee live only in an encrypted GitHub secret. The repository has a fake
  `config.example.yml`.
- **Public logs stay clean.** The job prints only the invoice number and period. If it fails
  in GitHub Actions it prints only the error type, because error messages can quote
  config values (tested in `tests/test_cli.py`).
- **Safe rollout.** `SEND_MODE=test` sends only to me until I switch it to `live`.
- **It does not stop silently.** GitHub turns off scheduled workflows in public repositories
  after 60 days without commits. A weekly keepalive job commits before that happens and
  opens an issue so I get an e-mail.

## Run it locally
```bash
pip install -r requirements.txt
cp config.example.yml config.yml      # then edit with your details
python -m invoicer                    # builds this week's PDF in out/
python -m invoicer --date 2026-11-13  # the invoice of a specific Friday
python -m pytest -q
```

## Set up the weekly e-mail
1. In Gmail, turn on 2-step verification and create an **App Password**.
2. In the repo, under **Settings → Secrets and variables → Actions**, add the secrets
   - `INVOICE_CONFIG`: the full contents of your `config.yml`
   - `SMTP_USER`: the Gmail address that sends the invoice
   - `SMTP_PASSWORD`: the App Password
3. Test it: **Actions → Weekly invoice → Run workflow**, fill in a Friday date and tick
   "E-mail the invoice". In test mode it goes only to `email.test_to`.
4. When you are happy with it, add the repo **variable** `SEND_MODE` = `live`.

To change the fee later, edit `billing.annual_salary` in the `INVOICE_CONFIG` secret.
No code changes are needed.

## Tech
Python 3.12 · reportlab · PyYAML · pytest · GitHub Actions (cron, secrets, variables) · Gmail SMTP
