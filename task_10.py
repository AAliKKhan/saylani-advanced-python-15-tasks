"""
Task 10 | CSV Inventory Reconciliation
CSV, file handling, validation

Problem: Read inventory.csv (sku, name, quantity) and movements.csv
(sku, type, units). Apply IN and OUT movements in order, then write
updated_inventory.csv and rejected_movements.csv.

Requirements:
  - Reject unknown SKUs, negative or zero units, invalid movement types, and
    any OUT causing negative stock.
  - Continue processing after rejected rows.

Sample / Expected Behavior:
  SKU P01 starts at 10; OUT 4, OUT 9, IN 2 -> final 8; second movement
  rejected.
"""

import csv
import os

INVENTORY_HEADER = ("sku", "name", "quantity")
MOVEMENTS_HEADER = ("sku", "type", "units")
REJECT_HEADER = ("sku", "type", "units", "reason")

MOVEMENT_TYPES = ("IN", "OUT")


def _to_int(text, field, row_number):
    try:
        value = int(str(text).strip())
    except (TypeError, ValueError):
        raise ValueError(f"row {row_number}: {field} must be an integer, "
                         f"got {text!r}")
    return value


def load_inventory(path):
    """Return {sku: {'name': str, 'quantity': int}} from inventory.csv."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"inventory file not found: {path}")

    inventory = {}
    with open(path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("inventory.csv is empty")
        missing = [c for c in INVENTORY_HEADER if c not in reader.fieldnames]
        if missing:
            raise ValueError(f"inventory.csv missing columns: {missing}")

        for row_number, row in enumerate(reader, start=2):
            sku = (row.get("sku") or "").strip()
            name = (row.get("name") or "").strip()
            if not sku:
                raise ValueError(f"row {row_number}: sku cannot be empty")
            if not name:
                raise ValueError(f"row {row_number}: name cannot be empty")
            if sku in inventory:
                raise ValueError(f"row {row_number}: duplicate sku {sku!r}")
            quantity = _to_int(row.get("quantity"), "quantity", row_number)
            if quantity < 0:
                raise ValueError(f"row {row_number}: quantity cannot be "
                                 f"negative ({quantity})")
            inventory[sku] = {"name": name, "quantity": quantity}
    return inventory


def load_movements(path):
    """Return the raw movement rows as a list of dicts (order preserved)."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"movements file not found: {path}")

    movements = []
    with open(path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("movements.csv is empty")
        missing = [c for c in MOVEMENTS_HEADER if c not in reader.fieldnames]
        if missing:
            raise ValueError(f"movements.csv missing columns: {missing}")
        for row in reader:
            movements.append({
                "sku": (row.get("sku") or "").strip(),
                "type": (row.get("type") or "").strip(),
                "units": (row.get("units") or "").strip(),
            })
    return movements


def apply_movements(inventory, movements):
    """Apply movements in order.

    Returns (inventory, rejected) where rejected is a list of
    {'sku','type','units','reason'} dicts. The inventory dict is updated in
    place; rejected rows never change stock.
    """
    rejected = []

    for index, row in enumerate(movements, start=2):
        sku = row["sku"]
        move_type = row["type"].upper()
        raw_units = row["units"]

        try:
            units = _to_int(raw_units, "units", index)
        except ValueError as exc:
            rejected.append({**row, "type": row["type"], "reason": str(exc)})
            continue

        if move_type not in MOVEMENT_TYPES:
            rejected.append({**row, "type": row["type"],
                             "reason": f"invalid movement type "
                                       f"{row['type']!r}"})
            continue
        if units <= 0:
            rejected.append({**row, "type": row["type"],
                             "reason": "units must be a positive integer"})
            continue
        if sku not in inventory:
            rejected.append({**row, "type": row["type"],
                             "reason": f"unknown sku {sku!r}"})
            continue

        current = inventory[sku]["quantity"]
        if move_type == "OUT" and units > current:
            rejected.append({**row, "type": row["type"],
                             "reason": f"insufficient stock: have {current}, "
                                       f"requested {units}"})
            continue

        inventory[sku]["quantity"] = current + units if move_type == "IN" \
            else current - units

    return inventory, rejected


def write_updated_inventory(path, inventory):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(INVENTORY_HEADER)
        for sku in sorted(inventory):
            item = inventory[sku]
            writer.writerow([sku, item["name"], item["quantity"]])


def write_rejected_movements(path, rejected):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REJECT_HEADER)
        writer.writeheader()
        for row in rejected:
            writer.writerow({
                "sku": row["sku"],
                "type": row["type"],
                "units": row["units"],
                "reason": row["reason"],
            })


def reconcile(inventory_path, movements_path, updated_path, rejected_path):
    """Full pipeline: read, apply, write both output files.

    Returns (inventory, rejected).
    """
    inventory = load_inventory(inventory_path)
    movements = load_movements(movements_path)
    inventory, rejected = apply_movements(inventory, movements)
    write_updated_inventory(updated_path, inventory)
    write_rejected_movements(rejected_path, rejected)
    return inventory, rejected


def write_sample_data(inventory_path, movements_path):
    """Generate the sample CSV files used by this task."""
    with open(inventory_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(INVENTORY_HEADER)
        writer.writerow(["P01", "Widget", 10])
        writer.writerow(["P02", "Gadget", 5])

    with open(movements_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(MOVEMENTS_HEADER)
        writer.writerow(["P01", "OUT", 4])    # accepted -> 6
        writer.writerow(["P01", "OUT", 9])    # rejected: would go negative
        writer.writerow(["P01", "IN", 2])     # accepted -> 8
        writer.writerow(["P99", "IN", 3])     # rejected: unknown sku
        writer.writerow(["P02", "OUT", 0])    # rejected: zero units
        writer.writerow(["P02", "IN", -2])    # rejected: negative units
        writer.writerow(["P02", "MOVE", 1])   # rejected: bad type
        writer.writerow(["P02", "OUT", 99])   # rejected: insufficient stock
        writer.writerow(["P02", "IN", 1])     # accepted -> 6
    return inventory_path, movements_path


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as folder:
        inventory_csv = os.path.join(folder, "inventory.csv")
        movements_csv = os.path.join(folder, "movements.csv")
        updated_csv = os.path.join(folder, "updated_inventory.csv")
        rejected_csv = os.path.join(folder, "rejected_movements.csv")

        write_sample_data(inventory_csv, movements_csv)
        inventory, rejected = reconcile(inventory_csv, movements_csv,
                                        updated_csv, rejected_csv)

        assert inventory["P01"]["quantity"] == 8, inventory
        assert inventory["P02"]["quantity"] == 6, inventory
        assert len(rejected) == 6, rejected

        with open(updated_csv, encoding="utf-8") as handle:
            content = handle.read()
        assert "P01,Widget,8" in content
        with open(rejected_csv, encoding="utf-8") as handle:
            lines = handle.read().strip().splitlines()
        assert len(lines) == 7  # header + 6 rejected rows

    print("all sample cases passed")
