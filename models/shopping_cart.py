"""
ShoppingCart model - owned by Customer (composition), contains Products,
and converts to an Order.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Optional
from datetime import datetime

if TYPE_CHECKING:
    from .customer import Customer
    from .product import Product
    from .order import Order


class CartItem:
    def __init__(self, product: Product, quantity: int):
        self.product = product
        self.quantity = quantity

    def subtotal(self) -> float:
        return round(self.product.price * self.quantity, 2)

    def to_dict(self) -> dict:
        return {
            "product_id": self.product.product_id,
            "product_name": self.product.name,
            "price": self.product.price,
            "quantity": self.quantity,
            "subtotal": self.subtotal(),
        }


class ShoppingCart:
    def __init__(self, owner: Customer):
        self.owner = owner
        self.items: Dict[str, CartItem] = {}
        self.created_at = datetime.now()

    def add_product(self, product: Product, quantity: int = 1) -> bool:
        if not product.is_available():
            return False
        if product.product_id in self.items:
            self.items[product.product_id].quantity += quantity
        else:
            self.items[product.product_id] = CartItem(product, quantity)
        return True

    def remove_product(self, product_id: str) -> bool:
        if product_id in self.items:
            del self.items[product_id]
            return True
        return False

    def update_quantity(self, product_id: str, quantity: int) -> bool:
        if product_id in self.items:
            if quantity <= 0:
                return self.remove_product(product_id)
            self.items[product_id].quantity = quantity
            return True
        return False

    def total(self) -> float:
        return round(sum(item.subtotal() for item in self.items.values()), 2)

    def item_count(self) -> int:
        return sum(item.quantity for item in self.items.values())

    def clear(self):
        self.items = {}

    def convert_to_order(self) -> Optional[Order]:
        if not self.items:
            return None
        from .order import Order
        import uuid
        order = Order(
            order_id=str(uuid.uuid4()),
            customer=self.owner,
            items=list(self.items.values()),
        )
        self.clear()
        return order

    def to_dict(self) -> dict:
        return {
            "owner_id": self.owner.account_id,
            "items": [item.to_dict() for item in self.items.values()],
            "total": self.total(),
            "item_count": self.item_count(),
        }

    def __repr__(self):
        return f"<ShoppingCart owner={self.owner.username} items={self.item_count()} total=${self.total()}>"