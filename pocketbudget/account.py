"""Domain: budgeting rules and protected account state."""

from pocketbudget.exceptions import InsufficientFundsError, InvalidAmountError


class Account:
    """Single source of truth for the balance.

    The balance can be read from outside, but the only ways it can change are
    add_income() and add_expense(). Every transaction is validated before it
    touches the balance.
    """

    def __init__(self) -> None:
        self._balance = 0.0
        self._transactions: list[object] = []

    @property
    def balance(self) -> float:
        """Current balance. Read-only from outside the class."""
        return self._balance

    def get_transactions(self) -> list[object]:
        """Return a copy of the transaction history.

        The copy means mutating the returned list can never change the
        account's own records.
        """
        return list(self._transactions)

    def add_income(self, amount: float) -> None:
        """Add a validated income to the balance."""
        self._validate_amount(amount)
        self._balance += amount
        self._transactions.append(amount)

    def add_expense(self, amount: float) -> None:
        """Record a validated expense, blocking overdrawing (rules.md, Rule 3)."""
        self._validate_amount(amount)
        if amount > self._balance:
            raise InsufficientFundsError(
                f"Cannot spend {amount}: balance is only {self._balance}"
            )
        self._balance -= amount
        self._transactions.append(amount)

    def _validate_amount(self, amount: float) -> None:
        if amount < 0:
            raise InvalidAmountError(f"Amount must not be negative: {amount}")
