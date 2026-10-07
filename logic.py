"""
logic.py - Cart, totals, payment validation and change computation.
Kept separate from the UI so it can be tested on its own (see test_logic.py).
"""


class Cart:
    def __init__(self):
        # product_id -> {"name": str, "price": float, "qty": int}
        self.items = {}

    def add(self, product_id, name, price):
        """Add one of a product. If it's already in the cart, increase its qty."""
        if product_id in self.items:
            self.items[product_id]["qty"] += 1
        else:
            self.items[product_id] = {"name": name, "price": price, "qty": 1}

    def increase(self, product_id):
        if product_id in self.items:
            self.items[product_id]["qty"] += 1

    def decrease(self, product_id):
        """Lower the qty by 1. If it reaches 0, the item is removed."""
        if product_id in self.items:
            self.items[product_id]["qty"] -= 1
            if self.items[product_id]["qty"] <= 0:
                del self.items[product_id]

    def remove(self, product_id):
        self.items.pop(product_id, None)

    def clear(self):
        self.items.clear()

    def is_empty(self):
        return len(self.items) == 0

    def lines(self):
        """Return the cart as a list of dicts with the subtotal computed."""
        result = []
        for pid, item in self.items.items():
            result.append({
                "id": pid,
                "name": item["name"],
                "price": item["price"],
                "qty": item["qty"],
                "subtotal": round(item["price"] * item["qty"], 2),
            })
        return result

    def total(self):
        return round(sum(line["subtotal"] for line in self.lines()), 2)


def peso(amount):
    """Format a number as Philippine pesos, e.g. 1234.5 -> ₱1,234.50"""
    return f"\u20b1{amount:,.2f}"


def validate_payment(text, total):
    """
    Check the cash amount typed by the cashier.
    Returns (True, amount) if valid, or (False, error_message) if not.
    Rejects: blank, non-numeric, negative, and insufficient amounts.
    """
    text = text.strip().replace(",", "")
    if text == "":
        return False, "Please enter a valid payment amount."
    try:
        amount = float(text)
    except ValueError:
        return False, "Please enter a valid payment amount."
    # float() accepts "nan" and "inf", so reject those too
    if amount != amount or amount in (float("inf"), float("-inf")):
        return False, "Please enter a valid payment amount."
    if amount < 0:
        return False, "Please enter a valid payment amount."
    if round(amount, 2) < total:
        return False, f"Insufficient payment. Please enter at least {peso(total)}."
    return True, round(amount, 2)


def compute_change(amount_paid, total):
    """Change = Amount Paid - Total Amount"""
    return round(amount_paid - total, 2)
