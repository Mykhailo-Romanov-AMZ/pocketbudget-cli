"""Custom domain exceptions."""


class InvalidAmountError(ValueError):
    """Raised when a transaction amount is not valid (e.g. negative)."""


class InsufficientFundsError(ValueError):
    """Raised when an expense exceeds the available balance (rules.md, Rule 3)."""
