import pytest
import yaml

from invoicer.__main__ import cli

# A broken config whose YAML error message would quote the line holding the "secret".
BROKEN_CONFIG = "supplier:\n  abn: [SECRET-ABN-123\n"


def test_ci_failure_hides_config_values(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("INVOICE_CONFIG", BROKEN_CONFIG)
    assert cli(["--out", str(tmp_path)]) == 1
    out = capsys.readouterr()
    assert "SECRET-ABN-123" not in out.out + out.err
    assert "Invoice run failed" in out.err


def test_local_failure_keeps_full_error(monkeypatch, tmp_path):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setenv("INVOICE_CONFIG", BROKEN_CONFIG)
    with pytest.raises(yaml.YAMLError):
        cli(["--out", str(tmp_path)])


def test_missing_smtp_secrets_is_a_clear_setup_error(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    assert cli(["--send", "--out", str(tmp_path)]) == 1
    assert "SMTP_USER, SMTP_PASSWORD" in capsys.readouterr().err
