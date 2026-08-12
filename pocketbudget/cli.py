"""CLI: user input and command routing."""

import sys
from typing import Callable, Sequence

from pocketbudget.exceptions import (
    DataLoadError,
    InsufficientFundsError,
    InvalidAmountError,
    InvalidCategoryError,
    OverBudgetError,
)
from pocketbudget.storage import load, save

_HANDLED_ERRORS = (
    InvalidAmountError,
    InsufficientFundsError,
    InvalidCategoryError,
    OverBudgetError,
    DataLoadError,
    OSError,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Route the given command (or sys.argv) through the app lifecycle.

    Every command loads the saved state, runs the domain operation, then
    saves the result. Domain errors bubble up to this interface layer, where
    they are translated into messages a user can act on - never tracebacks.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("Hello PocketBudget")
        return 0

    handlers: dict[str, Callable[[list[str]], int]] = {
        "add-income": _add_income,
        "add-expense": _add_expense,
        "show-balance": _show_balance,
        "show-history": _show_history,
        "set-budget": _set_budget,
        "show-summary": _show_summary,
    }
    handler = handlers.get(args[0])
    if handler is None:
        print(f"Error: unknown command: {args[0]}", file=sys.stderr)
        return 1
    return handler(args[1:])


def _add_income(args: list[str]) -> int:
    if len(args) != 2:
        print("Usage: add-income <amount> <category>", file=sys.stderr)
        return 1
    try:
        account = load()
        amount = _parse_amount(args[0])
        account.add_income(amount, args[1])
        save(account)
    except _HANDLED_ERRORS as exc:
        return _report_error(exc)
    print(
        f"Income of {_format_money(amount)} recorded. "
        f"Balance: {_format_money(account.balance)}"
    )
    return 0


def _add_expense(args: list[str]) -> int:
    if len(args) != 2:
        print("Usage: add-expense <amount> <category>", file=sys.stderr)
        return 1
    try:
        account = load()
        amount = _parse_amount(args[0])
        account.add_expense(amount, args[1])
        save(account)
    except _HANDLED_ERRORS as exc:
        return _report_error(exc)
    print(
        f"Expense of {_format_money(amount)} recorded. "
        f"Balance: {_format_money(account.balance)}"
    )
    return 0


def _show_balance(args: list[str]) -> int:
    try:
        account = load()
    except _HANDLED_ERRORS as exc:
        return _report_error(exc)
    print(f"Balance: {_format_money(account.balance)}")
    return 0


def _show_history(args: list[str]) -> int:
    try:
        account = load()
    except _HANDLED_ERRORS as exc:
        return _report_error(exc)
    for kind, amount, category in account.get_transactions():
        if category:
            print(f"{kind}: {_format_money(amount)} ({category})")
        else:
            print(f"{kind}: {_format_money(amount)}")
    return 0


def _set_budget(args: list[str]) -> int:
    if len(args) != 2:
        print("Usage: set-budget <category> <limit>", file=sys.stderr)
        return 1
    try:
        account = load()
        limit = _parse_amount(args[1])
        account.set_budget(args[0], limit)
        save(account)
    except _HANDLED_ERRORS as exc:
        return _report_error(exc)
    print(f"Budget set for {args[0]}: {_format_money(limit)}")
    return 0


def _show_summary(args: list[str]) -> int:
    try:
        account = load()
    except _HANDLED_ERRORS as exc:
        return _report_error(exc)
    for category in account.budgeted_categories():
        limit = account.get_budget(category)
        remaining = account.get_remaining_budget(category)
        if limit is not None and remaining is not None:
            print(
                f"{category}: {_format_money(remaining)} remaining "
                f"of {_format_money(limit)}"
            )
    return 0


def _parse_amount(raw: str) -> float:
    try:
        return float(raw)
    except ValueError as exc:
        raise InvalidAmountError(f"{raw!r} is not a valid amount") from exc


def _report_error(exc: Exception) -> int:
    print(f"Error: {exc}", file=sys.stderr)
    return 1


def _format_money(amount: float) -> str:
    return f"${amount:.2f}"


if __name__ == "__main__":
    raise SystemExit(main())
