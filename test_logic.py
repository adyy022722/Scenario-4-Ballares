"""
test_logic.py - Quick checks for the cart and payment logic.
Run with:  python test_logic.py
"""
from logic import Cart, validate_payment, compute_change


def test_cart_totals():
    cart = Cart()
    cart.add(1, "Classic Burger", 55.00)
    cart.add(1, "Classic Burger", 55.00)    # adding again increases qty
    cart.add(4, "French Fries (Regular)", 45.00)
    cart.add(6, "Soda (Can)", 25.00)
    assert cart.items[1]["qty"] == 2
    assert cart.total() == 180.00           # 110 + 45 + 25


def test_increase_decrease_remove():
    cart = Cart()
    cart.add(2, "Cheeseburger", 65.00)
    cart.increase(2)
    assert cart.items[2]["qty"] == 2
    cart.decrease(2)
    cart.decrease(2)                        # qty hits 0, item removed
    assert cart.is_empty()
    cart.add(5, "Nachos", 50.00)
    cart.remove(5)
    assert cart.is_empty()


def test_validation():
    total = 180.00
    assert validate_payment("", total) == (False, "Please enter a valid payment amount.")
    assert validate_payment("abc", total)[0] is False
    assert validate_payment("-50", total)[0] is False
    assert validate_payment("nan", total)[0] is False
    ok, msg = validate_payment("100", total)
    assert ok is False and msg == "Insufficient payment. Please enter at least \u20b1180.00."
    assert validate_payment("180", total) == (True, 180.00)
    assert validate_payment("200", total) == (True, 200.00)


def test_change():
    assert compute_change(200.00, 180.00) == 20.00
    assert compute_change(180.00, 180.00) == 0.00


if __name__ == "__main__":
    test_cart_totals()
    test_increase_decrease_remove()
    test_validation()
    test_change()
    print("All tests passed.")
