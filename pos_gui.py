import tkinter as tk
from tkinter import messagebox, simpledialog
import datetime
import os

# Dummy DB connection and data
def connect_db():
    # Placeholder for DB connection
    pass

# Dummy product data with stock count
PRODUCTS = [
    {"product_id": 1, "name": "Product A", "price": 100, "stock": 10, "barcode": "12345"},
    {"product_id": 2, "name": "Product B", "price": 200, "stock": 8, "barcode": "23456"},
    {"product_id": 3, "name": "Product C", "price": 50, "stock": 15, "barcode": "34567"},
]

# Dummy user data
USERS = {
    "cashier1": {"password": "pass", "role": "Cashier"},
    "manager1": {"password": "pass", "role": "Manager"},
}

# Global cart variable
cart = []

# Global suspended sale storage
suspended_sale = None

# Cash drawer info
cash_drawer_opening_amount = 1000.00
cash_drawer_current = cash_drawer_opening_amount

# Gift card dummy data (code: balance)
GIFT_CARDS = {
    "GIFT100": 100,
    "GIFT500": 500,
}

# Loyalty points store (user: points)
LOYALTY_POINTS = {
    "cashier1": 0,
    "manager1": 0,
}

class POSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("POS System")
        self.geometry("900x600")

        self.logged_in_user = None
        self.role = None

        self.sidebar = None
        self.main_frame = None

        self.cart = []
        self.discount = 0.0
        self.gift_card_balance = 0.0
        self.loyalty_points_earned = 0

        self.create_login_screen()

    def create_login_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

        tk.Label(self, text="Login", font=("Arial", 24)).pack(pady=20)

        tk.Label(self, text="Username:").pack()
        self.username_entry = tk.Entry(self)
        self.username_entry.pack()

        tk.Label(self, text="Password:").pack()
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack()

        tk.Button(self, text="Login", command=self.login).pack(pady=10)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        user = USERS.get(username)
        if user and user["password"] == password:
            self.logged_in_user = username
            self.role = user["role"]
            self.load_main_ui()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")

    def load_main_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.sidebar = tk.Frame(self, bg="#333", width=180)
        self.sidebar.pack(side="left", fill="y")

        self.main_frame = tk.Frame(self, bg="#eee")
        self.main_frame.pack(side="right", expand=True, fill="both")

        self.build_sidebar()
        self.show_dashboard()

    def build_sidebar(self):
        for widget in self.sidebar.winfo_children():
            widget.destroy()

        cashier_modules = [
            ("Dashboard", self.show_dashboard),
            ("POS Terminal", self.show_pos_terminal),
            ("Cash Drawer", self.show_cash_drawer),
            ("Returns", self.show_returns),
        ]

        manager_modules = [
            ("Inventory", self.show_inventory),
            ("Promotions", self.show_promotions),
            ("Gift Cards", self.show_gift_cards),
            ("Loyalty Program", self.show_loyalty_program),
            ("Reports", self.show_reports),
            ("Employees", self.show_employees),
            ("Settings", self.show_settings),
        ]

        for name, cmd in cashier_modules:
            btn = tk.Button(self.sidebar, text=name, fg="white", bg="#444", relief="flat",
                            command=cmd, padx=10, pady=10, anchor="w")
            btn.pack(fill="x", pady=2)

        if self.role == "Manager":
            for name, cmd in manager_modules:
                btn = tk.Button(self.sidebar, text=name, fg="white", bg="#444", relief="flat",
                                command=cmd, padx=10, pady=10, anchor="w")
                btn.pack(fill="x", pady=2)

        spacer = tk.Frame(self.sidebar, bg="#333")
        spacer.pack(expand=True, fill="both")

        logout_btn = tk.Button(self.sidebar, text="Logout", fg="white", bg="#444", relief="flat",
                               command=self.logout, padx=10, pady=10, anchor="w")
        logout_btn.pack(fill="x", pady=2)

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Welcome to the POS System", font=("Arial", 24)).pack(pady=20)
        tk.Label(self.main_frame, text=f"Logged in as: {self.logged_in_user} ({self.role})").pack()

    def show_pos_terminal(self):
        self.clear_main_frame()

        tk.Label(self.main_frame, text="POS Terminal", font=("Arial", 20)).pack(pady=10)

        search_frame = tk.Frame(self.main_frame)
        search_frame.pack(pady=5)

        tk.Label(search_frame, text="Search Product (Name or Barcode):").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", padx=5)

        tk.Button(search_frame, text="Search", command=self.search_products).pack(side="left")

        self.products_frame = tk.Frame(self.main_frame)
        self.products_frame.pack(pady=10)

        self.cart_frame = tk.Frame(self.main_frame, bd=2, relief="groove")
        self.cart_frame.pack(side="right", fill="y", padx=10, pady=10)

        tk.Label(self.cart_frame, text="Cart", font=("Arial", 16)).pack()

        self.cart_listbox = tk.Listbox(self.cart_frame, width=40)
        self.cart_listbox.pack(pady=5)

        self.cart_totals_label = tk.Label(self.cart_frame, text="Subtotal: ₱0.00\nDiscount: ₱0.00\nGift Card: ₱0.00\nTotal: ₱0.00\nLoyalty Points Earned: 0", justify="left")
        self.cart_totals_label.pack(pady=5)

        payment_frame = tk.Frame(self.cart_frame)
        payment_frame.pack(pady=10)

        tk.Button(payment_frame, text="Complete Sale", command=self.checkout).pack(fill="x", pady=5)
        tk.Button(payment_frame, text="Suspend Sale", command=self.suspend_sale).pack(fill="x", pady=5)
        tk.Button(payment_frame, text="Redeem Loyalty Points", command=self.redeem_loyalty_points).pack(fill="x", pady=5)
        tk.Button(payment_frame, text="Apply Gift Card", command=self.apply_gift_card).pack(fill="x", pady=5)

        self.load_products(PRODUCTS)
        self.update_cart_display()

    def load_products(self, products):
        for widget in self.products_frame.winfo_children():
            widget.destroy()

        for p in products:
            stock_display = f" (Stock: {p['stock']})" if p['stock'] is not None else ""
            btn = tk.Button(self.products_frame, text=f"{p['name']}\n₱{p['price']:.2f}{stock_display}", width=18, height=3,
                            command=lambda prod=p: self.add_to_cart(prod))
            btn.pack(side="left", padx=5, pady=5)

    def search_products(self):
        term = self.search_var.get().strip().lower()
        # Search by name or barcode
        filtered = []
        for p in PRODUCTS:
            if term in p["name"].lower() or term == p["barcode"]:
                filtered.append(p)
        if not filtered:
            messagebox.showinfo("Search", "No products found.")
        self.load_products(filtered)

    def add_to_cart(self, product):
        if product['stock'] <= 0:
            messagebox.showwarning("Out of Stock", f"{product['name']} is out of stock!")
            return
        # Add product to cart
        self.cart.append(product)
        # Decrease stock immediately (simulate live inventory sync)
        product['stock'] -= 1
        self.update_cart_display()
        self.load_products(PRODUCTS)  # Update stock display

        # Stock notification
        if product['stock'] < 5:
            messagebox.showwarning("Low Stock", f"Warning: {product['name']} stock is low ({product['stock']} left)!")

    def update_cart_display(self):
        self.cart_listbox.delete(0, tk.END)
        subtotal = 0
        for item in self.cart:
            self.cart_listbox.insert(tk.END, f"{item['name']} - ₱{item['price']:.2f}")
            subtotal += item['price']

        # Promotions: 10% discount if subtotal > 500
        self.discount = 0.1 * subtotal if subtotal > 500 else 0.0

        # Total after discount
        total_after_discount = max(0, subtotal - self.discount)

        # Apply gift card balance
        gift_card_applied = min(self.gift_card_balance, total_after_discount)
        total_after_gift = total_after_discount - gift_card_applied

        # Loyalty points: 1 point per ₱100 spent on final total
        self.loyalty_points_earned = int(total_after_gift // 100)

        self.cart_totals_label.config(text=(
            f"Subtotal: ₱{subtotal:.2f}\n"
            f"Discount: ₱{self.discount:.2f}\n"
            f"Gift Card: -₱{gift_card_applied:.2f}\n"
            f"Total: ₱{total_after_gift:.2f}\n"
            f"Loyalty Points Earned: {self.loyalty_points_earned}"
        ))

    def checkout(self):
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Add items to cart before checkout.")
            return

        # Payment method selection dialog (simulate multiple payment options)
        payment_methods = ["Cash", "Credit Card", "Mobile Payment", "Contactless"]
        method = simpledialog.askstring("Payment Method", f"Enter payment method ({', '.join(payment_methods)}):")
        if method is None or method.strip() == "":
            messagebox.showinfo("Payment Cancelled", "Payment was cancelled.")
            return
        method = method.strip().title()
        if method not in payment_methods:
            messagebox.showerror("Invalid Method", "Unsupported payment method.")
            return

        subtotal = sum(item['price'] for item in self.cart)
        discount = self.discount
        total_after_discount = max(0, subtotal - discount)
        gift_card_applied = min(self.gift_card_balance, total_after_discount)
        total_after_gift = total_after_discount - gift_card_applied

        global cash_drawer_current

        if method == "Cash":
            # Ask for cash received
            cash_received = simpledialog.askfloat("Cash Received", f"Total due: ₱{total_after_gift:.2f}\nEnter cash received:")
            if cash_received is None:
                messagebox.showinfo("Payment Cancelled", "Payment was cancelled.")
                return
            if cash_received < total_after_gift:
                messagebox.showerror("Insufficient Cash", "Cash received is less than total due.")
                return
            change = cash_received - total_after_gift
            cash_drawer_current += total_after_gift  # Add sale money to drawer
        else:
            # For other payment methods, just assume payment succeeds
            change = 0

        # Deduct gift card balance
        if gift_card_applied > 0:
            self.gift_card_balance -= gift_card_applied

        # Add loyalty points
        LOYALTY_POINTS[self.logged_in_user] += self.loyalty_points_earned

        # Generate receipt text
        receipt_text = self.generate_receipt_text(
            self.cart, subtotal, discount, gift_card_applied, total_after_gift, method, change
        )

        # Show receipt popup
        self.show_receipt(receipt_text)

        # Save receipt to file
        self.save_receipt_to_file(receipt_text)

        # Clear cart after sale
        self.cart.clear()
        self.gift_card_balance = 0.0
        self.update_cart_display()
        self.load_products(PRODUCTS)

        messagebox.showinfo("Sale Complete", f"Payment successful. Change: ₱{change:.2f}\nCash drawer balance: ₱{cash_drawer_current:.2f}")

    def generate_receipt_text(self, cart, subtotal, discount, gift_card_used, total, payment_method, change):
        lines = []
        lines.append("==== RECEIPT ====")
        lines.append(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Cashier: {self.logged_in_user}")
        lines.append("-----------------")
        for item in cart:
            lines.append(f"{item['name']} - ₱{item['price']:.2f}")
        lines.append("-----------------")
        lines.append(f"Subtotal: ₱{subtotal:.2f}")
        lines.append(f"Discount: -₱{discount:.2f}")
        lines.append(f"Gift Card Used: -₱{gift_card_used:.2f}")
        lines.append(f"Total: ₱{total:.2f}")
        lines.append(f"Payment Method: {payment_method}")
        lines.append(f"Change: ₱{change:.2f}")
        lines.append("=================")
        lines.append(f"Loyalty Points Earned: {self.loyalty_points_earned}")
        lines.append("Thank you for shopping!")
        return "\n".join(lines)

    def show_receipt(self, receipt_text):
        receipt_win = tk.Toplevel(self)
        receipt_win.title("Receipt")
        receipt_textbox = tk.Text(receipt_win, width=50, height=30)
        receipt_textbox.pack(padx=10, pady=10)
        receipt_textbox.insert("1.0", receipt_text)
        receipt_textbox.config(state="disabled")

    def save_receipt_to_file(self, receipt_text):
        folder = "receipts"
        os.makedirs(folder, exist_ok=True)
        filename = f"receipt_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join(folder, filename)
        with open(filepath, "w") as f:
            f.write(receipt_text)

    def apply_gift_card(self):
        code = simpledialog.askstring("Gift Card", "Enter gift card code:")
        if not code:
            return
        code = code.strip().upper()
        balance = GIFT_CARDS.get(code)
        if balance is None:
            messagebox.showerror("Invalid Code", "Gift card code not found.")
            return
        self.gift_card_balance = balance
        messagebox.showinfo("Gift Card Applied", f"Gift card balance of ₱{balance:.2f} applied.")
        self.update_cart_display()

    def redeem_loyalty_points(self):
        points = LOYALTY_POINTS.get(self.logged_in_user, 0)
        if points <= 0:
            messagebox.showinfo("No Points", "You have no loyalty points to redeem.")
            return
        redeem = simpledialog.askinteger("Redeem Points", f"You have {points} points.\nRedeem points? (1 point = ₱1)", minvalue=0, maxvalue=points)
        if redeem is None or redeem == 0:
            return
        # Apply redemption as discount
        if redeem > 0:
            self.discount += redeem
            LOYALTY_POINTS[self.logged_in_user] -= redeem
            messagebox.showinfo("Points Redeemed", f"Redeemed {redeem} points as discount.")
            self.update_cart_display()

    def suspend_sale(self):
        global suspended_sale
        if not self.cart:
            messagebox.showwarning("Empty Cart", "No sale to suspend.")
            return
        suspended_sale = {
            "cart": self.cart.copy(),
            "gift_card_balance": self.gift_card_balance,
            "discount": self.discount
        }
        self.cart.clear()
        self.gift_card_balance = 0.0
        self.discount = 0.0
        self.update_cart_display()
        self.load_products(PRODUCTS)
        messagebox.showinfo("Sale Suspended", "Current sale has been suspended.")

    def resume_sale(self):
        global suspended_sale
        if suspended_sale:
            self.cart = suspended_sale["cart"]
            self.gift_card_balance = suspended_sale["gift_card_balance"]
            self.discount = suspended_sale["discount"]
            suspended_sale = None
            self.update_cart_display()
            self.load_products(PRODUCTS)
            messagebox.showinfo("Sale Resumed", "Suspended sale has been resumed.")
        else:
            messagebox.showinfo("No Suspended Sale", "There is no suspended sale to resume.")

    # Placeholder functions for other modules
    def show_cash_drawer(self):
        self.clear_main_frame()
        global cash_drawer_current, cash_drawer_opening_amount
        tk.Label(self.main_frame, text="Cash Drawer Management", font=("Arial", 20)).pack(pady=20)
        tk.Label(self.main_frame, text=f"Opening Amount: ₱{cash_drawer_opening_amount:.2f}").pack()
        tk.Label(self.main_frame, text=f"Current Drawer Balance: ₱{cash_drawer_current:.2f}").pack()
        tk.Button(self.main_frame, text="Reset Drawer (New Day)", command=self.reset_cash_drawer).pack(pady=10)

    def reset_cash_drawer(self):
        global cash_drawer_current, cash_drawer_opening_amount
        cash_drawer_current = cash_drawer_opening_amount
        messagebox.showinfo("Reset", "Cash drawer balance reset to opening amount.")

    def show_returns(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Returns Module (Coming Soon)", font=("Arial", 20)).pack(pady=20)

    def show_inventory(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Inventory Management (Coming Soon)", font=("Arial", 20)).pack(pady=20)

    def show_promotions(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Promotions (10% off for purchases over ₱500)", font=("Arial", 16)).pack(pady=10)
        tk.Label(self.main_frame, text="This is an automatic discount applied at checkout.").pack()

    def show_gift_cards(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Gift Cards Available", font=("Arial", 16)).pack(pady=10)
        for code, bal in GIFT_CARDS.items():
            tk.Label(self.main_frame, text=f"Code: {code} - Balance: ₱{bal:.2f}").pack()

    def show_loyalty_program(self):
        self.clear_main_frame()
        points = LOYALTY_POINTS.get(self.logged_in_user, 0)
        tk.Label(self.main_frame, text="Loyalty Program", font=("Arial", 20)).pack(pady=10)
        tk.Label(self.main_frame, text=f"You currently have {points} points.").pack()

    def show_reports(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Reports Module (Coming Soon)", font=("Arial", 20)).pack(pady=20)

    def show_employees(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Employees Module (Coming Soon)", font=("Arial", 20)).pack(pady=20)

    def show_settings(self):
        self.clear_main_frame()
        resume_btn = tk.Button(self.main_frame, text="Resume Suspended Sale", command=self.resume_sale)
        resume_btn.pack(pady=20)
        tk.Label(self.main_frame, text="Settings Module (Coming Soon)", font=("Arial", 20)).pack()

    def logout(self):
        self.logged_in_user = None
        self.role = None
        self.cart.clear()
        self.gift_card_balance = 0.0
        self.discount = 0.0
        self.loyalty_points_earned = 0
        self.create_login_screen()


if __name__ == "__main__":
    app = POSApp()
    app.mainloop()
