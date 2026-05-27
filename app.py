"""
app.py — Flask website for the E-Commerce UML system.
Bootstraps demo data and exposes REST-style JSON API endpoints
plus a rich HTML dashboard.
"""
import uuid
from flask import Flask, jsonify, render_template, request, abort

# Use the package models
from models import (
    AccountFactory, Manager, Catalogue, Category, Product,
    CreditCardGateway, EWalletGateway, Payment, Shipment,
)

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Bootstrap demo data (runs once on startup)
# ---------------------------------------------------------------------------
def seed_data():
    mgr = Manager.get_instance()

    # Accounts
    customer = AccountFactory.create("customer", "Alice Chen", "alice@example.com", "pw123",
                                      phone="555-0101", address="10 Elm Street")
    admin     = AccountFactory.create("admin",    "Bob Admin",  "bob@store.com",     "adminpw")

    # Products
    products = [
        Product("p-001", "Laptop Pro 15",    "Powerful 15-inch laptop",        1299.99, 8),
        Product("p-002", "Wireless Mouse",   "Ergonomic wireless mouse",          29.99, 25),
        Product("p-003", "Mechanical Keyboard","RGB mechanical keyboard",         89.99, 15),
        Product("p-004", "Python Programming","Best-selling Python textbook",     39.99, 40),
        Product("p-005", "USB-C Hub",        "7-in-1 USB-C hub",                 49.99, 0),   # OOS
        Product("p-006", "Monitor 27\"",     "4K 27-inch IPS monitor",          449.99, 5),
    ]

    # Categories
    cat_tech  = Category("c-01", "Electronics",  "Computers, peripherals & more")
    cat_books = Category("c-02", "Books",         "Programming & tech books")
    cat_acc   = Category("c-03", "Accessories",   "Cables, hubs & add-ons")

    cat_tech.add_product(products[0])
    cat_tech.add_product(products[1])
    cat_tech.add_product(products[2])
    cat_tech.add_product(products[5])
    cat_books.add_product(products[3])
    cat_acc.add_product(products[4])

    # Catalogue
    catalogue = Catalogue("main", "Tech Store")
    catalogue.add_category(cat_tech)
    catalogue.add_category(cat_books)
    catalogue.add_category(cat_acc)

    for p in products:
        mgr.manage_product(p)

    # Demo order
    cart = customer.get_or_create_cart()
    cart.add_product(products[0], 1)
    cart.add_product(products[3], 2)
    order = customer.place_order()
    if order:
        mgr.process_order(order)
        invoice = order.generate_invoice()
        gw = CreditCardGateway("**** **** **** 4242", "12/27")
        pmt = Payment(str(uuid.uuid4()), order, order.total_amount, gw)
        order.add_payment(pmt)
        pmt.process()
        ship = Shipment(str(uuid.uuid4()), order, "QuickShip", "QS-00123", customer.address)
        order.add_shipment(ship)
        ship.ship()
        order.receive_feedback(5, "Super fast delivery — love the laptop!")

    # Stash references in app config for route access
    app.config["STORE"] = {
        "catalogue": catalogue,
        "customer":  customer,
        "admin":     admin,
        "products":  products,
    }

# ---------------------------------------------------------------------------
# HTML Dashboard
# ---------------------------------------------------------------------------
@app.route("/")
def dashboard():
    mgr   = Manager.get_instance()
    store = app.config["STORE"]
    return render_template("dashboard.html",
        manager=mgr,
        catalogue=store["catalogue"],
        customer=store["customer"],
        admin=store["admin"],
    )

# ---------------------------------------------------------------------------
# API — Products
# ---------------------------------------------------------------------------
@app.route("/api/products", methods=["GET"])
def api_products():
    mgr = Manager.get_instance()
    return jsonify([p.to_dict() for p in mgr.products])

@app.route("/api/products/<product_id>", methods=["GET"])
def api_product(product_id):
    mgr = Manager.get_instance()
    p = next((p for p in mgr.products if p.product_id == product_id), None)
    if not p: abort(404)
    return jsonify(p.to_dict())

# ---------------------------------------------------------------------------
# API — Catalogue & Categories
# ---------------------------------------------------------------------------
@app.route("/api/catalogue", methods=["GET"])
def api_catalogue():
    return jsonify(app.config["STORE"]["catalogue"].to_dict())

@app.route("/api/categories", methods=["GET"])
def api_categories():
    catalogue = app.config["STORE"]["catalogue"]
    return jsonify([c.to_dict() for c in catalogue.categories])

# ---------------------------------------------------------------------------
# API — Orders
# ---------------------------------------------------------------------------
@app.route("/api/orders", methods=["GET"])
def api_orders():
    mgr = Manager.get_instance()
    return jsonify([o.to_dict() for o in mgr.orders])

@app.route("/api/orders/<order_id>", methods=["GET"])
def api_order(order_id):
    mgr = Manager.get_instance()
    o = next((o for o in mgr.orders if o.order_id == order_id), None)
    if not o: abort(404)
    return jsonify(o.to_dict())

# ---------------------------------------------------------------------------
# API — Cart operations (demo customer)
# ---------------------------------------------------------------------------
@app.route("/api/cart", methods=["GET"])
def api_cart():
    customer = app.config["STORE"]["customer"]
    cart = customer.get_or_create_cart()
    return jsonify(cart.to_dict())

@app.route("/api/cart/add", methods=["POST"])
def api_cart_add():
    data       = request.get_json(force=True)
    product_id = data.get("product_id")
    quantity   = int(data.get("quantity", 1))
    mgr        = Manager.get_instance()
    customer   = app.config["STORE"]["customer"]
    p = next((p for p in mgr.products if p.product_id == product_id), None)
    if not p: abort(404)
    cart = customer.get_or_create_cart()
    ok   = cart.add_product(p, quantity)
    return jsonify({"success": ok, "cart": cart.to_dict()})

# ---------------------------------------------------------------------------
# API — Reports
# ---------------------------------------------------------------------------
@app.route("/api/reports/inventory", methods=["GET"])
def api_report_inventory():
    admin  = app.config["STORE"]["admin"]
    report = admin.request_report("inventory")
    return jsonify(report.to_dict())

@app.route("/api/reports/orders", methods=["GET"])
def api_report_orders():
    admin  = app.config["STORE"]["admin"]
    report = admin.request_report("orders")
    return jsonify(report.to_dict())

# ---------------------------------------------------------------------------
# API — Feedback
# ---------------------------------------------------------------------------
@app.route("/api/feedback", methods=["GET"])
def api_feedback():
    mgr = Manager.get_instance()
    feedbacks = [o.feedback.to_dict() for o in mgr.orders if o.feedback]
    return jsonify(feedbacks)

# ---------------------------------------------------------------------------
# API — Support Tickets
# ---------------------------------------------------------------------------
@app.route("/api/tickets", methods=["GET"])
def api_tickets():
    customer = app.config["STORE"]["customer"]
    return jsonify([t.to_dict() for t in customer.support_tickets])

@app.route("/api/tickets", methods=["POST"])
def api_create_ticket():
    data     = request.get_json(force=True)
    customer = app.config["STORE"]["customer"]
    ticket   = customer.raise_support_ticket(
        subject=data.get("subject", "No subject"),
        description=data.get("description", ""),
    )
    return jsonify(ticket.to_dict()), 201

# ---------------------------------------------------------------------------
# API — Manager state
# ---------------------------------------------------------------------------
@app.route("/api/manager", methods=["GET"])
def api_manager():
    return jsonify(Manager.get_instance().to_dict())

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    Manager.reset()   # clear singleton between reloads
    seed_data()
    app.run(debug=True, port=5000)