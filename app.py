"""
app.py — ACE Mart e-commerce store built on the UML class models.
"""
import uuid
from flask import Flask, jsonify, render_template, request, abort, session

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
    # id, name, desc, price, stock, emoji, category
    ("p-001", "Truffle Chips",        "Black truffle & sea salt kettle chips",     4.99,  80, "🍟", "chips"),
    ("p-002", "Mango Chili Gummies",  "Sweet-heat mango gummy bears",              3.49,  120,"🥭", "candy"),
    ("p-003", "Matcha Pocky",         "Japanese matcha cream biscuit sticks",      2.99,  95, "🍵", "biscuits"),
    ("p-004", "Ghost Pepper Puffs",   "Dangerously spicy corn puffs",              3.99,  60, "🌶️", "chips"),
    ("p-005", "Birthday Cake Oreos",  "Limited edition birthday cake filling",     4.49,  45, "🎂", "biscuits"),
    ("p-006", "Salted Caramel Nuts",  "Mixed nuts in salted caramel glaze",        6.99,  70, "🥜", "nuts"),
    ("p-007", "Watermelon Sour Belts","Chewy sour watermelon candy strips",        2.49,  150,"🍉", "candy"),
    ("p-008", "Wasabi Peas",          "Crunchy green peas with wasabi kick",       3.29,  85, "🟢", "nuts"),
    ("p-009", "Cheddar Popcorn",      "Extra sharp aged cheddar popcorn",          3.79,  110,"🍿", "chips"),
    ("p-010", "Strawberry Mochi",     "Soft Japanese rice cake, strawberry cream", 5.99,  40, "🍓", "sweets"),
    ("p-011", "Dark Choc Almonds",    "70% dark chocolate coated almonds",         7.49,  65, "🍫", "sweets"),
    ("p-012", "Tajin Mangonadas",     "Dried mango with tajin chili lime",         4.29,  90, "🌮", "candy"),
    ("p-013", "Korean Seaweed Snack", "Crispy sesame roasted seaweed sheets",      2.79,  130,"🌊", "biscuits"),
    ("p-014", "Honey Butter Chips",   "Korean honey butter flavoured chips",       4.49,  75, "🍯", "chips"),
    ("p-015", "Pistachio Baklava",    "Flaky honey-soaked pistachio pastry bites", 8.99,  0,  "🥐", "sweets"),
]

def seed_data():
    Manager.reset()
    mgr = Manager.get_instance()

    customer = AccountFactory.create("customer", "Alex Kim", "alex@acemart.com", "pw123",
                                     phone="555-0101", address="42 Crunch Lane")
    admin = AccountFactory.create("admin", "Sam Store", "sam@acemart.com", "admin123")

    categories = {
        "chips":    Category("c-01", "Chips & Crisps",    "Crunchy, salty, irresistible"),
        "candy":    Category("c-02", "Candy & Gummies",   "Sweet, sour, chewy & wild"),
        "biscuits": Category("c-03", "Biscuits & Sticks", "Cookies, crackers & more"),
        "nuts":     Category("c-04", "Nuts & Seeds",      "Roasted, spiced & glazed"),
        "sweets":   Category("c-05", "Sweets & Chocolate","Indulgent treats & desserts"),
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
        invoice = order.generate_invoice()
        gw = CreditCardGateway("**** **** **** 4242", "12/27")
        pmt = Payment(str(uuid.uuid4()), order, order.total_amount, gw)
        order.add_payment(pmt)
        pmt.process()
        ship = Shipment(str(uuid.uuid4()), order, "SnackExpress", "SE-00123", customer.address)
        order.add_shipment(ship)
        ship.ship()
        order.receive_feedback(5, "Arrived super fast and the truffle chips are AMAZING 🙌")

    app.config["STORE"] = {
        "catalogue": catalogue,
        "customer":  customer,
        "admin":     admin,
        "products":  products,
        "categories": categories,
    }

# ── Pages ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    store   = app.config["STORE"]
    mgr     = Manager.get_instance()
    cat_filter = request.args.get("category", "all")
    search_q   = request.args.get("q", "").strip()

    if search_q:
        products = store["catalogue"].search(search_q)
    elif cat_filter != "all":
        cat = next((c for c in store["catalogue"].categories if c.category_id == cat_filter), None)
        products = cat.products if cat else []
    else:
        products = store["catalogue"].all_products()

    cart = store["customer"].get_or_create_cart()
    return render_template("store.html",
        catalogue=store["catalogue"],
        products=products,
        categories=store["catalogue"].categories,
        cat_filter=cat_filter,
        search_q=search_q,
        cart=cart,
        orders=mgr.orders,
        customer=store["customer"],
    )

@app.route("/cart")
def cart_page():
    store = app.config["STORE"]
    cart  = store["customer"].get_or_create_cart()
    return render_template("cart.html", cart=cart, customer=store["customer"])

@app.route("/orders")
def orders_page():
    store = app.config["STORE"]
    mgr   = Manager.get_instance()
    return render_template("orders.html", orders=mgr.orders, customer=store["customer"])

# ── API ──────────────────────────────────────────────────────────────────────

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
    return jsonify({"success": ok, "item_count": cart.item_count(), "total": cart.total()})

@app.route("/api/cart/remove", methods=["POST"])
def api_cart_remove():
    data       = request.get_json(force=True)
    product_id = data.get("product_id")
    customer   = app.config["STORE"]["customer"]
    cart       = customer.get_or_create_cart()
    ok         = cart.remove_product(product_id)
    return jsonify({"success": ok, "item_count": cart.item_count(), "total": cart.total()})

@app.route("/api/cart/update", methods=["POST"])
def api_cart_update():
    data       = request.get_json(force=True)
    product_id = data.get("product_id")
    quantity   = int(data.get("quantity", 1))
    customer   = app.config["STORE"]["customer"]
    cart       = customer.get_or_create_cart()
    ok         = cart.update_quantity(product_id, quantity)
    return jsonify({"success": ok, "item_count": cart.item_count(), "total": cart.total()})

@app.route("/api/cart/checkout", methods=["POST"])
def api_checkout():
    store    = app.config["STORE"]
    customer = store["customer"]
    mgr      = Manager.get_instance()
    cart     = customer.get_or_create_cart()
    if not cart.items:
        return jsonify({"success": False, "error": "Cart is empty"}), 400
    order = customer.place_order()
    if not order:
        return jsonify({"success": False, "error": "Could not create order"}), 500
    mgr.process_order(order)
    invoice = order.generate_invoice()
    gw  = CreditCardGateway("**** **** **** 4242", "12/27")
    pmt = Payment(str(uuid.uuid4()), order, order.total_amount, gw)
    order.add_payment(pmt)
    pmt.process()
    return jsonify({"success": True, "order_id": order.order_id, "total": order.total_amount})

@app.route("/api/products")
def api_products():
    mgr = Manager.get_instance()
    return jsonify([p.to_dict() for p in mgr.products])

@app.route("/api/orders")
def api_orders():
    mgr = Manager.get_instance()
    return jsonify([o.to_dict() for o in mgr.orders])

@app.route("/api/cart")
def api_cart():
    cart = app.config["STORE"]["customer"].get_or_create_cart()
    return jsonify(cart.to_dict())

if __name__ == "__main__":
    seed_data()
    app.run(debug=True, port=5000)