"""
app.py — ACE Mart e-commerce store built on the UML class models.
Authentication: session-based login for Customers and Admin (Manager/Staff roles).
"""
import uuid
import hashlib
from flask import Flask, jsonify, render_template, request, abort, session, redirect, url_for

from models import (
    AccountFactory, Manager, Catalogue, Category, Product,
    CreditCardGateway, EWalletGateway, Payment, Shipment,
    Order, Invoice, Feedback, SupportTicket,
    Customer, Admin, Report, ShoppingCart, CartItem,
    PaymentGateway, Account,
)

app = Flask(__name__)
app.secret_key = "acemart-secret-2024"

SNACK_PRODUCTS = [
    ("p-001", "Truffle Chips",        "Black truffle & sea salt kettle chips",      4.99,  80, "🍟", "chips"),
    ("p-002", "Mango Chili Gummies",  "Sweet-heat mango gummy bears",               3.49, 120, "🥭", "candy"),
    ("p-003", "Matcha Pocky",         "Japanese matcha cream biscuit sticks",       2.99,  95, "🍵", "biscuits"),
    ("p-004", "Ghost Pepper Puffs",   "Dangerously spicy corn puffs",               3.99,  60, "🌶️", "chips"),
    ("p-005", "Birthday Cake Oreos",  "Limited edition birthday cake filling",      4.49,  45, "🎂", "biscuits"),
    ("p-006", "Salted Caramel Nuts",  "Mixed nuts in salted caramel glaze",         6.99,  70, "🥜", "nuts"),
    ("p-007", "Watermelon Sour Belts","Chewy sour watermelon candy strips",         2.49, 150, "🍉", "candy"),
    ("p-008", "Wasabi Peas",          "Crunchy green peas with wasabi kick",        3.29,  85, "🟢", "nuts"),
    ("p-009", "Cheddar Popcorn",      "Extra sharp aged cheddar popcorn",           3.79, 110, "🍿", "chips"),
    ("p-010", "Strawberry Mochi",     "Soft Japanese rice cake, strawberry cream",  5.99,  40, "🍓", "sweets"),
    ("p-011", "Dark Choc Almonds",    "70% dark chocolate coated almonds",          7.49,  65, "🍫", "sweets"),
    ("p-012", "Tajin Mangonadas",     "Dried mango with tajin chili lime",          4.29,  90, "🌮", "candy"),
    ("p-013", "Korean Seaweed Snack", "Crispy sesame roasted seaweed sheets",       2.79, 130, "🌊", "biscuits"),
    ("p-014", "Honey Butter Chips",   "Korean honey butter flavoured chips",        4.49,  75, "🍯", "chips"),
    ("p-015", "Pistachio Baklava",    "Flaky honey-soaked pistachio pastry bites",  8.99,   0, "🥐", "sweets"),
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_store():
    return app.config.get("STORE", {})

def get_current_user():
    uid  = session.get("user_id")
    if not uid:
        return None
    store = get_store()
    accounts = store.get("accounts", {})
    for acc in accounts.values():
        if acc.account_id == uid:
            return acc
    session.clear()
    return None

def login_required_customer(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("user_role") != "customer" or not session.get("user_id"):
            session["next"] = request.url
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated

def login_required_admin(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("user_role") not in ("admin", "manager", "staff") \
                or not session.get("user_id"):
            session["next"] = request.url
            return redirect(url_for("login_page") + "?mode=staff")
        return f(*args, **kwargs)
    return decorated

# ── Seed data ─────────────────────────────────────────────────────────────────

@app.before_request
def ensure_seeded():
    """Auto-reseed after Flask debug hot-reload wipes app.config."""
    if not app.config.get("STORE"):
        seed_data()

def seed_data():
    Manager.reset()
    mgr = Manager.get_instance()

    customer = AccountFactory.create(
        "customer", "Alex Kim", "alex@acemart.com", "pw123",
        phone="555-0101", address="42 Crunch Lane"
    )
    # Seed multiple sample addresses
    customer.addresses = ["42 Crunch Lane", "Suite 4B, 100 Gourmet Blvd", "Snack Locker #12, Railway St"]
    admin = AccountFactory.create(
        "admin", "Sam Store", "sam@acemart.com", "admin123", role="manager"
    )
    staff = AccountFactory.create(
        "admin", "Lee Staff", "lee@acemart.com", "staff123", role="staff"
    )

    categories = {
        "chips":    Category("c-01", "Chips & Crisps",     "Crunchy, salty, irresistible"),
        "candy":    Category("c-02", "Candy & Gummies",    "Sweet, sour, chewy & wild"),
        "biscuits": Category("c-03", "Biscuits & Sticks",  "Cookies, crackers & more"),
        "nuts":     Category("c-04", "Nuts & Seeds",       "Roasted, spiced & glazed"),
        "sweets":   Category("c-05", "Sweets & Chocolate", "Indulgent treats & desserts"),
    }

    products = {}
    for pid, name, desc, price, stock, emoji, cat_key in SNACK_PRODUCTS:
        p = Product(pid, name, desc, price, stock)
        p.image_url = emoji
        categories[cat_key].add_product(p)
        mgr.manage_product(p)
        products[pid] = p

    catalogue = Catalogue("main", "ACE Mart Store")
    for cat in categories.values():
        catalogue.add_category(cat)

    # Demo order
    cart = customer.get_or_create_cart()
    cart.add_product(products["p-001"], 2)
    cart.add_product(products["p-010"], 1)
    order = customer.place_order()
    if order:
        mgr.process_order(order)
        order.generate_invoice()
        gw  = CreditCardGateway("**** **** **** 4242", "12/27")
        pmt = Payment(str(uuid.uuid4()), order, order.total_amount, gw)
        order.add_payment(pmt)
        pmt.process()
        cart.confirm_order()  # reduce stock + clear cart after demo payment
        ship = Shipment(str(uuid.uuid4()), order, "SnackExpress", "SE-00123", customer.address)
        order.add_shipment(ship)
        ship.ship()
        ship.mark_delivered()
        fb = order.receive_feedback(5, "Arrived super fast and the truffle chips are AMAZING!")
        customer.feedback_list.append(fb)

    ticket = customer.raise_support_ticket(
        "Missing item in order",
        "I ordered 2 Truffle Chips but only received 1 bag."
    )
    ticket.assign(admin)

    app.config["STORE"] = {
        "catalogue":  catalogue,
        "customer":   customer,
        "admin":      admin,
        "staff":      staff,
        "products":   products,
        "categories": categories,
        "accounts":   {
            customer.email: customer,
            admin.email:    admin,
            staff.email:    staff,
        },
    }

# ── Auth Routes ───────────────────────────────────────────────────────────────

@app.route("/login")
def login_page():
    if get_current_user():
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data       = request.get_json(force=True) or {}
    email      = data.get("email", "").strip().lower()
    password   = data.get("password", "")
    role_hint  = data.get("role", "customer")
    staff_role = data.get("staff_role", "manager")

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password are required"}), 400

    store    = get_store()
    accounts = store.get("accounts", {})
    account  = accounts.get(email)

    if not account:
        return jsonify({"success": False, "error": "No account found with that email"}), 401
    if not account.is_active:
        return jsonify({"success": False, "error": "This account has been deactivated"}), 403
    if account.password_hash != hash_password(password):
        return jsonify({"success": False, "error": "Incorrect password"}), 401

    is_customer = isinstance(account, Customer)
    is_admin    = isinstance(account, Admin)

    if role_hint == "customer" and not is_customer:
        return jsonify({"success": False, "error": "This is a staff account. Use the Staff tab."}), 403
    if role_hint == "admin" and not is_admin:
        return jsonify({"success": False, "error": "This is a customer account. Use the Shopper tab."}), 403

    session["user_id"]   = account.account_id
    session["username"]  = account.username
    if is_admin:
        session["user_role"]  = account.role  # "manager" or "staff"
        redirect_url = "/admin"
    else:
        session["user_role"]  = "customer"
        redirect_url = session.pop("next", "/")

    return jsonify({
        "success":  True,
        "username": account.username,
        "role":     session["user_role"],
        "redirect": redirect_url,
    })

@app.route("/api/auth/signup", methods=["POST"])
def api_signup():
    data    = request.get_json(force=True) or {}
    name    = data.get("username", "").strip()
    email   = data.get("email", "").strip().lower()
    phone   = data.get("phone", "").strip()
    address = data.get("address", "").strip()
    pw      = data.get("password", "")

    if not name:
        return jsonify({"success": False, "error": "Name cannot be blank"}), 400
    if not email or "@" not in email:
        return jsonify({"success": False, "error": "Enter a valid email address"}), 400
    if not address:
        return jsonify({"success": False, "error": "Delivery address is required"}), 400
    if len(pw) < 6:
        return jsonify({"success": False, "error": "Password must be at least 6 characters"}), 400

    store    = get_store()
    accounts = store.get("accounts", {})
    if email in accounts:
        return jsonify({"success": False, "error": "An account with that email already exists"}), 409

    new_customer = AccountFactory.create(
        "customer", name, email, pw, phone=phone, address=address
    )
    accounts[email] = new_customer
    session["user_id"]   = new_customer.account_id
    session["username"]  = new_customer.username
    session["user_role"] = "customer"

    return jsonify({"success": True, "username": new_customer.username, "redirect": "/"}), 201

# ── Page Routes ───────────────────────────────────────────────────────────────

@app.route("/")
def index():
    store      = get_store()
    mgr        = Manager.get_instance()
    cat_filter = request.args.get("category", "all")
    search_q   = request.args.get("q", "").strip()

    if search_q:
        products = store["catalogue"].search(search_q)
    elif cat_filter != "all":
        cat = next((c for c in store["catalogue"].categories
                    if c.category_id == cat_filter), None)
        products = cat.products if cat else []
    else:
        products = store["catalogue"].all_products()

    # Filter out inactive products so shoppers cannot see them
    products = [p for p in products if p.is_active]

    current_user = get_current_user()
    customer     = current_user if isinstance(current_user, Customer) else None
    cart         = customer.get_or_create_cart() if customer else None

    return render_template("store.html",
        catalogue=store["catalogue"],
        products=products,
        categories=store["catalogue"].categories,
        cat_filter=cat_filter,
        search_q=search_q,
        cart=cart,
        customer=customer,
        is_logged_in=current_user is not None,
        user_role=session.get("user_role", ""),
    )

@app.route("/cart")
@login_required_customer
def cart_page():
    customer = get_current_user()
    cart     = customer.get_or_create_cart()
    return render_template("cart.html", cart=cart, customer=customer)


@app.route("/payment")
@login_required_customer
def payment_page():
    """Standalone payment page — used by payment.html standalone flow."""
    customer = get_current_user()
    cart     = customer.get_or_create_cart()
    if not cart.items:
        return redirect(url_for("cart_page"))
    return render_template("payment.html", cart=cart, customer=customer)
@app.route("/orders")
@login_required_customer
def orders_page():
    mgr      = Manager.get_instance()
    customer = get_current_user()
    my_orders = [o for o in mgr.orders if o.customer.account_id == customer.account_id]
    return render_template("orders.html", orders=my_orders, customer=customer)

@app.route("/support")
@login_required_customer
def support_page():
    mgr      = Manager.get_instance()
    customer = get_current_user()
    my_orders = [o for o in mgr.orders if o.customer.account_id == customer.account_id]
    return render_template("support.html",
        customer=customer,
        tickets=customer.support_tickets,
        orders=my_orders,
    )

@app.route("/admin")
@login_required_admin
def admin_page():
    store = get_store()
    mgr   = Manager.get_instance()
    admin = get_current_user()

    # 1. Active Products Count (where p.is_active is True)
    active_products_count = sum(1 for p in mgr.products if p.is_active)

    # 2. Ongoing Orders Count (excluding delivered, cancelled, and refunded finalized states)
    ongoing_orders_count = sum(1 for o in mgr.orders if o.status in ("pending", "processing", "shipped"))

    # Support Tickets parsing
    all_tickets = []
    for o in mgr.orders:
        all_tickets.extend(o.support_tickets)
    for acc in store["accounts"].values():
        if isinstance(acc, Customer):
            all_tickets.extend(acc.support_tickets)
    seen, unique_tickets = set(), []
    for t in all_tickets:
        if t.ticket_id not in seen:
            unique_tickets.append(t)
            seen.add(t.ticket_id)

    # 3. Ongoing Tickets Count (where status is open or in_progress)
    ongoing_tickets_count = sum(1 for t in unique_tickets if t.status in ("open", "in_progress"))

    all_feedbacks = [o.feedback for o in mgr.orders if o.feedback]

    # 4. New Reviews Count (Reviews submitted in the last 7 days)
    from datetime import datetime
    now = datetime.now()
    new_reviews_count = sum(1 for o in mgr.orders if o.feedback and (now - o.feedback.submitted_at).days <= 7)

    # 5. Out of Stock Count (where stock_quantity is 0)
    out_of_stock_count = sum(1 for p in mgr.products if p.stock_quantity == 0)

    staff_members = [acc for acc in store["accounts"].values() if isinstance(acc, Admin)]

    return render_template("admin.html",
        admin=admin,
        manager=mgr,
        catalogue=store["catalogue"],
        products=mgr.products,
        categories=store["catalogue"].categories,
        orders=mgr.orders,
        tickets=unique_tickets,
        feedbacks=all_feedbacks,
        staff_role=session.get("user_role", "admin"),
        staff_members=staff_members,
        
        # Pass the updated KPI counts to the template
        active_products_count=active_products_count,
        ongoing_orders_count=ongoing_orders_count,
        ongoing_tickets_count=ongoing_tickets_count,
        new_reviews_count=new_reviews_count,
        out_of_stock_count=out_of_stock_count,
    )

# ── Cart API ──────────────────────────────────────────────────────────────────

@app.route("/api/cart/add", methods=["POST"])
def api_cart_add():
    if session.get("user_role") != "customer":
        return jsonify({"success": False, "error": "Please log in to add items to cart", "login_required": True}), 401

    data       = request.get_json(force=True) or {}
    product_id = data.get("product_id", "").strip()
    quantity   = data.get("quantity", 1)
    if not product_id:
        return jsonify({"success": False, "error": "product_id is required"}), 400
    try:
        quantity = int(quantity)
        if quantity < 1: raise ValueError
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "quantity must be a positive integer"}), 400

    mgr       = Manager.get_instance()
    customer  = get_current_user()
    catalogue = get_store()["catalogue"]
    p = next((p for p in mgr.products if p.product_id == product_id), None)
    if not p:
        return jsonify({"success": False, "error": "Product not found"}), 404
    cart = customer.get_or_create_cart()
    ok   = cart.add_product(p, quantity, catalogue=catalogue)
    if not ok:
        return jsonify({"success": False, "error": "Product is out of stock"}), 409
    return jsonify({"success": True, "item_count": cart.item_count(), "total": cart.total()})

@app.route("/api/cart/remove", methods=["POST"])
def api_cart_remove():
    if session.get("user_role") != "customer":
        return jsonify({"success": False, "error": "Not logged in"}), 401
    data       = request.get_json(force=True) or {}
    product_id = data.get("product_id", "").strip()
    customer   = get_current_user()
    cart       = customer.get_or_create_cart()
    ok         = cart.remove_product(product_id)
    return jsonify({"success": ok, "item_count": cart.item_count(), "total": cart.total()})

@app.route("/api/cart/update", methods=["POST"])
def api_cart_update():
    if session.get("user_role") != "customer":
        return jsonify({"success": False, "error": "Not logged in"}), 401
    data       = request.get_json(force=True) or {}
    product_id = data.get("product_id", "").strip()
    quantity   = data.get("quantity", 1)
    try: quantity = int(quantity)
    except: return jsonify({"success": False, "error": "quantity must be an integer"}), 400
    customer = get_current_user()
    cart     = customer.get_or_create_cart()
    ok       = cart.update_quantity(product_id, quantity)
    
    if not ok:
        return jsonify({"success": False, "error": "Requested quantity exceeds available stock"}), 409
        
    return jsonify({"success": True, "item_count": cart.item_count(), "total": cart.total()})


@app.route("/api/cart/checkout", methods=["POST", "GET"])
def api_checkout():
    if request.method == "GET":
        return jsonify({"error": "Use POST to checkout"}), 405
    if session.get("user_role") != "customer":
        return jsonify({"success": False, "error": "Please log in to checkout", "login_required": True}), 401
    customer = get_current_user()
    if not customer:
        session.clear()
        return jsonify({"success": False, "error": "Session expired. Please log in again.", "login_required": True}), 401
    mgr  = Manager.get_instance()
    cart = customer.get_or_create_cart()
    if not cart.items:
        return jsonify({"success": False, "error": "Cart is empty. Add items before checking out."}), 400
        
    order = cart.convert_to_order()
    if not order:
        return jsonify({"success": False, "error": "Insufficient stock for one or more items"}), 409
        
    customer.orders.append(order)
    mgr.process_order(order)
    order.generate_invoice()
    
    # Calculate grand total including shipping to return to frontend gateways
    shipping = 0 if order.total_amount >= 25 else 3.99
    grand_total = round(order.total_amount + shipping, 2)
    
    return jsonify({"success": True, "order_id": order.order_id, "total": grand_total})  # Return grand_total


@app.route("/api/cart")
def api_cart():
    customer = get_current_user()
    if not customer or not isinstance(customer, Customer):
        return jsonify({"items": [], "total": 0, "item_count": 0})
    return jsonify(customer.get_or_create_cart().to_dict())

# ── Product / Order APIs ──────────────────────────────────────────────────────

@app.route("/api/products")
def api_products():
    return jsonify([p.to_dict() for p in Manager.get_instance().products])

@app.route("/api/orders")
def api_orders():
    return jsonify([o.to_dict() for o in Manager.get_instance().orders])

# ── Admin APIs ────────────────────────────────────────────────────────────────

@app.route("/api/admin/product/add", methods=["POST"])
@login_required_admin
def api_admin_add_product():
    store = get_store(); admin = get_current_user(); mgr = Manager.get_instance()
    data  = request.get_json(force=True) or {}
    name  = data.get("name", "").strip()
    desc  = data.get("description", "").strip()
    cat_id= data.get("category_id", "").strip()
    emoji = data.get("emoji", "📦").strip() or "📦"
    if not name:   return jsonify({"success": False, "error": "Product name cannot be blank"}), 400
    if not cat_id: return jsonify({"success": False, "error": "Category is required"}), 400
    try:
        price = float(data.get("price", 0))
        if price <= 0: raise ValueError
    except: return jsonify({"success": False, "error": "Price must be a positive number"}), 400
    try:
        stock = int(data.get("stock", 0))
        if stock < 0: raise ValueError
    except: return jsonify({"success": False, "error": "Stock must be non-negative"}), 400
    category = store["catalogue"].get_category(cat_id)
    if not category: return jsonify({"success": False, "error": "Category not found"}), 404
    p = Product("p-" + str(uuid.uuid4())[:6], name, desc, round(price, 2), stock)
    p.image_url = emoji
    category.add_product(p); admin.add_product(p); mgr.manage_product(p)
    return jsonify({"success": True, "product": p.to_dict()}), 201

@app.route("/api/admin/product/restock", methods=["POST"])
@login_required_admin
def api_admin_restock():
    data = request.get_json(force=True) or {}
    pid  = data.get("product_id", "").strip()
    if not pid: return jsonify({"success": False, "error": "product_id is required"}), 400
    try:
        qty = int(data.get("quantity", 0))
        if qty <= 0: raise ValueError
    except: return jsonify({"success": False, "error": "quantity must be a positive integer"}), 400
    p = next((p for p in Manager.get_instance().products if p.product_id == pid), None)
    if not p: return jsonify({"success": False, "error": "Product not found"}), 404
    p.restock(qty)
    return jsonify({"success": True, "product": p.to_dict()})

@app.route("/api/admin/product/remove", methods=["POST"])
@login_required_admin
def api_admin_remove_product():
    data = request.get_json(force=True) or {}
    pid  = data.get("product_id", "").strip()
    if not pid: return jsonify({"success": False, "error": "product_id is required"}), 400
    store = get_store()
    for cat in store["catalogue"].categories: cat.remove_product(pid)
    get_current_user().remove_product(pid)
    ok = Manager.get_instance().remove_product(pid)
    return jsonify({"success": ok})

@app.route("/api/admin/report/<report_type>")
@login_required_admin
def api_admin_report(report_type):
    admin = get_current_user()
    
    # RBAC Enforcement: Only managers can request/compile reports from the Manager singleton
    if admin.role != "manager":
        return jsonify({"success": False, "error": "Unauthorized: Only managers can compile system reports."}), 403
        
    if report_type not in {"inventory","orders","sales","feedback","support"}:
        return jsonify({"error": "Unknown report type"}), 400
        
    report = admin.request_report(report_type)
    return jsonify(report.to_dict())

@app.route("/api/admin/ticket/assign", methods=["POST"])
@login_required_admin
def api_admin_assign_ticket():
    data = request.get_json(force=True) or {}
    tid  = data.get("ticket_id", "").strip()
    assignee_id = data.get("assignee_id", "").strip()
    
    if not tid: 
        return jsonify({"success": False, "error": "ticket_id is required"}), 400
        
    # Role Enforcement: Only managers are allowed to assign tickets
    admin = get_current_user()
    if admin.role != "manager":
        return jsonify({"success": False, "error": "Unauthorized: Only managers can assign tickets."}), 403
        
    store = get_store()
    
    # Locate the target assignee (staff member)
    assignee = None
    for acc in store["accounts"].values():
        if acc.account_id == assignee_id:
            assignee = acc
            break
    if not assignee:
        assignee = admin  # Fallback to self-assignment
        
    ticket = None
    for acc in store["accounts"].values():
        if isinstance(acc, Customer):
            ticket = next((t for t in acc.support_tickets if t.ticket_id == tid), None)
            if ticket: break
    if not ticket: 
        return jsonify({"success": False, "error": "Ticket not found"}), 404
        
    ticket.assign(assignee)
    return jsonify({"success": True, "ticket": ticket.to_dict()})

@app.route("/api/admin/ticket/resolve", methods=["POST"])
@login_required_admin
def api_admin_resolve_ticket():
    data  = request.get_json(force=True) or {}
    tid   = data.get("ticket_id", "").strip()
    notes = data.get("notes", "").strip()
    if not tid:   return jsonify({"success": False, "error": "ticket_id is required"}), 400
    if not notes: return jsonify({"success": False, "error": "Resolution notes cannot be blank"}), 400
    
    store  = get_store()
    ticket = None
    for acc in store["accounts"].values():
        if isinstance(acc, Customer):
            ticket = next((t for t in acc.support_tickets if t.ticket_id == tid), None)
            if ticket: break
    if not ticket: 
        return jsonify({"success": False, "error": "Ticket not found"}), 404
        
    # Role Enforcement: A staff member can only resolve if assigned directly to them
    admin = get_current_user()
    if admin.role == "staff" and (not ticket.assigned_to or ticket.assigned_to.account_id != admin.account_id):
        return jsonify({"success": False, "error": "Unauthorized: You cannot resolve a ticket that is not assigned to you."}), 403
        
    ticket.resolve(notes)
    return jsonify({"success": True, "ticket": ticket.to_dict()})

# ── Support Ticket API ────────────────────────────────────────────────────────

@app.route("/api/tickets", methods=["GET"])
def api_tickets():
    customer = get_current_user()
    if not customer or not isinstance(customer, Customer): return jsonify([])
    return jsonify([t.to_dict() for t in customer.support_tickets])

@app.route("/api/tickets", methods=["POST"])
def api_create_ticket():
    if session.get("user_role") != "customer":
        return jsonify({"success": False, "error": "Please log in first"}), 401
    data   = request.get_json(force=True) or {}
    subject= data.get("subject","").strip(); desc = data.get("description","").strip()
    oid    = data.get("order_id","").strip()
    if not subject: return jsonify({"success": False, "error": "Subject cannot be blank"}), 400
    if not desc:    return jsonify({"success": False, "error": "Description cannot be blank"}), 400
    customer = get_current_user(); mgr = Manager.get_instance()
    ticket   = customer.raise_support_ticket(subject, desc)
    if oid:
        order = next((o for o in mgr.orders if o.order_id == oid), None)
        if order: ticket.order = order; order.support_tickets.append(ticket)
    return jsonify({"success": True, "ticket": ticket.to_dict()}), 201

# ── Feedback API ──────────────────────────────────────────────────────────────

@app.route("/api/feedback", methods=["POST"])
def api_submit_feedback():
    if session.get("user_role") != "customer":
        return jsonify({"success": False, "error": "Please log in first"}), 401
    data    = request.get_json(force=True) or {}
    oid     = data.get("order_id","").strip(); comment = data.get("comment","").strip()
    if not oid:     return jsonify({"success": False, "error": "order_id is required"}), 400
    if not comment: return jsonify({"success": False, "error": "Comment cannot be blank"}), 400
    try:
        rating = int(data.get("rating", 0))
        if not 1 <= rating <= 5: raise ValueError
    except: return jsonify({"success": False, "error": "Rating must be between 1 and 5"}), 400
    customer = get_current_user(); mgr = Manager.get_instance()
    order = next((o for o in mgr.orders if o.order_id == oid), None)
    if not order:    return jsonify({"success": False, "error": "Order not found"}), 404
    if order.feedback: return jsonify({"success": False, "error": "Feedback already submitted"}), 409
    fb = order.receive_feedback(rating, comment)
    customer.feedback_list.append(fb)
    return jsonify({"success": True, "feedback": fb.to_dict()}), 201

@app.route("/api/feedback", methods=["GET"])
def api_get_feedback():
    return jsonify([o.feedback.to_dict() for o in Manager.get_instance().orders if o.feedback])
# ── Payment Process API (Scenario 1, Steps 11–24) ────────────────────────────
#
# A2 Scenario 1 sequence:
#   Steps 11-13: Payment routes through PaymentGateway (Strategy Pattern)
#   Steps 14-17 (success): Invoice generated, status → "Paid", Shipment triggered
#   Steps 19-24 (failure): Order reverts to "Pending", customer may reattempt (Assumption A5)

@app.route("/api/payment/process", methods=["POST"])
def api_payment_process():
    if session.get("user_role") != "customer":
        return jsonify({"success": False, "error": "Please log in first", "login_required": True}), 401

    data     = request.get_json(force=True) or {}
    order_id = data.get("order_id", "").strip()
    gw_type  = data.get("gateway", "credit_card")
    sim_fail = data.get("simulate_failure", False)

    if not order_id:
        return jsonify({"success": False, "error": "order_id is required"}), 400

    mgr   = Manager.get_instance()
    order = next((o for o in mgr.orders if o.order_id == order_id), None)
    if not order:
        return jsonify({"success": False, "error": "Order not found"}), 404
    if order.is_paid():
        return jsonify({"success": False, "error": "Order is already paid"}), 409

    # Calculate actual grand total including shipping for the gateway Payment log
    shipping = 0 if order.total_amount >= 25 else 3.99
    grand_total = round(order.total_amount + shipping, 2)

    # Select PaymentGateway strategy at runtime (Strategy Pattern)
    if gw_type == "ewallet":
        provider  = data.get("provider", "TouchNGo")
        wallet_id = data.get("wallet_id", "wallet-demo-001")
        gateway   = EWalletGateway(wallet_id, provider) 
    else:
        card_num = data.get("card_number", "**** **** **** 0000")
        expiry   = data.get("expiry", "00/00")
        digits   = card_num.replace(" ", "")
        masked   = "**** **** **** " + digits[-4:] if len(digits) >= 4 else card_num
        gateway  = CreditCardGateway(masked, expiry) 
        
    # Create Payment using the calculated grand_total
    payment = Payment(str(uuid.uuid4()), order, grand_total, gateway)
    order.add_payment(payment)

    # Demo failure simulation (Assumption A5: multiple attempts allowed)
    if sim_fail:
        payment.status = "failed"
        order.update_status("pending")  # Steps 23-24: revert to Pending
        return jsonify({
            "success":  False,
            "error":    "Payment declined by provider. Please try a different method.",
            "order_id": order.order_id,
            "status":   "pending",
        })

    processed = payment.process()  # Steps 11-13: routes through gateway

    if processed:
         # Confirm order: reduce stock + clear cart
        order.customer.get_or_create_cart().confirm_order()
        order.update_status("pending")  # Remains pending, awaiting Admin acceptance

        return jsonify({  # Step 17: Order Confirmed
            "success":        True,
            "payment_status": "completed",
            "order_id":       order.order_id,
            "total":          order.total_amount,
            "transaction_id": payment.transaction_id,
            "gateway":        gateway.gateway_name(),
            "invoice_id":     order.invoice.invoice_id if order.invoice else None,
            "message":        "Payment authorised! Your order is being processed.",
        })
    else:
        # Steps 22-24: declined — revert to Pending, allow reattempt
        order.update_status("pending")
        return jsonify({
            "success":  False,
            "error":    "Payment declined by provider. Please try a different method.",
            "order_id": order.order_id,
            "status":   "pending",
        })
    
@app.route("/invoice/<invoice_id>")
@login_required_customer
def invoice_page(invoice_id):
    mgr = Manager.get_instance()
    # Find the order that owns this invoice
    order = next((o for o in mgr.orders if o.invoice and o.invoice.invoice_id == invoice_id), None)
    if not order:
        abort(404)
        
    # Security check: Ensure this invoice belongs to the logged-in customer
    customer = get_current_user()
    if order.customer.account_id != customer.account_id:
        abort(403)

     # Find the completed payment for this order (Strategy Pattern)
    payment = next((p for p in order.payments if p.status == "completed"), None)

    return render_template("invoice.html", order=order, invoice=order.invoice, payment=payment)  

@app.route("/api/customer/addresses", methods=["GET"])
@login_required_customer
def api_get_addresses():
    customer = get_current_user()
    return jsonify({"addresses": customer.addresses, "active": customer.address})

@app.route("/api/customer/addresses/add", methods=["POST"])
@login_required_customer
def api_add_address():
    data = request.get_json(force=True) or {}
    address = data.get("address", "").strip()
    if not address:
        return jsonify({"success": False, "error": "Address cannot be blank"}), 400
    customer = get_current_user()
    if address not in customer.addresses:
        customer.addresses.append(address)
    if not customer.address:
        customer.address = address
    return jsonify({"success": True, "addresses": customer.addresses, "active": customer.address})

@app.route("/api/customer/addresses/select", methods=["POST"])
@login_required_customer
def api_select_address():
    data = request.get_json(force=True) or {}
    address = data.get("address", "").strip()
    customer = get_current_user()
    if address in customer.addresses:
        customer.address = address
        return jsonify({"success": True, "active": customer.address})
    return jsonify({"success": False, "error": "Address not found"}), 404

@app.route("/api/customer/addresses/edit", methods=["POST"])
@login_required_customer
def api_edit_address():
    data = request.get_json(force=True) or {}
    old_address = data.get("old_address", "").strip()
    new_address = data.get("new_address", "").strip()
    if not new_address:
        return jsonify({"success": False, "error": "New address cannot be blank"}), 400
    customer = get_current_user()
    if old_address in customer.addresses:
        idx = customer.addresses.index(old_address)
        customer.addresses[idx] = new_address
        if customer.address == old_address:
            customer.address = new_address
        return jsonify({"success": True, "addresses": customer.addresses, "active": customer.address})
    return jsonify({"success": False, "error": "Original address not found"}), 404

@app.route("/profile")
def profile_page():
    user = get_current_user()
    if not user:
        return redirect(url_for("login_page"))
    # Detect if the logged-in user is a customer or admin/staff
    is_admin = isinstance(user, Admin)
    return render_template("profile.html", user=user, is_admin=is_admin)

@app.route("/api/customer/profile/update", methods=["POST"])
def api_update_profile():
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401
        
    data = request.get_json(force=True) or {}
    username = data.get("username", "").strip()
    phone    = data.get("phone", "").strip()
    
    if not username:
        return jsonify({"success": False, "error": "Username cannot be blank"}), 400
        
    user.username = username
    # Phone only exists on Customer accounts
    if not isinstance(user, Admin):
        user.phone = phone
        
    return jsonify({"success": True, "message": "Profile details updated successfully!"})

@app.route("/api/profile/password/reset", methods=["POST"])
def api_password_reset():
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401
        
    data = request.get_json(force=True) or {}
    old_pw = data.get("current_password", "").strip()
    new_pw = data.get("new_password", "").strip()
    
    if not old_pw or not new_pw:
        return jsonify({"success": False, "error": "Both current and new passwords are required"}), 400
    if len(new_pw) < 6:
        return jsonify({"success": False, "error": "New password must be at least 6 characters"}), 400
        
    # Verify current password hash
    if user.password_hash != hash_password(old_pw):
        return jsonify({"success": False, "error": "Current password is incorrect"}), 401
        
    # Set new password
    user.password_hash = hash_password(new_pw)
    return jsonify({"success": True, "message": "Password updated successfully!"})

@app.route("/api/customer/addresses/delete", methods=["POST"])
@login_required_customer
def api_delete_address():
    data = request.get_json(force=True) or {}
    address = data.get("address", "").strip()
    customer = get_current_user()
    if address in customer.addresses:
        customer.addresses.remove(address)
        # Reset active address if the active one was deleted
        if customer.address == address:
            customer.address = customer.addresses[0] if customer.addresses else ""
        return jsonify({"success": True, "addresses": customer.addresses, "active": customer.address})
    return jsonify({"success": False, "error": "Address not found"}), 404

@app.route("/api/admin/order/accept", methods=["POST"])
@login_required_admin
def api_admin_accept_order():
    data = request.get_json(force=True) or {}
    order_id = data.get("order_id", "").strip()
    mgr = Manager.get_instance()
    order = next((o for o in mgr.orders if o.order_id == order_id), None)
    if not order:
        return jsonify({"success": False, "error": "Order not found"}), 404
    order.update_status("processing")
    # Trigger Customer Notification
    order.customer.add_notification(
        f"Your order #{order.order_id[:8].upper()} has been accepted and is now being packed! ⏳", 
        order.order_id
    )
    return jsonify({"success": True, "status": order.status})


@app.route("/api/admin/order/ship", methods=["POST"])
@login_required_admin
def api_admin_ship_order():
    data = request.get_json(force=True) or {}
    order_id = data.get("order_id", "").strip()
    carrier = data.get("carrier", "SnackExpress").strip()
    tracking = data.get("tracking_number", "").strip()
    if not tracking:
        return jsonify({"success": False, "error": "Tracking number is required"}), 400
        
    mgr = Manager.get_instance()
    order = next((o for o in mgr.orders if o.order_id == order_id), None)
    if not order:
        return jsonify({"success": False, "error": "Order not found"}), 404
        
    # Create the shipment manually
    ship = Shipment(
        shipment_id=str(uuid.uuid4()),
        order=order,
        carrier=carrier,
        tracking_number=tracking,
        destination_address=order.customer.address,
    )
    order.add_shipment(ship)
    ship.ship()  # This updates order.status to "shipped"
    # Trigger Customer Notification
    order.customer.add_notification(
        f"Great news! Your order #{order.order_id[:8].upper()} has been shipped via {carrier}! Tracking: {tracking} 🚚", 
        order.order_id
    )
    return jsonify({"success": True, "status": order.status, "tracking": tracking})

@app.route("/api/admin/order/deliver", methods=["POST"])
@login_required_admin
def api_admin_deliver_order():
    data = request.get_json(force=True) or {}
    order_id = data.get("order_id", "").strip()
    mgr = Manager.get_instance()
    order = next((o for o in mgr.orders if o.order_id == order_id), None)
    if not order:
        return jsonify({"success": False, "error": "Order not found"}), 404
        
    if order.shipments:
        order.shipments[0].mark_delivered()
    else:
        order.update_status("delivered")
    # Trigger Customer Notification
    order.customer.add_notification(
        f"Your order #{order.order_id[:8].upper()} has been delivered successfully! Please leave a review. ⭐", 
        order.order_id
    )
    return jsonify({"success": True, "status": order.status})

@app.route("/api/admin/order/cancel", methods=["POST"])
@login_required_admin
def api_admin_cancel_order():
    data = request.get_json(force=True) or {}
    order_id = data.get("order_id", "").strip()
    mgr = Manager.get_instance()
    order = next((o for o in mgr.orders if o.order_id == order_id), None)
    if not order:
        return jsonify({"success": False, "error": "Order not found"}), 404
    order.update_status("cancelled")
    # Trigger Customer Notification
    order.customer.add_notification(
        f"Your order #{order.order_id[:8].upper()} was cancelled.", 
        order.order_id
    )
    return jsonify({"success": True, "status": order.status})

@app.route("/api/admin/order/refund", methods=["POST"])
@login_required_admin
def api_admin_refund_order():
    data = request.get_json(force=True) or {}
    order_id = data.get("order_id", "").strip()
    mgr = Manager.get_instance()
    order = next((o for o in mgr.orders if o.order_id == order_id), None)
    if not order:
        return jsonify({"success": False, "error": "Order not found"}), 404
    order.update_status("refunded")
    # Trigger Customer Notification
    order.customer.add_notification(
        f"Your order #{order.order_id[:8].upper()} has been refunded. 💰", 
        order.order_id
    )
    return jsonify({"success": True, "status": order.status})

@app.route("/api/admin/product/toggle_active", methods=["POST"])
@login_required_admin
def api_admin_toggle_product_active():
    data = request.get_json(force=True) or {}
    pid  = data.get("product_id", "").strip()
    mgr  = Manager.get_instance()
    p    = next((p for p in mgr.products if p.product_id == pid), None)
    if not p:
        return jsonify({"success": False, "error": "Product not found"}), 404
    p.is_active = not p.is_active
    return jsonify({"success": True, "is_active": p.is_active})

@app.route("/api/tickets/reopen", methods=["POST"])
@login_required_customer
def api_reopen_ticket():
    data = request.get_json(force=True) or {}
    tid  = data.get("ticket_id", "").strip()
    if not tid:
        return jsonify({"success": False, "error": "ticket_id is required"}), 400
        
    customer = get_current_user()
    # Find the ticket inside the logged-in customer's own list for security
    ticket = next((t for t in customer.support_tickets if t.ticket_id == tid), None)
    if not ticket:
        return jsonify({"success": False, "error": "Ticket not found or unauthorized"}), 404
        
    if ticket.status != "resolved":
        return jsonify({"success": False, "error": "Only resolved tickets can be reopened."}), 400
        
    ticket.reopen()
    return jsonify({"success": True, "ticket": ticket.to_dict()})

@app.route("/api/admin/category/add", methods=["POST"])
@login_required_admin
def api_admin_add_category():
    data = request.get_json(force=True) or {}
    name = data.get("name", "").strip()
    desc = data.get("description", "").strip()
    if not name:
        return jsonify({"success": False, "error": "Category name cannot be blank"}), 400
        
    store = get_store()
    catalogue = store["catalogue"]
    
    # Avoid duplicate names
    if any(c.name.lower() == name.lower() for c in catalogue.categories):
        return jsonify({"success": False, "error": "A category with that name already exists"}), 409
        
    cat_id = "c-" + str(uuid.uuid4())[:6]
    new_cat = Category(cat_id, name, desc)
    catalogue.add_category(new_cat)
    return jsonify({"success": True, "category": new_cat.to_dict()}), 201

@app.route("/api/admin/category/rename", methods=["POST"])
@login_required_admin
def api_admin_rename_category():
    data = request.get_json(force=True) or {}
    cid  = data.get("category_id", "").strip()
    new_name = data.get("name", "").strip()
    if not cid:
        return jsonify({"success": False, "error": "category_id is required"}), 400
    if not new_name:
        return jsonify({"success": False, "error": "New category name cannot be blank"}), 400
        
    store = get_store()
    catalogue = store["catalogue"]
    cat = catalogue.get_category(cid)
    if not cat:
        return jsonify({"success": False, "error": "Category not found"}), 404
        
    cat.name = new_address = new_name
    return jsonify({"success": True, "category": cat.to_dict()})

@app.route("/api/admin/category/toggle_active", methods=["POST"])
@login_required_admin
def api_admin_toggle_category_active():
    data = request.get_json(force=True) or {}
    cid  = data.get("category_id", "").strip()
    if not cid:
        return jsonify({"success": False, "error": "category_id is required"}), 400
        
    store = get_store()
    catalogue = store["catalogue"]
    cat = catalogue.get_category(cid)
    if not cat:
        return jsonify({"success": False, "error": "Category not found"}), 404
        
    cat.is_active = not cat.is_active
    return jsonify({"success": True, "category": cat.to_dict()})

@app.route("/api/admin/alerts", methods=["GET"])
@login_required_admin
def api_admin_get_alerts():
    mgr = Manager.get_instance()
    # Return alerts reverse-sorted (newest first)
    return jsonify({
        "alerts": mgr.alerts[::-1],
        "unread_count": sum(1 for a in mgr.alerts if not a["read"])
    })

@app.route("/api/admin/alerts/read", methods=["POST"])
@login_required_admin
def api_admin_read_alerts():
    mgr = Manager.get_instance()
    for a in mgr.alerts:
        a["read"] = True
    return jsonify({"success": True})

@app.route("/api/customer/notifications", methods=["GET"])
@login_required_customer
def api_customer_get_notifications():
    customer = get_current_user()
    return jsonify({
        "notifications": customer.notifications[::-1] if hasattr(customer, "notifications") else [],
        "unread_count": sum(1 for n in customer.notifications if not n["read"]) if hasattr(customer, "notifications") else 0
    })

@app.route("/api/customer/notifications/read", methods=["POST"])
@login_required_customer
def api_customer_read_notifications():
    customer = get_current_user()
    if hasattr(customer, "notifications"):
        for n in customer.notifications:
            n["read"] = True
    return jsonify({"success": True})


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    seed_data()
    app.run(debug=True, port=5000)

