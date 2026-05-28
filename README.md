# ACE Mart System — Python + Flask

Generated from the UML class diagram. Every class lives in its own file
under `models/`, with all classes also bundled in `all_classes.py`.

## Project structure

```
Software-Architecture-Assignment-3/
├── app.py                    # Flask application + seed data + API routes
├── all_classes.py            # ★ Standalone single-file version of ALL classes
├── requirements.txt
├── models/
│   ├── __init__.py           # Convenient re-exports
│   ├── account.py            # Base Account
│   ├── account_factory.py    # Factory Pattern
│   ├── customer.py           # Customer (extends Account)
│   ├── admin.py              # Admin (extends Account)
│   ├── manager.py            # Singleton Pattern
│   ├── report.py
│   ├── product.py
│   ├── category.py
│   ├── catalogue.py
│   ├── shopping_cart.py      # CartItem + ShoppingCart (Composition)
│   ├── order.py
│   ├── invoice.py
│   ├── payment_gateway.py    # Strategy Pattern (CreditCard + EWallet)
│   ├── payment.py
│   ├── shipment.py
│   ├── feedback.py
│   └── support_ticket.py
└── templates/
    ├── cart.html
    ├── orders.html
    └── store.html
```

## Quick start

```bash
# 1. Install Flask
pip install flask

# 2a. Run the Flask website
cd Software-Architecture-Assignment-3
python app.py
# → Open http://localhost:5000

# 2b. The standalone demo for all classes (no Flask needed)
python all_classes.py
```

## API Endpoints

| Method | Path                     | Description                    |
|--------|--------------------------|--------------------------------|
| GET    | /                        | HTML dashboard                 |
| GET    | /api/products            | All products (JSON)            |
| GET    | /api/products/<id>       | Single product                 |
| GET    | /api/catalogue           | Full catalogue + categories    |
| GET    | /api/categories          | All categories                 |
| GET    | /api/orders              | All orders                     |
| GET    | /api/orders/<id>         | Single order                   |
| GET    | /api/cart                | Demo customer's cart           |
| POST   | /api/cart/add            | Add item: {product_id, quantity}|
| GET    | /api/reports/inventory   | Inventory report (Singleton)   |
| GET    | /api/reports/orders      | Orders report                  |
| GET    | /api/feedback            | All feedback                   |
| GET    | /api/tickets             | All support tickets            |
| POST   | /api/tickets             | New ticket: {subject, description} |
| GET    | /api/manager             | Manager singleton state        |

## Using all_classes.py independently

```python
from all_classes import AccountFactory, Manager, Catalogue, Category, Product

# Factory pattern
customer = AccountFactory.create("customer", "Jane", "jane@x.com", "pw")

# Singleton
mgr = Manager.get_instance()

# Build catalogue
cat = Category("c1", "Books")
cat.add_product(Product("p1", "Clean Code", "...", 35.00, 10))
```

## Design patterns

| Pattern     | Where                                          |
|-------------|------------------------------------------------|
| Factory     | `AccountFactory.create("customer" / "admin")`  |
| Singleton   | `Manager.get_instance()`                       |
| Strategy    | `PaymentGateway` → `CreditCardGateway` / `EWalletGateway` |
| Composition | `Customer ◆── ShoppingCart` (cart deleted with customer) |
| Aggregation | `Catalogue ◇── Category ◇── Product`          |