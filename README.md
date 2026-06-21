# ACE Mart System — Python + Flask 

Generated from the UML class diagram. Every class lives in its own file
under `models/`, with all classes also bundled in `all_classes.py`.

## Project structure

```
Software-Architecture-Assignment-3/
├── app.py                    # Flask application + seed data + API routes
├── all_classes.py            # Standalone single-file version of ALL classes
├── requirements.txt
├── models/
│   ├── __init__.py           # Convenient re-exports
│   ├── account.py            # Base Account
│   ├── account_factory.py    # Factory Pattern
│   ├── customer.py           # Customer (extends Account)
│   ├── admin.py              # Admin (extends Account)
│   ├── manager.py            # Singleton Pattern
│   │── report.py             # Passive Report entity
│   ├── product.py            # Product (soft-deletion & low-stock signaling)
│   ├── category.py           # Category (soft deactivation)
│   ├── catalogue.py          # Aggregate catalog lookup
│   ├── shopping_cart.py      # CartItem + ShoppingCart (Composition)
│   ├── order.py              # Order state-machine
│   ├── invoice.py            # Invoice entity (stores true grand totals)
│   ├── payment_gateway.py    # Strategy Pattern (CreditCard vs EWallet)
│   ├── payment.py            # Payment processor
│   ├── shipment.py           # Shipment logistics controller
│   ├── feedback.py           # Customer Feedback
│   └── support_ticket.py     # Customer Support Ticket
└── templates/
    ├── store.html            # Shopper Catalog & Navigation
    ├── cart.html             # Interactive Cart, Address Book, & Payment Gateway
    ├── payment.html          # Standalone Payment Checkout Portal
    ├── orders.html           # Customer Order History (Interactive card toggles)
    ├── invoice.html          # Printable, Paper-style Invoice Page
    ├── support.html          # Support Center (Ticket submission & Reopening)
    ├── profile.html          # Unified Profile Settings & Password Reset (Customer & Staff)
    ├── admin.html            # Operational Admin Panel (Orders lifecycle, Categories & Tickets)
    └── admin_dashboard.html  # Manager Real-Time Analytical Charts Dashboard
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

## Demo Account 
Use these pre-seeded accounts to log in and test different user roles across the platform:
| Role	              | Email Address	  | Password   | Description / Permissions                                                                                       |
|---------------------|-------------------|------------|-----------------------------------------------------------------------------------------------------------------|
| Customer (Shopper)  | alex@acemart.com  |	pw123	   | Can shop, manage cart/addresses, pay, view invoices, raise tickets, and leave feedback.                         |
| Manager (Admin)     |	sam@acemart.com	  | admin123   | Full access, including the real-time visual charts dashboard, report generation, and support ticket assignment. |
| Staff (Admin)	      | lee@acemart.com	  | staff123   | Operational access to manage products, restock, transition orders, and resolve assigned tickets.                |