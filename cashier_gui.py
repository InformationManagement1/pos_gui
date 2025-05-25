import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import mysql.connector
import subprocess

def logout():
    root.destroy()
    subprocess.Popen(["python", "login.py"])

# Connect to MySQL
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="your_mysql_user",
        password="your_mysql_password",
        database="pos_system"
    )

cart = []
gift_card_code = ""

# Temporary products dictionary for testing without DB
temp_products = {
    "123456": {"product_id": 1, "barcode": "123456", "name": "Rice", "price": 100.0, "stock": 5},
    "789012": {"product_id": 2, "barcode": "789012", "name": "Kwek2x", "price": 50.0, "stock": 3},
    "345678": {"product_id": 3, "barcode": "345678", "name": "Siomai", "price": 75.0, "stock": 0},  # out of stock example
}

# Add product to cart by barcode
def add_product(barcode):
    # Uncomment this section when ready to use DB
    """
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE barcode = %s", (barcode,))
        product = cursor.fetchone()

        if not product:
            messagebox.showerror("Error", "Product not found.")
            return

        if product["stock"] <= 0:
            messagebox.showwarning("Out of Stock", "Product is out of stock.")
            return

        cart.append(product)
        cursor.execute("UPDATE products SET stock = stock - 1 WHERE product_id = %s", (product["product_id"],))
        conn.commit()
        refresh_cart()

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        conn.close()
    """

    # Temporary non-DB code for testing
    product = temp_products.get(barcode)
    if not product:
        messagebox.showerror("Error", "Product not found.")
        return
    if product["stock"] <= 0:
        messagebox.showwarning("Out of Stock", "Product is out of stock.")
        return

    # Decrease stock locally for temp testing
    product["stock"] -= 1

    cart.append(product)
    refresh_cart()

# Refresh cart UI
def refresh_cart():
    for i in cart_tree.get_children():
        cart_tree.delete(i)
    total = 0
    for idx, item in enumerate(cart):
        cart_tree.insert("", "end", iid=idx, values=(item["name"], item["price"]))
        total += item["price"]
    total_label.config(text=f"Total: ₱{total:.2f}")

# Load customer list
def load_customers():
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM customers")
        return cursor.fetchall()
    except:
        return []
    finally:
        if conn:
            conn.close()

# Apply gift card
def apply_gift_card():
    global gift_card_code
    code = gift_card_entry.get()
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM gift_cards WHERE card_code = %s AND status = 'active'", (code,))
        card = cursor.fetchone()
        if not card:
            messagebox.showerror("Invalid", "Gift card not valid or already used.")
            return
        gift_card_code = code
        gift_card_balance_label.config(text=f"Gift Card Balance: ₱{card['balance']:.2f}")
    except mysql.connector.Error as err:
        messagebox.showerror("DB Error", str(err))
    finally:
        conn.close()

# Process checkout
def checkout():
    if not cart:
        messagebox.showwarning("Empty Cart", "Cart is empty.")
        return

    try:
        conn = connect_db()
        cursor = conn.cursor()

        subtotal = sum(item["price"] for item in cart)
        discount = 0

        # Loyalty points
        customer_id = customer_var.get()
        if customer_id != "None":
            cursor.execute("SELECT * FROM customers WHERE customer_id = %s", (customer_id,))
            customer = cursor.fetchone()
            points_to_redeem = min(customer[4], int(subtotal))  # loyalty_points
            discount += points_to_redeem
            new_points = int(subtotal / 100)
            cursor.execute(
                "UPDATE customers SET loyalty_points = loyalty_points - %s + %s WHERE customer_id = %s",
                (points_to_redeem, new_points, customer_id)
            )
        else:
            customer_id = None

        # Gift card
        if gift_card_code:
            cursor.execute("SELECT balance FROM gift_cards WHERE card_code = %s", (gift_card_code,))
            card = cursor.fetchone()
            if card:
                usable = min(card[0], subtotal - discount)
                discount += usable
                cursor.execute("UPDATE gift_cards SET balance = balance - %s WHERE card_code = %s", (usable, gift_card_code))
                cursor.execute("UPDATE gift_cards SET status = 'used' WHERE card_code = %s AND balance <= 0", (gift_card_code,))

        total = max(0, subtotal - discount)

        # Insert transaction
        cursor.execute(
            "INSERT INTO sales_transactions (cashier_id, total_amount, payment_method, customer_id) VALUES (%s, %s, %s, %s)",
            (1, total, "Cash", customer_id)
        )
        transaction_id = cursor.lastrowid

        for item in cart:
            cursor.execute(
                "INSERT INTO sales_items (transaction_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
                (transaction_id, item["product_id"], 1, item["price"])
            )

        conn.commit()
        messagebox.showinfo("Success", f"Transaction complete!\nTotal Paid: ₱{total:.2f}")
        cart.clear()
        refresh_cart()
        gift_card_entry.delete(0, tk.END)
        gift_card_balance_label.config(text="Gift Card Balance: ₱0.00")

    except mysql.connector.Error as err:
        messagebox.showerror("DB Error", str(err))
    finally:
        conn.close()

# GUI SETUP
root = tk.Tk()
root.title("Retail POS System")

frame = tk.Frame(root)
frame.pack(pady=10, padx=10)

tk.Label(frame, text="Scan Barcode:").grid(row=0, column=0)
barcode_entry = tk.Entry(frame)
barcode_entry.grid(row=0, column=1)
barcode_entry.focus()

def scan_product(event=None):
    add_product(barcode_entry.get())
    barcode_entry.delete(0, tk.END)

barcode_entry.bind("<Return>", scan_product)

cart_tree = ttk.Treeview(frame, columns=("Product", "Price"), show="headings", height=10)
cart_tree.heading("Product", text="Product")
cart_tree.heading("Price", text="Price (₱)")
cart_tree.grid(row=1, column=0, columnspan=2, pady=10)

total_label = tk.Label(frame, text="Total: ₱0.00", font=("Arial", 14))
total_label.grid(row=2, column=0, columnspan=2)

# Loyalty customer dropdown
tk.Label(frame, text="Customer:").grid(row=3, column=0)
customers = load_customers()
customer_options = ["None"] + [str(c["customer_id"]) for c in customers]
customer_var = tk.StringVar(value="None")
customer_dropdown = ttk.Combobox(frame, textvariable=customer_var, values=customer_options)
customer_dropdown.grid(row=3, column=1)

# Gift card input
tk.Label(frame, text="Gift Card Code:").grid(row=4, column=0)
gift_card_entry = tk.Entry(frame)
gift_card_entry.grid(row=4, column=1)

gift_card_balance_label = tk.Label(frame, text="Gift Card Balance: ₱0.00")
gift_card_balance_label.grid(row=5, column=0, columnspan=2)

apply_card_btn = tk.Button(frame, text="Apply Gift Card", command=apply_gift_card)
apply_card_btn.grid(row=6, column=0, columnspan=2, pady=5)

checkout_btn = tk.Button(frame, text="Checkout", command=checkout, bg="green", fg="white")
checkout_btn.grid(row=7, column=0, columnspan=2, pady=10, ipadx=20)

tk.Button(root, text="Logout", command=lambda: logout(), bg="red", fg="white").pack(pady=10)

root.mainloop()
