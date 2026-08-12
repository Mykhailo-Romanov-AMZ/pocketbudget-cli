"""Storage: saving and loading application state."""

import json
from pathlib import Path
from typing import Any

from pocketbudget.account import KIND_EXPENSE, KIND_INCOME, Account
from pocketbudget.exceptions import (
    DataLoadError,
    InsufficientFundsError,
    InvalidAmountError,
    InvalidCategoryError,
    OverBudgetError,
)

DEFAULT_PATH = Path("data") / "budget.json"


def save(account: Account, path: str | Path | None = None) -> None:
    """Write the account's balance and history to a JSON file.

    The default location is the dedicated data folder (data/budget.json).
    """
    save_path = Path(path) if path is not None else DEFAULT_PATH
    data = {
        "balance": account.balance,
        "history": [list(transaction) for transaction in account.get_transactions()],
        "budgets": account.budgets,
    }
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_text(json.dumps(data, indent=2))


def load(path: str | Path | None = None) -> Account:
    """Rebuild an Account from a saved file.

    A missing file yields a clean, empty account. A corrupted or invalid
    file raises DataLoadError instead of silently producing a wrong balance.
    """
    load_path = Path(path) if path is not None else DEFAULT_PATH
    if not load_path.exists():
        return Account()

    data = _read_save_data(load_path)
    account = Account()
    _replay_history(account, data.get("history"), load_path)
    _check_balance(data.get("balance"), account, load_path)
    _restore_budgets(account, data.get("budgets"), load_path)
    return account


def _read_save_data(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text()
    except OSError as exc:
        raise DataLoadError(f"Could not read {path}: {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DataLoadError(f"Corrupted save file {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise DataLoadError(f"Save file {path} must contain a JSON object")
    return data


def _replay_history(account: Account, history: Any, path: Path) -> None:
    if not isinstance(history, list):
        raise DataLoadError(f"Save file {path} has no valid history list")

    for entry in history:
        _apply_entry(account, entry, path)


def _apply_entry(account: Account, entry: Any, path: Path) -> None:
    if not isinstance(entry, list) or len(entry) != 3:
        raise DataLoadError(f"Invalid transaction entry in {path}: {entry}")
    kind, amount, category = entry
    if kind not in (KIND_INCOME, KIND_EXPENSE):
        raise DataLoadError(f"Unknown transaction kind in {path}: {kind}")
    if not isinstance(amount, (int, float)) or isinstance(amount, bool):
        raise DataLoadError(f"Invalid transaction amount in {path}: {amount}")
    try:
        if kind == KIND_INCOME:
            account.add_income(float(amount), category)
        else:
            account.add_expense(float(amount), category)
    except (InvalidAmountError, InsufficientFundsError) as exc:
        raise DataLoadError(
            f"Save file {path} contains an invalid transaction: {exc}"
        ) from exc
    except (InvalidCategoryError, OverBudgetError) as exc:
        raise DataLoadError(
            f"Save file {path} contains an invalid transaction: {exc}"
        ) from exc


def _check_balance(balance: Any, account: Account, path: Path) -> None:
    if not isinstance(balance, (int, float)) or isinstance(balance, bool):
        raise DataLoadError(f"Save file {path} has an invalid balance")
    if balance != account.balance:
        raise DataLoadError(f"Balance in {path} does not match its transaction history")


def _restore_budgets(account: Account, budgets: Any, path: Path) -> None:
    if budgets is None:
        return
    if not isinstance(budgets, dict):
        raise DataLoadError(f"Save file {path} has an invalid budgets map")
    for category, limit in budgets.items():
        if not isinstance(limit, (int, float)) or isinstance(limit, bool):
            raise DataLoadError(f"Invalid budget limit in {path}: {limit}")
        try:
            account.set_budget(category, float(limit))
        except ValueError as exc:
            raise DataLoadError(
                f"Save file {path} contains an invalid budget: {exc}"
            ) from exc
