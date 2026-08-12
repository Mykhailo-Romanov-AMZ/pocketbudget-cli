"""Domain: budgeting rules and protected account state."""

from typing import Any

from pocketbudget.exceptions import (
    InsufficientFundsError,
    InvalidAmountError,
    InvalidCategoryError,
    OverBudgetError,
)

ALLOWED_CATEGORIES = frozenset({"Food", "Transport"})


class Account:
    """Single source of truth for the balance.

    The balance can be read from outside, but the only ways it can change are
    add_income() and add_expense(). Every transaction is validated before it
    touches the balance. Category budgets are tracked per category and checked
    against the transaction history.
    """

    def __init__(self) -> None:
        self._balance = 0.0
        self._transactions: list[Any] = []
        self._budgets: dict[str, float] = {}

    @property
    def balance(self) -> float:
        """Current balance. Read-only from outside the class."""
        return self._balance

    def get_transactions(self) -> list[Any]:
        """Return a copy of the transaction history.

        The copy means mutating the returned list can never change the
        account's own records. Entries are (kind, amount, category) tuples
        such as ("income", 500.0, None) or ("expense", 30.0, "Food").
        """
        return list(self._transactions)

    def add_income(self, amount: float) -> None:
        """Add a validated income to the balance."""
        self._validate_amount(amount)
        self._balance += amount
        self._transactions.append(("income", amount, None))

    def add_expense(self, amount: float, category: str) -> None:
        """Record a validated expense against a category.

        Blocks overdrawing (rules.md, Rule 3) and expenses that exceed the
        category's remaining budget (rules.md, Rule 4).
        """
        self._validate_amount(amount)
        self._validate_category(category)
        if amount > self._balance:
            raise InsufficientFundsError(
                f"Cannot spend {amount}: balance is only {self._balance}"
            )
        remaining = self.get_remaining_budget(category)
        if remaining is not None and amount > remaining:
            raise OverBudgetError(
                f"Expense of {amount} exceeds remaining budget of "
                f"{remaining} for {category}"
            )
        self._balance -= amount
        self._transactions.append(("expense", amount, category))

    def set_budget(self, category: str, limit: float) -> None:
        """Set the spending limit for a category."""
        self._validate_category(category)
        self._validate_amount(limit)
        self._budgets[category] = limit

    def get_budget(self, category: str) -> float | None:
        """Return the spending limit for a category, or None if unset."""
        return self._budgets.get(category)

    def get_remaining_budget(self, category: str) -> float | None:
        """Return the unused budget for a category, or None if no budget is set."""
        limit = self._budgets.get(category)
        if limit is None:
            return None
        return limit - self._spent_on(category)

    def _spent_on(self, category: str) -> float:
        spent = 0.0
        for transaction in self._transactions:
            if transaction[0] == "expense" and transaction[2] == category:
                spent += transaction[1]
        return spent

    def _validate_amount(self, amount: float) -> None:
        if amount < 0:
            raise InvalidAmountError(f"Amount must not be negative: {amount}")

    def _validate_category(self, category: str) -> None:
        if category not in ALLOWED_CATEGORIES:
            raise InvalidCategoryError(
                f"Invalid category {category!r}: only "
                f"{', '.join(sorted(ALLOWED_CATEGORIES))} are allowed"
            )
