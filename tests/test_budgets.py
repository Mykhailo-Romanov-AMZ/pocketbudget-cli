"""Tests for category budgets (rules.md, Rules 2, 3 and 4).

- Rule 2: only "Food" and "Transport" are valid categories; anything else errors.
- Rule 3: an expense larger than the total balance is still blocked.
- Rule 4: an expense that exceeds a category's remaining budget is blocked,
  even when the balance could still cover it.
"""

import pytest

from pocketbudget.account import Account
from pocketbudget.exceptions import (
    InsufficientFundsError,
    InvalidCategoryError,
    OverBudgetError,
)


def test_budget_can_be_set_for_a_category() -> None:
    account = Account()
    account.set_budget("Food", 200)
    assert account.get_budget("Food") == 200


def test_remaining_budget_counts_expenses_in_that_category() -> None:
    account = Account()
    account.add_income(500)
    account.set_budget("Food", 200)
    account.add_expense(150, "Food")
    assert account.get_remaining_budget("Food") == 50


def test_expense_within_budget_is_recorded() -> None:
    account = Account()
    account.add_income(500)
    account.set_budget("Food", 200)
    account.add_expense(120, "Food")
    assert account.balance == 380
    assert account.get_remaining_budget("Food") == 80


def test_expense_exceeding_category_budget_is_blocked() -> None:
    account = Account()
    account.add_income(500)
    account.set_budget("Food", 200)
    account.add_expense(150, "Food")
    with pytest.raises(OverBudgetError):
        account.add_expense(60, "Food")
    assert account.balance == 350
    assert account.get_remaining_budget("Food") == 50
    assert ("expense", 60, "Food") not in account.get_transactions()
    assert len(account.get_transactions()) == 2


def test_expense_matching_remaining_budget_is_allowed() -> None:
    account = Account()
    account.add_income(500)
    account.set_budget("Food", 200)
    account.add_expense(200, "Food")
    assert account.balance == 300
    assert account.get_remaining_budget("Food") == 0


def test_expense_without_a_budget_is_unrestricted() -> None:
    account = Account()
    account.add_income(500)
    account.add_expense(300, "Transport")
    assert account.balance == 200
    assert account.get_remaining_budget("Transport") is None


def test_budgets_are_tracked_per_category() -> None:
    account = Account()
    account.add_income(1000)
    account.set_budget("Food", 200)
    account.set_budget("Transport", 100)
    account.add_expense(150, "Food")
    account.add_expense(40, "Transport")
    assert account.get_remaining_budget("Food") == 50
    assert account.get_remaining_budget("Transport") == 60


def test_invalid_category_is_rejected() -> None:
    account = Account()
    account.add_income(500)
    with pytest.raises(InvalidCategoryError):
        account.add_expense(50, "Entertainment")


def test_set_budget_rejects_invalid_category() -> None:
    account = Account()
    with pytest.raises(InvalidCategoryError):
        account.set_budget("Entertainment", 100)


def test_balance_rule_still_blocks_overdrawing_within_budget() -> None:
    account = Account()
    account.add_income(50)
    account.set_budget("Food", 200)
    with pytest.raises(InsufficientFundsError):
        account.add_expense(150, "Food")
