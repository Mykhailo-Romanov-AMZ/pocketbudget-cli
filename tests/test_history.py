"""Tests for protected transaction history.

The account's history must be readable but not mutable from outside:
mutating the list returned by get_transactions() must never change the
account's own records.
"""

from pocketbudget.account import Account


def test_get_transactions_returns_a_new_list_each_time() -> None:
    account = Account()
    account.add_income(100)
    account.add_expense(30, "Food")

    first = account.get_transactions()
    second = account.get_transactions()

    assert first is not second
    assert first == second


def test_mutating_returned_history_does_not_change_account() -> None:
    account = Account()
    account.add_income(100)
    account.add_expense(30, "Food")

    pristine = account.get_transactions()
    original_count = len(pristine)

    tampered = account.get_transactions()
    tampered.append("fake_transaction")
    tampered.clear()

    current = account.get_transactions()
    assert current == pristine
    assert len(current) == original_count


def test_mutating_returned_budgets_does_not_change_account() -> None:
    account = Account()
    account.set_budget("Food", 200)

    budgets = account.budgets
    budgets["Food"] = 9999
    budgets["Transport"] = 123

    assert account.get_budget("Food") == 200
    assert account.get_budget("Transport") is None
