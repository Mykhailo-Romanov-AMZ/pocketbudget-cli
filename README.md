# PocketBudget

A personal finance CLI for people who want to track money without a spreadsheet or a cloud subscription. Add income, record expenses, set per-category budgets, and get an instant summary of what's left — all from the terminal, with your data saved locally to `data/budget.json`.

Built with a strict test-first workflow: every rule in `rules.md` is enforced by a test before any feature ships, and the domain model is hardened so that bad input can never corrupt your ledger.

## Installation & Setup

```bash
# 1. Clone and enter the project
git clone https://github.com/Mykhailo-Romanov-AMZ/pocketbudget-cli.git
cd pocketbudget-cli

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install dependencies (pytest, ruff, mypy, pre-commit)
pip install -r requirements.txt

# 4. Install the pre-commit hooks
pre-commit install
```

## Usage

Run the CLI from the project root with `python -m pocketbudget.cli`. A bare invocation prints a greeting; every other command loads your saved state, performs the operation, and saves again.

```bash
# Record income
python -m pocketbudget.cli add-income 500 Food

# Record an expense (only the categories Food and Transport are allowed)
python -m pocketbudget.cli add-expense 25.50 Transport

# Set a monthly budget for a category
python -m pocketbudget.cli set-budget Food 100

# View your current balance
python -m pocketbudget.cli show-balance

# View the full transaction history
python -m pocketbudget.cli show-history

# View remaining budgets per category
python -m pocketbudget.cli show-summary
```

Bad input never crashes the app: an invalid amount, an unknown category, an overdraw, or an expense that exceeds a category budget all print a clear `Error:` message to stderr and exit with a non-zero status.

## Running the Tests

The full test suite lives in `tests/` and covers the domain rules, storage validation, CLI behaviour, and error handling:

```bash
python -m pytest -v
```

A passing run reports 59 tests passing. The suite is also wired into pre-commit, so every commit re-runs it along with the linters:

```bash
pre-commit run --all-files
```

This runs `ruff lint` (which enforces a McCabe complexity ceiling of 7), `ruff format`, `mypy --strict`, and `pytest`.

## Design Decisions

We decided to keep the design simple and easy to use so users can understand it without needing much guidance. The layout focuses on the most important features and avoids adding unnecessary elements that could make the interface feel cluttered. We chose consistent colours, fonts, and spacing to make the overall design look clean and professional. 
The navigation was kept straightforward so users can quickly find what they are looking for. We also made sure the design works well across different screen sizes and devices. Overall, these decisions were made to create a design that is practical, visually appealing, and easy for users to interact with.
I made the `Account` class the single source of truth for the whole application, and I deliberately made its internals impossible to reach from outside. The balance, the transaction history, and the budgets are all private, and the only way to change them is through domain methods that validate first.

**The balance is read-only.** `balance` is a property with no setter. You can read it anywhere, but you cannot assign to it. The only way money moves is through `add_income()` or `add_expense()`, so every change has to pass through validation — a negative amount, an overdraft, an unknown category, or a budget overrun is rejected before the balance is touched.

**The transaction history is copy-on-read.** `get_transactions()` builds and returns a fresh list on every call. Mutating the list you get back does nothing to the account, because it isn't the account's list — there is no way to append to or rewrite the ledger from outside.

**Budgets follow the same rule.** The budgets live in a private dict, `budgets` returns a copy, and `get_budget()` / `get_remaining_budget()` are read-only accessors. Spent amounts are never stored separately — they are derived from the history each time. The ledger stays the single source of truth, so balance, spent totals, and history can never drift out of sync.

**Validation always runs before mutation.** Every write path checks the input (amount, then category, then overdraw, then budget limit) before any state changes. A rejected operation leaves the account exactly as it was, and raises a specific exception (`InvalidAmountError`, `InsufficientFundsError`, `InvalidCategoryError`, `OverBudgetError`, `DataLoadError`) that the CLI translates into an actionable message.

**Storage replays through the domain API.** Loading a save file doesn't set attributes directly — it rebuilds the account by calling the same validated methods the user would call. Corrupted, negative, or over-drafted save data is rejected the same way live input is, so a half-validated account never escapes `load()`.
