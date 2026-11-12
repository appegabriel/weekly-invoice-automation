"""Load the YAML configuration from a file or from the INVOICE_CONFIG env var."""
from __future__ import annotations

import os
from pathlib import Path

import yaml

REQUIRED_SECTIONS = ("supplier", "client", "billing", "payment", "email")


class SetupError(Exception):
    """A setup problem whose message never contains personal data, so it is safe to
    print in public CI logs (unlike most exception messages, see __main__.cli)."""


def load_config(path: str | None = None) -> dict:
    raw = os.environ.get("INVOICE_CONFIG")
    if path:
        raw = Path(path).read_text(encoding="utf-8")
    elif not raw:
        default = Path("config.yml")
        if not default.exists():
            raise SetupError("No configuration found: set the INVOICE_CONFIG secret or create config.yml")
        raw = default.read_text(encoding="utf-8")
    cfg = yaml.safe_load(raw)
    if not isinstance(cfg, dict):
        raise SetupError("The configuration must be a YAML mapping like config.example.yml")
    missing = [s for s in REQUIRED_SECTIONS if s not in cfg]
    if missing:
        raise SetupError(f"Config is missing sections: {', '.join(missing)}")
    cfg.setdefault("services_provided", [])
    return cfg
