"""
Task 01 | Nested Transaction Analyzer
Data structures, sorting, comprehensions

Problem: Given a list of transaction dictionaries with keys id, customer, category,
amount, and status, produce a report containing each customer's successful spending,
top category, and rank by spending. Ignore failed transactions and reject duplicate
transaction IDs.

Requirements:
  - Return a list sorted by spending descending, then customer name ascending.
  - Customers with no successful transactions must appear with total 0.
  - Do not use pandas.

Sample / Expected Behavior:
  Input: [{id:1, customer:"Ali", category:"Food", amount:500, status:"success"},
          {id:2, customer:"Ali", category:"Travel", amount:200, status:"failed"},
          {id:3, customer:"Sara", category:"Food", amount:700, status:"success"}]
  ->  Output totals: Sara=700, Ali=500.
"""

from collections import defaultdict

REQUIRED_KEYS = ("id", "customer", "category", "amount", "status")
VALID_STATUSES = ("success", "failed")


def _validate_transaction(transaction, index):
    """Validate one raw transaction record and return normalized values."""
    if not isinstance(transaction, dict):
        raise TypeError(f"transaction at index {index} must be a dict, "
                        f"got {type(transaction).__name__}")

    missing = [key for key in REQUIRED_KEYS if key not in transaction]
    if missing:
        raise ValueError(f"transaction at index {index} is missing keys: {missing}")

    status = transaction["status"]
    if not isinstance(status, str) or status.strip().lower() not in VALID_STATUSES:
        raise ValueError(f"transaction at index {index} has invalid status "
                         f"{status!r}; expected one of {VALID_STATUSES}")

    customer = transaction["customer"]
    category = transaction["category"]
    if not isinstance(customer, str) or not customer.strip():
        raise ValueError(f"transaction at index {index} has an empty customer name")
    if not isinstance(category, str) or not category.strip():
        raise ValueError(f"transaction at index {index} has an empty category")

    amount = transaction["amount"]
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise TypeError(f"transaction at index {index} has a non-numeric amount "
                        f"{amount!r}")
    if amount < 0:
        raise ValueError(f"transaction at index {index} has a negative amount "
                         f"{amount!r}")

    return (transaction["id"], customer.strip(), category.strip(),
            amount, status.strip().lower())


def analyze_transactions(transactions):
    """Build a ranked spending report from a list of transaction dicts.

    Returns a list of dictionaries with keys:
      customer, total, top_category, rank

    Ordering: total descending, then customer name ascending.
    Duplicate transaction IDs raise ValueError.
    """
    if transactions is None:
        raise TypeError("transactions must be a list of dictionaries")
    if not isinstance(transactions, list):
        raise TypeError("transactions must be a list of dictionaries")

    seen_ids = set()
    totals = defaultdict(int)
    category_totals = defaultdict(lambda: defaultdict(int))
    customers = []

    for index, raw in enumerate(transactions):
        tx_id, customer, category, amount, status = _validate_transaction(raw, index)

        if tx_id in seen_ids:
            raise ValueError(f"duplicate transaction id: {tx_id!r}")
        seen_ids.add(tx_id)

        if customer not in totals:
            customers.append(customer)
            totals[customer] = 0
            category_totals[customer] = defaultdict(int)

        if status == "success":
            totals[customer] += amount
            category_totals[customer][category] += amount

    def top_category(customer):
        per_category = category_totals[customer]
        if not per_category:
            return None
        # Highest spend first; alphabetical order breaks ties deterministically.
        return min(per_category.items(), key=lambda kv: (-kv[1], kv[0]))[0]

    ranked = sorted(customers, key=lambda name: (-totals[name], name))

    report = []
    for position, customer in enumerate(ranked, start=1):
        report.append({
            "customer": customer,
            "total": totals[customer],
            "top_category": top_category(customer),
            "rank": position,
        })
    return report


def format_report(report):
    """Render the report as readable lines (one per customer)."""
    lines = []
    for row in report:
        category = row["top_category"] if row["top_category"] else "-"
        lines.append(f'{row["rank"]}. {row["customer"]}: total={row["total"]}, '
                     f'top_category={category}')
    return lines


SAMPLE_TRANSACTIONS = [
    {"id": 1, "customer": "Ali", "category": "Food", "amount": 500,
     "status": "success"},
    {"id": 2, "customer": "Ali", "category": "Travel", "amount": 200,
     "status": "failed"},
    {"id": 3, "customer": "Sara", "category": "Food", "amount": 700,
     "status": "success"},
    {"id": 4, "customer": "Hina", "category": "Bills", "amount": 150,
     "status": "failed"},
]


if __name__ == "__main__":
    result = analyze_transactions(SAMPLE_TRANSACTIONS)
    print("\n".join(format_report(result)))
    expected = {"Sara": 700, "Ali": 500, "Hina": 0}
    assert {row["customer"]: row["total"] for row in result} == expected
    assert [row["customer"] for row in result] == ["Sara", "Ali", "Hina"]
