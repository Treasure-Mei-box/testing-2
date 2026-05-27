"""
Product model - managed by Admin/Manager, contained in Catalogue and Category.
"""
from typing import List, Optional


class Product:
    """A sellable item in the store."""

    def __init__(self, product_id: str, name: str, description: str,
                 price: float, stock_quantity: int, category_id: Optional[str] = None):
        self.product_id = product_id
        self.name = name
        self.description = description
        self.price = price
        self.stock_quantity = stock_quantity
        self.category_id = category_id
        self.image_url: str = ""

    def is_available(self) -> bool:
        return self.stock_quantity > 0

    def reduce_stock(self, quantity: int) -> bool:
        if self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            return True
        return False

    def restock(self, quantity: int):
        self.stock_quantity += quantity

    def apply_discount(self, percent: float) -> float:
        """Return discounted price without modifying the original."""
        return round(self.price * (1 - percent / 100), 2)

    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "stock_quantity": self.stock_quantity,
            "category_id": self.category_id,
            "is_available": self.is_available(),
            "image_url": self.image_url,
        }

    def __repr__(self):
        return f"<Product {self.product_id}: {self.name} (${self.price})>"