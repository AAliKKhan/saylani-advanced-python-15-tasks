"""
Task 06 | Banking Ledger with OOP
Classes, encapsulation, properties

Problem: Build Account and Bank classes. Support deposit, withdrawal, transfer,
and account statements. Maintain immutable transaction records containing
transaction ID, action, amount, and resulting balance.

Requirements:
  - Reject nonpositive amounts, insufficient funds, and nonexistent accounts.
  - A transfer must be atomic: both balances update or neither does.

Sample / Expected Behavior:
  Account A=1000, B=200; transfer 350 from A to B -> A=650, B=550.
"""

from typing import NamedTuple


class Transaction(NamedTuple):
    """Immutable ledger entry: id, action, amount and the balance after it."""
    txn_id: int
    action: str
    amount: float
    balance_after: float


def _validate_amount(amount):
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise TypeError(f"amount must be a number, got {amount!r}")
    if amount <= 0:
        raise ValueError(f"amount must be positive, got {amount!r}")


def _validate_balance(balance):
    if isinstance(balance, bool) or not isinstance(balance, (int, float)):
        raise TypeError(f"balance must be a number, got {balance!r}")
    if balance < 0:
        raise ValueError(f"opening balance cannot be negative, got {balance!r}")


class Account:
    """A single bank account with an append-only, immutable statement."""

    def __init__(self, account_id, owner="", opening_balance=0):
        if not isinstance(account_id, str) or not account_id.strip():
            raise ValueError("account_id must be a non-empty string")
        _validate_balance(opening_balance)

        self._account_id = account_id.strip()
        self._owner = str(owner)
        self._balance = opening_balance
        self._transactions = []
        self._local_sequence = 0

    @property
    def account_id(self):
        return self._account_id

    @property
    def owner(self):
        return self._owner

    @property
    def balance(self):
        """Read-only balance; mutation must go through deposit/withdraw."""
        return self._balance

    @property
    def transaction_count(self):
        return len(self._transactions)

    def deposit(self, amount, txn_id=None):
        _validate_amount(amount)
        self._balance += amount
        return self._record("deposit", amount, txn_id)

    def withdraw(self, amount, txn_id=None):
        _validate_amount(amount)
        if amount > self._balance:
            raise ValueError(
                f"insufficient funds in account {self._account_id!r}: "
                f"balance {self._balance}, requested {amount}")
        self._balance -= amount
        return self._record("withdrawal", amount, txn_id)

    def _record(self, action, amount, txn_id=None):
        if txn_id is None:
            self._local_sequence += 1
            txn_id = self._local_sequence
        entry = Transaction(txn_id, action, amount, self._balance)
        self._transactions.append(entry)
        return entry

    def _force_record(self, action, amount, txn_id):
        """Book an already-validated movement (used by Bank.transfer)."""
        self._balance += amount
        self._local_sequence += 1
        entry = Transaction(txn_id, action, abs(amount), self._balance)
        self._transactions.append(entry)
        return entry

    def statement(self):
        """Return an immutable copy of the transaction history."""
        return tuple(self._transactions)

    def __repr__(self):
        return (f"Account(id={self._account_id!r}, owner={self._owner!r}, "
                f"balance={self._balance})")


class Bank:
    """Holds accounts and executes atomic transfers between them."""

    def __init__(self, name="Bank"):
        self.name = name
        self._accounts = {}
        self._next_txn_id = 0

    def _next_id(self):
        self._next_txn_id += 1
        return self._next_txn_id

    def create_account(self, account_id, owner="", opening_balance=0):
        if account_id in self._accounts:
            raise ValueError(f"account already exists: {account_id!r}")
        account = Account(account_id, owner, opening_balance)
        self._accounts[account_id] = account
        return account

    def get_account(self, account_id):
        if account_id not in self._accounts:
            raise KeyError(f"unknown account: {account_id!r}")
        return self._accounts[account_id]

    def account_exists(self, account_id):
        return account_id in self._accounts

    def deposit(self, account_id, amount):
        return self.get_account(account_id).deposit(amount, self._next_id())

    def withdraw(self, account_id, amount):
        return self.get_account(account_id).withdraw(amount, self._next_id())

    def transfer(self, from_id, to_id, amount):
        """Move ``amount`` from one account to another atomically.

        Both sides are validated before either balance moves, so the ledger
        can never be left half-updated.
        """
        _validate_amount(amount)

        if from_id not in self._accounts:
            raise KeyError(f"unknown source account: {from_id!r}")
        if to_id not in self._accounts:
            raise KeyError(f"unknown destination account: {to_id!r}")
        if from_id == to_id:
            raise ValueError("cannot transfer an account to itself")

        source = self._accounts[from_id]
        target = self._accounts[to_id]

        if amount > source.balance:
            raise ValueError(
                f"insufficient funds: account {from_id!r} holds "
                f"{source.balance}, transfer requested {amount}")

        # Pre-validated: neither call below can fail, but guard anyway.
        try:
            out_txn = source._force_record("transfer_out", -amount,
                                           self._next_id())
            in_txn = target._force_record("transfer_in", amount,
                                          self._next_id())
        except Exception:
            source._balance += amount
            target._balance -= amount
            raise
        return out_txn, in_txn

    def statement(self, account_id):
        return self.get_account(account_id).statement()

    def accounts(self):
        return tuple(self._accounts.values())


if __name__ == "__main__":
    bank = Bank("Saylani")
    bank.create_account("A", "Ali", 1000)
    bank.create_account("B", "Sara", 200)

    bank.transfer("A", "B", 350)
    assert bank.get_account("A").balance == 650
    assert bank.get_account("B").balance == 550

    # Rejections
    for bad_amount in (0, -10):
        try:
            bank.deposit("A", bad_amount)
        except ValueError:
            pass
        else:
            raise AssertionError("nonpositive deposit accepted")

    try:
        bank.transfer("A", "B", 10_000)
    except ValueError:
        pass
    else:
        raise AssertionError("overdraft accepted")

    try:
        bank.transfer("A", "ZZ", 10)
    except KeyError:
        pass
    else:
        raise AssertionError("unknown account accepted")

    # Atomicity: failed transfer leaves both balances untouched
    before = (bank.get_account("A").balance, bank.get_account("B").balance)
    try:
        bank.transfer("A", "B", 99_999)
    except ValueError:
        pass
    after = (bank.get_account("A").balance, bank.get_account("B").balance)
    assert before == after

    statement = bank.statement("A")
    assert isinstance(statement, tuple)
    assert all(isinstance(t, Transaction) for t in statement)
    print("all sample cases passed")
