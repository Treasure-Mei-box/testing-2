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
        self.is_active: bool = True  # Default to active

    def is_available(self) -> bool:
        return self.stock_quantity > 0

    def reduce_stock(self, quantity: int) -> bool:
        if self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            
            # Low Stock Alert Check: Trigger warning if stock falls to 5 or fewer units (CRC 4.6)
            if self.stock_quantity <= 10:
                from .manager import Manager
                import uuid
                from datetime import datetime
                mgr = Manager.get_instance()
                
                # Avoid flooding: check if there is already an active unread alert for this product
                if not any(a.get("product_id") == self.product_id and not a.get("read") for a in mgr.alerts):
                    mgr.alerts.append({
                        "alert_id": str(uuid.uuid4())[:8].upper(),
                        "product_id": self.product_id,
                        "name": self.name,
                        "image_url": self.image_url,
                        "stock_quantity": self.stock_quantity,
                        "timestamp": datetime.now().strftime("%I:%M %p"),
                        "read": False
                    })
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