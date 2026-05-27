"""
Manager - Singleton pattern. Central orchestrator: manages Products,
creates Reports, and processes Orders.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
import uuid
from datetime import datetime

if TYPE_CHECKING:
    from .product import Product
    from .order import Order
    from .report import Report


class Manager:
    """
    Singleton manager that oversees products, orders, and reporting.
    Implements the Singleton design pattern.
    """
    _instance: Optional[Manager] = None

    def __init__(self):
        if Manager._instance is not None:
            raise RuntimeError("Use Manager.get_instance() — Manager is a Singleton.")
        self.products: List[Product] = []
        self.orders: List[Order] = []
        self.reports: List[Report] = []

    @classmethod
    def get_instance(cls) -> Manager:
        if cls._instance is None:
            cls._instance = Manager()
        return cls._instance

    @classmethod
    def reset(cls):
        cls._instance = None

    def manage_product(self, product: Product):
        if not any(p.product_id == product.product_id for p in self.products):
            self.products.append(product)

    def remove_product(self, product_id: str) -> bool:
        before = len(self.products)
        self.products = [p for p in self.products if p.product_id != product_id]
        return len(self.products) < before

    def process_order(self, order: Order) -> bool:
        order.status = "processing"
        self.orders.append(order)
        return True

    def create_report(self, report_type: str, requested_by=None) -> Report:
        from .report import Report
        report = Report(
            report_id=str(uuid.uuid4()),
            report_type=report_type,
            generated_at=datetime.now(),
            data=self._compile_report_data(report_type),
            requested_by=requested_by,
        )
        self.reports.append(report)
        return report

    def _compile_report_data(self, report_type: str) -> dict:
        if report_type == "inventory":
            return {
                "total_products": len(self.products),
                "total_stock": sum(p.stock_quantity for p in self.products),
                "products": [p.to_dict() for p in self.products],
            }
        if report_type == "orders":
            return {
                "total_orders": len(self.orders),
                "orders": [o.to_dict() for o in self.orders],
            }
        return {"report_type": report_type, "data": "N/A"}

    def to_dict(self) -> dict:
        return {
            "products": len(self.products),
            "orders": len(self.orders),
            "reports": len(self.reports),
        }

    def __repr__(self):
        return "<Manager (Singleton)>"