"""
database.py - SQLite storage for the Campus Snack Bar POS.

Tables:
  products           - the hard-coded snack bar menu (seeded on first run)
  transactions       - one row per completed payment
  transaction_items  - the items that belonged to each transaction
"""
import sqlite3
from datetime import datetime

DB_FILE = "snackbar_pos.db"

# Scenario 4 product list (prices in Philippine pesos)
DEFAULT_PRODUCTS = [
    ("Classic Burger", 55.00),
    ("Cheeseburger", 65.00),
    ("Ham Sandwich", 40.00),
    ("French Fries (Regular)", 45.00),
    ("Nachos", 50.00),
    ("Soda (Can)", 25.00),
]


def get_connection():
    return sqlite3.connect(DB_FILE)


def init_db():
    """Create the tables if they don't exist and seed the products once."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            reference   TEXT NOT NULL,
            total       REAL NOT NULL,
            amount_paid REAL NOT NULL,
            change      REAL NOT NULL,
            created_at  TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transaction_items (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            product_name   TEXT NOT NULL,
            unit_price     REAL NOT NULL,
            quantity       INTEGER NOT NULL,
            subtotal       REAL NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES transactions(id)
        )
    """)

    # Seed products only if the table is empty
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO products (name, price) VALUES (?, ?)",
                        DEFAULT_PRODUCTS)
    conn.commit()
    conn.close()


def get_products():
    """Return a list of (id, name, price) tuples."""
    conn = get_connection()
    rows = conn.execute("SELECT id, name, price FROM products ORDER BY id").fetchall()
    conn.close()
    return rows


def save_transaction(cart_lines, total, amount_paid, change):
    """
    Save a completed transaction and its items.
    cart_lines: list of dicts with keys name, price, qty, subtotal
    Returns (reference, timestamp).
    """
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO transactions (reference, total, amount_paid, change, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        ("PENDING", total, amount_paid, change, timestamp),
    )
    txn_id = cur.lastrowid
    # Reference format: SB-YYYYMMDD-0001 (SB = Snack Bar)
    reference = f"SB-{now.strftime('%Y%m%d')}-{txn_id:04d}"
    cur.execute("UPDATE transactions SET reference = ? WHERE id = ?", (reference, txn_id))

    for line in cart_lines:
        cur.execute(
            "INSERT INTO transaction_items "
            "(transaction_id, product_name, unit_price, quantity, subtotal) "
            "VALUES (?, ?, ?, ?, ?)",
            (txn_id, line["name"], line["price"], line["qty"], line["subtotal"]),
        )
    conn.commit()
    conn.close()
    return reference, timestamp
