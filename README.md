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

Authentication & Session
|Method	 | Path	                       | Description	                      | Access       |
|--------|-----------------------------|--------------------------------------|--------------|
|POST	 | /api/auth/login	           | Authenticate customer/admin sessions | Guest        |
|POST	 | /api/auth/signup	           | Register new customer accounts       | Guest        |
|POST	 | /api/profile/password/reset | Update account passwords	          | Authenticated|

Shopping Cart & Addresses
|Method	 | Path	                         | Description	                          | Access      |
|--------|-------------------------------|----------------------------------------|-------------|
|GET	 | /api/cart	                 | Retrieve current cart items & subtotals|	Customer    |
|POST	 | /api/cart/add	             | Add product to cart	                  | Customer    |
|POST	 | /api/cart/update	             | Update item quantity (validated)	      | Customer    |
|POST	 | /api/cart/remove	             | Remove item from cart                  | Customer    |
|POST	 | /api/customer/addresses/add   | Add address to profile list	          | Customer    |
|POST	 | /api/customer/addresses/select| Set active address for shipping	      | Customer    |
|POST	 | /api/customer/addresses/delete| Remove address from profile list	      | Customer    |

Transaction Lifecycle
|Method	 | Path	                       | Description	                       | Access       |
|--------|-----------------------------|---------------------------------------|--------------|
|POST	 | /api/cart/checkout	       | Convert cart contents to pending Order| Customer     |
|POST	 | /api/payment/process   	   | Route payment and update order status | Customer     |

Operational Administration
|Method	 | Path	                            | Description	                             | Access       |
|--------|----------------------------------|--------------------------------------------|--------------|
|POST	 | /api/admin/product/add	        | Add new product to catalog	             | Admin(Staff) |
|POST	 | /api/admin/product/restock	    | Replenish product stock level	             | Admin(Staff) |
|POST	 | /api/admin/product/toggle_active | Toggle visibility of catalog item	         | Admin(Staff) |
|POST	 | /api/admin/product/remove	    | Hard-delete product from catalog	         | Admin(Staff) |
|POST	 | /api/admin/category/add	        | Create new product category	             | Admin(Staff) |
|POST	 | /api/admin/category/rename	    | Rename category title	                     | Admin(Staff) |
|POST	 | /api/admin/category/toggle_active| Toggle category activation	             | Admin(Staff) |
|POST	 | /api/admin/order/accept	        | Accept order (pending →processing)         | Admin(Staff) |
|POST	 | /api/admin/order/ship	        | Dispatch order (processing → shipped)      | Admin(Staff) |
|POST	 | /api/admin/order/deliver	        | Mark order delivered (shipped → delivered) | Admin(Staff) |
|POST	 | /api/admin/order/cancel	        | Cancel an active unpaid/pending order	     | Admin(Staff) |
|POST	 | /api/admin/order/refund	        | Refund a cancelled paid order	             | Admin(Staff) |
|POST	 | /api/admin/ticket/resolve	    | Resolve support ticket	                 | Admin(Staff) |

Business Intelligence & Cooperation
|Method	 | Path	                           | Description	                                  | Access       |
|--------|---------------------------------|--------------------------------------------------|--------------|
|GET	 | /api/admin/report/<type>	       | Compile inventory, sales, orders, or support data|	Manager      |
|POST	 | /api/admin/report/request	   | Standard staff requests report compilation	      | Admin(Staff) |
|GET	 | /api/admin/notifications	       | Fetch context-aware admin notifications	      | Admin        |
|POST	 | /api/admin/notifications/read   | Mark admin notifications as read	              | Admin        |
|GET	 | /api/customer/notifications	   | Fetch active order status notifications	      | Customer     |
|POST	 | /api/customer/notifications/read| Mark customer notifications as read	          | Customer     |


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

## Heuristics Implemented
| Heuristic                | Where                        |
|--------------------------|------------------------------|
| Heuristic 2.9 (Cohesion) | `Product.reduce_stock`       |        
| Heuristic 5.1 (RBAC)     | `app.py / admin.html`        |

## Demo Account 
Use these pre-seeded accounts to log in and test different user roles across the platform:
| Role	              | Email Address	  | Password   | Description / Permissions               |
|---------------------|-------------------|------------|-----------------------------------------|
| Customer (Shopper)  | alex@acemart.com  |	pw123	   | Can shop, manage cart/addresses, pay, view invoices, raise tickets, and leave feedback.|
| Manager (Admin)     |	sam@acemart.com	  | admin123   | Full access, including the real-time visual charts dashboard, report generation, and support ticket assignment. |
| Staff (Admin)	      | lee@acemart.com	  | staff123   | Operational access to manage products, restock, transition orders, and resolve assigned tickets. |

## Role Positions & Features
Shopper (Customer)
- Authenticated Portal: Isolated login view with a self-service password-reset interface inside profile settings.
- Shopping Cart & Checkout: Manual quantity entry capped at maximum available inventory, and multi-address management (add, edit, select, or delete).
- Payment Processing: Modal simulation for credit cards and e-wallets, incorporating success, decline, and re-attempt routines.
- In-App Notifications: Real-time alerts displayed through a navigation header bell dropdown whenever order statuses are updated.
- Orders & Invoices: Interactive order ledger showing items and tracking details, with a printable, paper-style invoice showing custom payment methods.
- Support & Feedback: Submit support tickets, reopen resolved inquiries (CRC 4.17), and leave reviews once order delivery is confirmed.

Store Staff (Admin)
- Isolated Portal: Access via ?mode=staff, with standard shopper options hidden.
- Product Management: Create new catalog entries, hard-delete, or soft-delete produc (toggling visible/hidden status) to protect transactional records.
- Category Administration (CRC 4.7): Create, rename, or toggle category visibility.
- Manual Inventory Restocking: Replenish stock on-demand, with status badges updating on the UI.
- Order Transition Operations: Move orders manually through the status lifecycle  (Accept → Ship → Deliver → Cancel → Refund).
- Support Ticket Resolutions: Resolve customer support tickets directly on demand.
- Real-time Notifications: Real-time bell dropdown notifications showing new orders, low-stock warnings (≤10 units), new tickets, and reviews.

Manager (Admin + Elevated Privileges)
- Consolidated Dashboard: Real-time visual metrics showing 5 custom Chart.js charts covering inventory, sales, orders, feedback, and support upon login.
- Reports compilation: Compiles reports on inventory turnover ratios, category revenues, and top-selling product rankings.
- Staff Reports Request Loop: Receives real-time notifications when staff requests a report. Automatically notifies staff once a report is compiled.