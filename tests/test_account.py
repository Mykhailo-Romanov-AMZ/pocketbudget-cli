"""Tests for the protected Account class.

The Account class is the single source of truth for the balance:
- the balance can be read but never assigned from outside,
- the only entry points that change it are add_income() and add_expense(),
- every transaction is validated before it touches the balance,
- overdrawing is blocked (see rules.md, Rule 3).
"""

import pytest

from pocketbudget.account import Account
from pocketbudget.exceptions import InsufficientFundsError, InvalidAmountError


def test_new_account_starts_at_zero_balance() -> None:
    account = Account()
    assert account.balance == 0


def test_balance_can_be_read_from_outside() -> None:
    account = Account()
    account.add_income(100)
    assert account.balance == 100


def test_balance_cannot_be_assigned_from_outside() -> None:
    account = Account()
    with pytest.raises(AttributeError):
        account.balance = 500  # type: ignore[misc]
    assert account.balance == 0


def test_add_income_increases_balance() -> None:
    account = Account()
    account.add_income(250)
    assert account.balance == 250


def test_add_expense_decreases_balance() -> None:
    account = Account()
    account.add_income(300)
    account.add_expense(120)
    assert account.balance == 180


def test_negative_income_is_rejected() -> None:
    account = Account()
    with pytest.raises(InvalidAmountError):
        account.add_income(-50)
    assert account.balance == 0


def test_negative_expense_is_rejected() -> None:
    account = Account()
    account.add_income(100)
    with pytest.raises(InvalidAmountError):
        account.add_expense(-20)
    assert account.balance == 100


def test_overdrawing_is_blocked() -> None:
    account = Account()
    account.add_income(100)
    with pytest.raises(InsufficientFundsError):
        account.add_expense(150)
    assert account.balance == 100


def test_expense_matching_balance_is_allowed() -> None:
    account = Account()
    account.add_income(100)
    account.add_expense(100)
    assert account.balance == 0
