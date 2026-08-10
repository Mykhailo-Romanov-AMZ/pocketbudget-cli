"""Tests for saving and loading account state (storage.py).

- save() writes the account's state to a dedicated data folder (data/budget.json).
- load() rebuilds an Account whose balance and history match what was saved.
- A missing save file means a clean, empty account, not a crash.
- A corrupted file is handled with an error, never a silently wrong balance.
- Loaded data passes through the same validation as live data.
"""

import json
from pathlib import Path

import pytest

from pocketbudget.account import Account
from pocketbudget.exceptions import DataLoadError
from pocketbudget.storage import load, save


def _populated_account() -> Account:
    account = Account()
    account.add_income(500)
    account.add_expense(120)
    return account


def test_save_writes_state_to_default_data_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    account = _populated_account()

    save(account)

    save_file = tmp_path / "data" / "budget.json"
    assert save_file.exists()
    data = json.loads(save_file.read_text())
    assert data["balance"] == 380


def test_load_rebuilds_account_with_saved_balance_and_history(tmp_path: Path) -> None:
    path = tmp_path / "data" / "budget.json"
    account = _populated_account()
    save(account, path)

    loaded = load(path)

    assert loaded.balance == account.balance
    assert loaded.get_transactions() == account.get_transactions()


def test_load_with_missing_file_returns_clean_empty_account(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.json"

    loaded = load(missing)

    assert loaded.balance == 0
    assert loaded.get_transactions() == []


def test_load_with_corrupted_file_raises_data_load_error(tmp_path: Path) -> None:
    path = tmp_path / "budget.json"
    path.write_text("{ this is not valid json")

    with pytest.raises(DataLoadError):
        load(path)


def test_load_with_valid_json_but_wrong_shape_raises_data_load_error(
    tmp_path: Path,
) -> None:
    path = tmp_path / "budget.json"
    path.write_text(json.dumps({"balance": "not-a-number", "history": []}))

    with pytest.raises(DataLoadError):
        load(path)


def test_load_validates_data_like_live_data(tmp_path: Path) -> None:
    path = tmp_path / "budget.json"
    path.write_text(json.dumps({"balance": 100, "history": [["income", -50]]}))

    with pytest.raises(DataLoadError):
        load(path)


def test_load_rejects_balance_that_contradicts_history(tmp_path: Path) -> None:
    path = tmp_path / "budget.json"
    path.write_text(json.dumps({"balance": 9999, "history": [["income", 100]]}))

    with pytest.raises(DataLoadError):
        load(path)
