"""Tests for domain error handling.

Deliberately bad data must produce the correct custom exception, and
validation must happen before any state changes (balance, history and
budgets are all left untouched by a rejected operation).
"""

import json
from pathlib import Path

import pytest

from pocketbudget.account import Account
from pocketbudget.exceptions import (
    DataLoadError,
    InsufficientFundsError,
    InvalidAmountError,
    InvalidCategoryError,
    OverBudgetError,
)
from pocketbudget.storage import load


def test_negative_income_raises_invalid_amount_error() -> None:
    account = Account()
    with pytest.raises(InvalidAmountError) as excinfo:
        account.add_income(-100)
    assert type(excinfo.value) is InvalidAmountError
    assert account.balance == 0
    assert account.get_transactions() == []


def test_negative_expense_raises_invalid_amount_error() -> None:
    account = Account()
    account.add_income(500)
    with pytest.raises(InvalidAmountError):
        account.add_expense(-50, "Food")
    assert account.balance == 500
    assert len(account.get_transactions()) == 1


def test_negative_budget_limit_raises_invalid_amount_error() -> None:
    account = Account()
    with pytest.raises(InvalidAmountError):
        account.set_budget("Food", -10)
    assert account.get_budget("Food") is None


def test_expense_exceeding_budget_raises_over_budget_error() -> None:
    account = Account()
    account.add_income(1000)
    account.set_budget("Food", 200)
    account.add_expense(150, "Food")
    with pytest.raises(OverBudgetError) as excinfo:
        account.add_expense(60, "Food")
    assert type(excinfo.value) is OverBudgetError
    assert account.balance == 850
    assert account.get_remaining_budget("Food") == 50
    assert len(account.get_transactions()) == 2


def test_overdrawing_raises_insufficient_funds_error() -> None:
    account = Account()
    account.add_income(100)
    with pytest.raises(InsufficientFundsError):
        account.add_expense(200, "Food")
    assert account.balance == 100
    assert len(account.get_transactions()) == 1


def test_invalid_expense_category_raises_invalid_category_error() -> None:
    account = Account()
    account.add_income(500)
    with pytest.raises(InvalidCategoryError):
        account.add_expense(10, "Entertainment")
    assert account.balance == 500


def test_invalid_budget_category_raises_invalid_category_error() -> None:
    account = Account()
    with pytest.raises(InvalidCategoryError):
        account.set_budget("Entertainment", 100)
    assert account.budgeted_categories() == []


def test_corrupted_json_raises_data_load_error(tmp_path: Path) -> None:
    path = tmp_path / "budget.json"
    path.write_text("{ this is not valid json")

    with pytest.raises(DataLoadError):
        load(path)


def test_balance_with_wrong_type_raises_data_load_error(tmp_path: Path) -> None:
    path = tmp_path / "budget.json"
    path.write_text(json.dumps({"balance": "abc", "history": [], "budgets": {}}))

    with pytest.raises(DataLoadError):
        load(path)


def test_negative_amount_in_save_file_raises_data_load_error(
    tmp_path: Path,
) -> None:
    path = tmp_path / "budget.json"
    path.write_text(
        json.dumps({"balance": 100, "history": [["income", -50, None]], "budgets": {}})
    )

    with pytest.raises(DataLoadError):
        load(path)


def test_overdrawn_history_in_save_file_raises_data_load_error(
    tmp_path: Path,
) -> None:
    path = tmp_path / "budget.json"
    path.write_text(
        json.dumps({"balance": 0, "history": [["expense", 500, "Food"]], "budgets": {}})
    )

    with pytest.raises(DataLoadError):
        load(path)


def test_invalid_budget_category_in_save_file_raises_data_load_error(
    tmp_path: Path,
) -> None:
    path = tmp_path / "budget.json"
    path.write_text(
        json.dumps({"balance": 0, "history": [], "budgets": {"Entertainment": 100}})
    )

    with pytest.raises(DataLoadError):
        load(path)
