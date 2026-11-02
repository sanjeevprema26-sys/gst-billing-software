from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "gst_billing.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            gstin TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            hsn TEXT,
            rate REAL NOT NULL,
            gst_rate REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT UNIQUE NOT NULL,
            customer_id INTEGER NOT NULL,
            invoice_date TEXT NOT NULL,
            subtotal REAL NOT NULL,
            gst_total REAL NOT NULL,
            grand_total REAL NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            rate REAL NOT NULL,
            gst_rate REAL NOT NULL,
            taxable_amount REAL NOT NULL,
            gst_amount REAL NOT NULL,
            total_amount REAL NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
        """
    )
    conn.commit()
    conn.close()


def seed_demo_data():
    conn = get_db_connection()
    customer_count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    product_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]

    if customer_count == 0:
        conn.execute(
            "INSERT INTO customers (name, phone, gstin, address) VALUES (?, ?, ?, ?)",
            ("Aarav Traders", "9876543210", "27ABCDE1234F1Z5", "Pune, Maharashtra"),
        )

    if product_count == 0:
        conn.executemany(
            "INSERT INTO products (name, hsn, rate, gst_rate) VALUES (?, ?, ?, ?)",
            [
                ("Laptop Stand", "8473", 1200, 18),
                ("Office Chair", "9403", 3500, 18),
                ("Printer Paper", "4823", 240, 5),
                ("USB Cable", "8544", 160, 18),
            ],
        )

    conn.commit()
    conn.close()


def generate_invoice_number():
    now = datetime.now()
    return f"INV-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}"


@app.route("/")
def index():
    conn = get_db_connection()
    customers = conn.execute("SELECT * FROM customers ORDER BY id DESC").fetchall()
    products = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    invoices = conn.execute(
        """
        SELECT i.*, c.name AS customer_name
        FROM invoices i
        JOIN customers c ON c.id = i.customer_id
        ORDER BY i.id DESC
        LIMIT 10
        """
    ).fetchall()
    conn.close()

    total_sales = 0
    for invoice in invoices:
        total_sales += invoice["grand_total"]

    return render_template(
        "index.html",
        customers=customers,
        products=products,
        invoices=invoices,
        total_sales=total_sales,
    )


@app.route("/customer", methods=["POST"])
def add_customer():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    gstin = request.form.get("gstin", "").strip()
    address = request.form.get("address", "").strip()

    if not name:
        return redirect(url_for("index"))

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO customers (name, phone, gstin, address) VALUES (?, ?, ?, ?)",
        (name, phone, gstin, address),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/product", methods=["POST"])
def add_product():
    name = request.form.get("name", "").strip()
    hsn = request.form.get("hsn", "").strip()
    rate = request.form.get("rate", "0").strip()
    gst_rate = request.form.get("gst_rate", "0").strip()

    if not name:
        return redirect(url_for("index"))

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO products (name, hsn, rate, gst_rate) VALUES (?, ?, ?, ?)",
        (name, hsn, float(rate), float(gst_rate)),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/invoice", methods=["POST"])
def create_invoice():
    customer_id = request.form.get("customer_id")
    notes = request.form.get("notes", "").strip()
    product_ids = request.form.getlist("product_id")
    quantities = request.form.getlist("quantity")

    if not customer_id or not product_ids:
        return redirect(url_for("index"))

    conn = get_db_connection()
    subtotal = 0.0
    gst_total = 0.0
    invoice_items = []

    for idx, product_id in enumerate(product_ids):
        if not product_id:
            continue

        quantity = float(quantities[idx]) if idx < len(quantities) and quantities[idx] else 0
        if quantity <= 0:
            continue

        product = conn.execute(
            "SELECT * FROM products WHERE id = ?",
            (int(product_id),),
        ).fetchone()
        if not product:
            continue

        taxable_amount = product["rate"] * quantity
        gst_amount = taxable_amount * (product["gst_rate"] / 100)
        total_amount = taxable_amount + gst_amount

        subtotal += taxable_amount
        gst_total += gst_amount

        invoice_items.append(
            {
                "product_id": int(product_id),
                "quantity": quantity,
                "rate": product["rate"],
                "gst_rate": product["gst_rate"],
                "taxable_amount": taxable_amount,
                "gst_amount": gst_amount,
                "total_amount": total_amount,
            }
        )

    if not invoice_items:
        conn.close()
        return redirect(url_for("index"))

    grand_total = subtotal + gst_total
    invoice_no = generate_invoice_number()

    cursor = conn.execute(
        """
        INSERT INTO invoices (invoice_no, customer_id, invoice_date, subtotal, gst_total, grand_total, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            invoice_no,
            int(customer_id),
            datetime.now().strftime("%Y-%m-%d"),
            round(subtotal, 2),
            round(gst_total, 2),
            round(grand_total, 2),
            notes,
        ),
    )

    invoice_id = cursor.lastrowid
    for item in invoice_items:
        conn.execute(
            """
            INSERT INTO invoice_items (
                invoice_id, product_id, quantity, rate, gst_rate,
                taxable_amount, gst_amount, total_amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                invoice_id,
                item["product_id"],
                item["quantity"],
                item["rate"],
                item["gst_rate"],
                item["taxable_amount"],
                item["gst_amount"],
                item["total_amount"],
            ),
        )

    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/invoice/<int:invoice_id>")
def invoice_details(invoice_id):
    conn = get_db_connection()
    invoice = conn.execute(
        """
        SELECT i.*, c.name AS customer_name, c.phone, c.gstin, c.address
        FROM invoices i
        JOIN customers c ON c.id = i.customer_id
        WHERE i.id = ?
        """,
        (invoice_id,),
    ).fetchone()

    items = conn.execute(
        """
        SELECT ii.*, p.name AS product_name, p.hsn
        FROM invoice_items ii
        JOIN products p ON p.id = ii.product_id
        WHERE ii.invoice_id = ?
        """,
        (invoice_id,),
    ).fetchall()
    conn.close()

    if not invoice:
        return redirect(url_for("index"))

    return render_template("invoice.html", invoice=invoice, items=items)


init_db()
seed_demo_data()

if __name__ == "__main__":
    app.run(debug=True)


































































































































