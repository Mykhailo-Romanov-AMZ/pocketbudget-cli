"""Custom domain exceptions."""


class InvalidAmountError(ValueError):
    """Raised when a transaction amount is not valid (e.g. negative)."""


class InsufficientFundsError(ValueError):
    """Raised when an expense exceeds the available balance (rules.md, Rule 3)."""


class InvalidCategoryError(ValueError):
    """Raised when a category is not one of the allowed ones (rules.md, Rule 2)."""


class OverBudgetError(ValueError):
    """Raised when an expense exceeds a category's remaining budget (Rule 4)."""


class DataLoadError(Exception):
    """Raised when a save file is missing, corrupted, or fails validation."""
