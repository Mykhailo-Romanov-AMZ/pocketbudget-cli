"""Tests for the CLI command routing (cli.py).

Every command follows the same lifecycle: load the saved state, run the
domain operation, save the result. State therefore persists between
invocations in the data folder.
"""

from pathlib import Path

import pytest

from pocketbudget.cli import main


def run_cli(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *args: str,
) -> None:
    monkeypatch.chdir(tmp_path)
    main(list(args))


def output(capsys: pytest.CaptureFixture[str]) -> str:
    return capsys.readouterr().out


def error_output(capsys: pytest.CaptureFixture[str]) -> str:
    return capsys.readouterr().err


def test_show_balance_for_new_user_is_zero(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run_cli(capsys, monkeypatch, tmp_path, "show-balance")
    assert "Balance: $0.00" in output(capsys)


def test_add_income_records_and_persists(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run_cli(capsys, monkeypatch, tmp_path, "add-income", "500", "Food")
    out = output(capsys)
    assert "Income of $500.00 recorded" in out
    assert "Balance: $500.00" in out
    assert (tmp_path / "data" / "budget.json").exists()

    run_cli(capsys, monkeypatch, tmp_path, "show-balance")
    assert "Balance: $500.00" in output(capsys)


def test_add_expense_records_and_decreases_balance(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run_cli(capsys, monkeypatch, tmp_path, "add-income", "500", "Food")
    run_cli(capsys, monkeypatch, tmp_path, "add-expense", "120", "Food")
    run_cli(capsys, monkeypatch, tmp_path, "show-balance")
    assert "Balance: $380.00" in output(capsys)


def test_add_expense_overdraw_is_blocked(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run_cli(capsys, monkeypatch, tmp_path, "add-income", "50", "Food")
    run_cli(capsys, monkeypatch, tmp_path, "add-expense", "150", "Food")
    assert "Error" in error_output(capsys)

    run_cli(capsys, monkeypatch, tmp_path, "show-balance")
    assert "Balance: $50.00" in output(capsys)


def test_add_expense_exceeding_budget_is_blocked(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run_cli(capsys, monkeypatch, tmp_path, "add-income", "500", "Food")
    run_cli(capsys, monkeypatch, tmp_path, "set-budget", "Food", "200")
    run_cli(capsys, monkeypatch, tmp_path, "add-expense", "150", "Food")
    run_cli(capsys, monkeypatch, tmp_path, "add-expense", "60", "Food")
    assert "Error" in error_output(capsys)

    run_cli(capsys, monkeypatch, tmp_path, "show-balance")
    assert "Balance: $350.00" in output(capsys)


def test_add_expense_rejects_invalid_category(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run_cli(capsys, monkeypatch, tmp_path, "add-income", "500", "Food")
    run_cli(capsys, monkeypatch, tmp_path, "add-expense", "10", "Entertainment")
    assert "Error" in error_output(capsys)


def test_add_income_rejects_invalid_category(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run_cli(capsys, monkeypatch, tmp_path, "add-income", "500", "Entertainment")
    assert "Error" in error_output(capsys)
    run_cli(capsys, monkeypatch, tmp_path, "show-balance")
    assert "Balance: $0.00" in output(capsys)


def test_add_income_rejects_negative_amount(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run_cli(capsys, monkeypatch, tmp_path, "add-income", "-50", "Food")
    assert "Error" in error_output(capsys)
    run_cli(capsys, monkeypatch, tmp_path, "show-balance")
    assert "Balance: $0.00" in output(capsys)


def test_show_history_lists_all_transactions(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run_cli(capsys, monkeypatch, tmp_path, "add-income", "500", "Food")
    run_cli(capsys, monkeypatch, tmp_path, "add-expense", "120", "Food")
    run_cli(capsys, monkeypatch, tmp_path, "show-history")
    out = output(capsys)
    assert "income" in out
    assert "$500.00" in out
    assert "expense" in out
    assert "$120.00" in out
    assert "Food" in out


def test_set_budget_records_a_ceiling(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run_cli(capsys, monkeypatch, tmp_path, "add-income", "500", "Food")
    run_cli(capsys, monkeypatch, tmp_path, "set-budget", "Food", "200")
    assert "Budget set for Food: $200.00" in output(capsys)


def test_show_summary_reports_spending_per_category(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    run_cli(capsys, monkeypatch, tmp_path, "add-income", "1000", "Food")
    run_cli(capsys, monkeypatch, tmp_path, "set-budget", "Food", "200")
    run_cli(capsys, monkeypatch, tmp_path, "set-budget", "Transport", "100")
    run_cli(capsys, monkeypatch, tmp_path, "add-expense", "50", "Food")
    run_cli(capsys, monkeypatch, tmp_path, "add-expense", "40", "Transport")
    run_cli(capsys, monkeypatch, tmp_path, "show-summary")
    out = output(capsys)
    assert "Food" in out
    assert "$150.00" in out
    assert "Transport" in out
    assert "$60.00" in out
