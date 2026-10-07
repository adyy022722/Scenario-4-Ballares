# Campus Snack Bar POS (Scenario 4)

A desktop food ordering and point-of-sale (POS) application for a campus snack bar, built for the IT 415 Midterm Practical Examination.

## Tech stack
- **Python 3** with **Tkinter** (desktop GUI, built into Python)
- **SQLite** (`sqlite3`, built into Python) for products and saved transactions

No extra packages need to be installed.

## How to run
```
python app.py
```
The database file `snackbar_pos.db` is created automatically on first run.

To run the logic tests:
```
python test_logic.py
```

## Products
| Product | Price |
|---|---|
| Classic Burger | ₱55.00 |
| Cheeseburger | ₱65.00 |
| Ham Sandwich | ₱40.00 |
| French Fries (Regular) | ₱45.00 |
| Nachos | ₱50.00 |
| Soda (Can) | ₱25.00 |

## Screen layout
- **Sidebar** – app name and the **New Transaction** button.
- **Menu (center)** – banner and product cards with a photo, name, price, and a **+** button.
- **Order Menu (right)** – cart items, total, cash input, and the **Pay Now** button.
- **Pop-up panels** – *Payment Successful* and *Receipt* panels appear over a see-through pink "glass" backdrop after paying (press **Esc**, click the glass, or **Close** to dismiss).

## Transaction flow
1. **Browse Products** – product cards show each photo, name, and price.
2. **Add to Cart** – click **+** on a card (or the card itself); clicking again adds one more.
3. **Review Order** – the Order Menu shows each item, quantity, unit price, subtotal, and the total. Use **−** / **+** to change the quantity, or **✕ Remove**.
4. **Enter Payment** – type the cash amount in the payment field.
5. **Validate & Compute** – blank, non-numeric, negative, and insufficient amounts are rejected with a message. Change = Amount Paid − Total.
6. **Confirm Payment** – an in-app *Payment Successful* panel shows the transaction details.
7. **Receipt / New Transaction** – the *Receipt* panel shows items, quantities, subtotals, total, amount paid, change, and a transaction number (e.g. `SB-20261007-0001`). **Start New Transaction** (or **New Transaction** in the sidebar) clears the cart, payment, and receipt.

## Files
- `app.py` – the user interface
- `logic.py` – cart, totals, payment validation, change computation
- `database.py` – SQLite setup and saving transactions
- `test_logic.py` – tests for the logic
- `images/` – product photos, pre-sized for the app
