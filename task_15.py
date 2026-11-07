"""
Task 15 | Integrated Order Fulfillment System
OOP, composition, files, exceptions, algorithms

Problem: Design Product, Cart, Order, and Inventory classes. Read a product
catalog from JSON, build carts, apply percentage discounts, compute totals,
and place orders with stock updates. Persist orders to JSON.

Requirements:
  - Reject invalid quantities and out-of-stock purchases.
  - Validate all items before changing inventory; roll back if order
    persistence fails.
  - Generate unique order IDs.
  - Include at least three unit tests using unittest.

Sample / Expected Behavior:
  Catalog: P1 price=100 stock=5; cart P1 x2 with 10% discount -> total 180,
  stock becomes 3 after successful order.
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone


class ProductError(ValueError):
    """Raised for invalid product data or quantities."""


class StockError(ProductError):
    """Raised when an order asks for more stock than is available."""


class Product:
    """A single catalog item with a mutable stock level."""

    def __init__(self, sku, name, price, stock):
        if not isinstance(sku, str) or not sku.strip():
            raise ProductError("sku must be a non-empty string")
        if not isinstance(name, str) or not name.strip():
            raise ProductError("name must be a non-empty string")
        if isinstance(price, bool) or not isinstance(price, (int, float)):
            raise ProductError(f"price must be a number for {sku}")
        if price < 0:
            raise ProductError(f"price cannot be negative for {sku}")
        if isinstance(stock, bool) or not isinstance(stock, int):
            raise ProductError(f"stock must be an integer for {sku}")
        if stock < 0:
            raise ProductError(f"stock cannot be negative for {sku}")

        self.sku = sku.strip()
        self.name = name.strip()
        self.price = float(price)
        self.stock = stock

    def as_dict(self):
        return {"sku": self.sku, "name": self.name,
                "price": self.price, "stock": self.stock}

    def __repr__(self):
        return (f"Product({self.sku!r}, price={self.price}, "
                f"stock={self.stock})")


class Inventory:
    """Collection of products keyed by SKU, loadable from JSON."""

    def __init__(self, products=None):
        self._products = {}
        for product in products or []:
            self.add(product)

    @classmethod
    def from_json(cls, path):
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            data = data.get("products", [])
        if not isinstance(data, list):
            raise ProductError("catalog JSON must be a list of products")
        inventory = cls()
        for entry in data:
            if not isinstance(entry, dict):
                raise ProductError("each catalog entry must be an object")
            inventory.add(Product(
                entry.get("sku", ""),
                entry.get("name", ""),
                entry.get("price", -1),
                entry.get("stock", -1),
            ))
        return inventory

    def add(self, product):
        if not isinstance(product, Product):
            raise TypeError("only Product instances can be added")
        if product.sku in self._products:
            raise ProductError(f"duplicate sku: {product.sku!r}")
        self._products[product.sku] = product
        return product

    def get(self, sku):
        if sku not in self._products:
            raise KeyError(f"unknown sku: {sku!r}")
        return self._products[sku]

    def __contains__(self, sku):
        return sku in self._products

    def products(self):
        return tuple(self._products[sku] for sku in sorted(self._products))

    def snapshot(self):
        return {sku: p.stock for sku, p in self._products.items()}

    def restore(self, snapshot):
        for sku, stock in snapshot.items():
            if sku in self._products:
                self._products[sku].stock = stock

    def deduct(self, sku, quantity):
        product = self.get(sku)
        if quantity > product.stock:
            raise StockError(
                f"out of stock: {sku} has {product.stock}, "
                f"requested {quantity}")
        product.stock -= quantity

    def restock(self, sku, quantity):
        self.get(sku).stock += quantity

    def save_json(self, path):
        payload = [p.as_dict() for p in self.products()]
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)


class Cart:
    """A shopping cart bound to an inventory; validates quantities only."""

    def __init__(self, inventory):
        if not isinstance(inventory, Inventory):
            raise TypeError("cart needs an Inventory")
        self._inventory = inventory
        self._lines = {}          # sku -> quantity

    @property
    def inventory(self):
        return self._inventory

    def add(self, sku, quantity):
        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise ProductError(f"quantity must be an integer, "
                               f"got {quantity!r}")
        if quantity <= 0:
            raise ProductError(f"quantity must be positive, got {quantity}")
        self._inventory.get(sku)          # raises KeyError for unknown sku
        self._lines[sku] = self._lines.get(sku, 0) + quantity
        return self

    def remove(self, sku):
        self._lines.pop(sku, None)
        return self

    def clear(self):
        self._lines.clear()
        return self

    @property
    def lines(self):
        """Immutable view of {sku: quantity}."""
        return dict(self._lines)

    def subtotal(self):
        total = 0.0
        for sku, quantity in self._lines.items():
            total += self._inventory.get(sku).price * quantity
        return round(total, 2)

    def total(self, discount_percent=0):
        return apply_discount(self.subtotal(), discount_percent)

    def is_empty(self):
        return not self._lines


def apply_discount(amount, discount_percent):
    """Apply a percentage discount; validates the percentage range."""
    if isinstance(discount_percent, bool) \
            or not isinstance(discount_percent, (int, float)):
        raise ProductError("discount must be a number")
    if not 0 <= discount_percent < 100:
        raise ProductError("discount must be in [0, 100)")
    if amount < 0:
        raise ProductError("amount cannot be negative")
    return round(amount * (1 - discount_percent / 100.0), 2)


class Order:
    """Immutable record of a placed order."""

    def __init__(self, order_id, lines, subtotal, discount_percent, total,
                 placed_at=None):
        self.order_id = order_id
        self.lines = dict(lines)              # sku -> quantity
        self.subtotal = round(float(subtotal), 2)
        self.discount_percent = float(discount_percent)
        self.total = round(float(total), 2)
        self.placed_at = placed_at or datetime.now(timezone.utc).isoformat()

    def as_dict(self):
        return {
            "order_id": self.order_id,
            "lines": self.lines,
            "subtotal": self.subtotal,
            "discount_percent": self.discount_percent,
            "total": self.total,
            "placed_at": self.placed_at,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data["order_id"], data.get("lines", {}),
                   data.get("subtotal", 0), data.get("discount_percent", 0),
                   data.get("total", 0), data.get("placed_at"))

    def __repr__(self):
        return f"Order({self.order_id!r}, total={self.total})"


class OrderManager:
    """Places carts as orders, updating stock and persisting to JSON."""

    def __init__(self, inventory, orders_path="orders.json"):
        if not isinstance(inventory, Inventory):
            raise TypeError("manager needs an Inventory")
        self.inventory = inventory
        self.orders_path = orders_path

    def load_orders(self):
        if not os.path.exists(self.orders_path):
            return []
        with open(self.orders_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, list):
            raise ProductError("orders file must contain a JSON list")
        return [Order.from_dict(entry) for entry in data]

    def _save_orders(self, orders):
        directory = os.path.dirname(os.path.abspath(self.orders_path))
        temp_path = os.path.join(directory,
                                 f".{os.path.basename(self.orders_path)}.tmp")
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump([o.as_dict() for o in orders], handle, indent=2)
            handle.write("\n")
        os.replace(temp_path, self.orders_path)

    def _next_order_id(self):
        used = {order.order_id for order in self.load_orders()}
        index = 1
        while f"ORD-{index:05d}" in used:
            index += 1
        return f"ORD-{index:05d}"

    def place_order(self, cart, discount_percent=0):
        """Validate the whole cart, deduct stock, then persist the order.

        Nothing is written to inventory until every line has been checked,
        and if persistence fails the stock deduction is rolled back before
        the error is re-raised.
        """
        if not isinstance(cart, Cart):
            raise TypeError("place_order expects a Cart")
        if cart.inventory is not self.inventory:
            raise ProductError("cart belongs to a different inventory")
        if cart.is_empty():
            raise ProductError("cannot place an order with an empty cart")

        lines = cart.lines
        subtotal = cart.subtotal()
        total = apply_discount(subtotal, discount_percent)

        # 1. Validate every line first - no stock changes yet.
        for sku, quantity in lines.items():
            product = self.inventory.get(sku)
            if product.stock < quantity:
                raise StockError(
                    f"out of stock: {sku} has {product.stock}, "
                    f"requested {quantity}")

        # 2. Deduct stock for all lines.
        for sku, quantity in lines.items():
            self.inventory.deduct(sku, quantity)

        # 3. Persist; roll the stock back if that fails.
        order = Order(self._next_order_id(), lines, subtotal,
                      discount_percent, total)
        try:
            existing = self.load_orders()
            self._save_orders(existing + [order])
        except Exception:
            for sku, quantity in lines.items():
                self.inventory.restock(sku, quantity)
            raise RuntimeError(
                f"could not persist order {order.order_id}; "
                f"inventory rolled back") from None

        return order


def write_sample_catalog(path, products=None):
    """Generate the sample catalog JSON used by this task."""
    payload = products if products is not None else [
        {"sku": "P1", "name": "Notebook", "price": 100, "stock": 5},
        {"sku": "P2", "name": "Pen", "price": 25, "stock": 20},
        {"sku": "P3", "name": "Bag", "price": 450, "stock": 2},
    ]
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return path


class TestOrderFulfillment(unittest.TestCase):
    """Unit tests covering the sample behaviour and the edge cases."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.catalog = os.path.join(self.folder.name, "catalog.json")
        self.orders = os.path.join(self.folder.name, "orders.json")
        write_sample_catalog(self.catalog, [
            {"sku": "P1", "name": "Notebook", "price": 100, "stock": 5},
        ])
        self.inventory = Inventory.from_json(self.catalog)
        self.manager = OrderManager(self.inventory, self.orders)

    def test_discounted_total_and_stock_update(self):
        """Sample: P1 x2 at 10% off -> total 180, stock 5 -> 3."""
        cart = Cart(self.inventory).add("P1", 2)
        self.assertEqual(cart.subtotal(), 200)
        self.assertEqual(cart.total(10), 180)

        order = self.manager.place_order(cart, discount_percent=10)
        self.assertEqual(order.total, 180)
        self.assertEqual(self.inventory.get("P1").stock, 3)
        self.assertEqual(len(self.manager.load_orders()), 1)

    def test_rejects_out_of_stock_without_changing_inventory(self):
        before = self.inventory.snapshot()
        cart = Cart(self.inventory).add("P1", 6)
        with self.assertRaises(StockError):
            self.manager.place_order(cart)
        self.assertEqual(self.inventory.snapshot(), before)
        self.assertEqual(self.manager.load_orders(), [])

    def test_rejects_invalid_quantities(self):
        cart = Cart(self.inventory)
        for bad in (0, -3, 2.5, "2", True):
            with self.assertRaises(ProductError):
                cart.add("P1", bad)
        with self.assertRaises(KeyError):
            cart.add("MISSING", 1)
        self.assertEqual(self.inventory.get("P1").stock, 5)

    def test_rollback_when_persistence_fails(self):
        """A broken orders path must not leave stock deducted."""
        broken = os.path.join(self.folder.name, "no_such_dir", "orders.json")
        manager = OrderManager(self.inventory, broken)
        before = self.inventory.snapshot()
        cart = Cart(self.inventory).add("P1", 2)
        with self.assertRaises(RuntimeError):
            manager.place_order(cart)
        self.assertEqual(self.inventory.snapshot(), before)
        self.assertEqual(self.inventory.get("P1").stock, 5)

    def test_unique_order_ids_and_discount_validation(self):
        first = self.manager.place_order(Cart(self.inventory).add("P1", 1))
        second = self.manager.place_order(Cart(self.inventory).add("P1", 1))
        self.assertNotEqual(first.order_id, second.order_id)
        with self.assertRaises(ProductError):
            apply_discount(100, 150)
        with self.assertRaises(ProductError):
            apply_discount(100, -1)


def run_demo():
    """Interactive demo of the sample scenario from the task sheet."""
    folder = tempfile.mkdtemp(prefix="fulfilment-")
    catalog = os.path.join(folder, "catalog.json")
    write_sample_catalog(catalog)
    inventory = Inventory.from_json(catalog)
    manager = OrderManager(inventory, os.path.join(folder, "orders.json"))

    cart = Cart(inventory).add("P1", 2)
    print(f"subtotal: {cart.subtotal()}  total with 10% off: {cart.total(10)}")
    order = manager.place_order(cart, discount_percent=10)
    print(f"placed {order.order_id}: {order.as_dict()}")
    print(f"P1 stock now: {inventory.get('P1').stock}")
    print(f"orders file: {manager.orders_path}")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        run_demo()
    else:
        unittest.main()
