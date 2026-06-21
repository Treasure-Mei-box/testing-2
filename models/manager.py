"""
Manager - Singleton pattern. Central orchestrator: manages Products,
creates Reports, and processes Orders.
Accesses Invoice and Feedback indirectly via Order traversal
(avoids tight coupling — Riel Heuristic on dependency reduction).
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
        self.alerts: List[dict] = []

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
        order.update_status("processing")
        if not any(o.order_id == order.order_id for o in self.orders):
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
        """
        Compiles report data. Accesses Invoice and Feedback indirectly
        by traversing the Order collection (Manager --> Order in UML),
        avoiding redundant structural dependencies on Invoice/Feedback directly.
        """
        # Pre-calculate active units sold & category breakdown for the system
        product_sales = {p.name: 0 for p in self.products}
        category_sales = {}
        total_units_sold = 0
        
        for o in self.orders:
            if o.is_paid():
                for item in o.items:
                    product_sales[item.product.name] = product_sales.get(item.product.name, 0) + item.quantity
                    total_units_sold += item.quantity
                    
                    cat_id = item.product.category_id or "Uncategorized"
                    category_sales[cat_id] = round(category_sales.get(cat_id, 0.0) + item.subtotal(), 2)

        if report_type == "inventory":
            out_of_stock = [p for p in self.products if p.stock_quantity == 0]
            low_stock    = [p for p in self.products if 0 < p.stock_quantity <= 5]
            
            # KPI 3: Inventory turnover statistics (Units Sold vs. Average Inventory)
            current_total_stock = sum(p.stock_quantity for p in self.products)
            avg_inventory = current_total_stock + (total_units_sold / 2.0)
            global_turnover_ratio = round(total_units_sold / avg_inventory, 2) if avg_inventory > 0 else 0.0
            
            # Product level velocities
            turnover_details = []
            for p in self.products:
                p_sold = product_sales.get(p.name, 0)
                p_avg = p.stock_quantity + (p_sold / 2.0)
                p_turnover = round(p_sold / p_avg, 2) if p_avg > 0 else 0.0
                turnover_details.append({
                    "product_id": p.product_id,
                    "name": p.name,
                    "units_sold": p_sold,
                    "turnover_ratio": p_turnover,
                    "stock_left": p.stock_quantity
                })
                
            return {
                "total_products": len(self.products),
                "total_stock_units": sum(p.stock_quantity for p in self.products),
                "out_of_stock_count": len(out_of_stock),
                "low_stock_count": len(low_stock),
                "global_turnover_ratio": global_turnover_ratio,
                "turnover_details": turnover_details,
                "out_of_stock": [p.to_dict() for p in out_of_stock],
                "low_stock": [p.to_dict() for p in low_stock],
                "products": [p.to_dict() for p in self.products],
            }

        if report_type == "orders":
            status_map = {}
            for o in self.orders:
                status_map[o.status] = status_map.get(o.status, 0) + 1
            return {
                "total_orders": len(self.orders),
                "by_status": status_map,
                "orders": [o.to_dict() for o in self.orders],
            }

        if report_type == "sales":
            invoices = [o.invoice for o in self.orders if o.invoice]
            total_revenue = round(sum(inv.amount for inv in invoices if inv.is_paid), 2)
            paid_orders   = [o for o in self.orders if o.is_paid()]
            
            # KPI 1: Calculates top-selling and low-performing products
            sorted_sales = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)
            top_selling = [{"name": name, "qty_sold": qty} for name, qty in sorted_sales[:3]]
            low_performing = [{"name": name, "qty_sold": qty} for name, qty in sorted_sales[-3:]][::-1]
            
            return {
                "total_revenue": total_revenue,
                "total_paid_orders": len(paid_orders),
                "total_invoices": len(invoices),
                "average_order_value": round(
                    total_revenue / len(paid_orders) if paid_orders else 0, 2
                ),
                "top_selling": top_selling,
                "low_performing": low_performing,
                "category_sales": category_sales,  # KPI 2: Category sales breakdown
                "invoice_details": [inv.to_dict() for inv in invoices],
            }

        if report_type == "feedback":
            feedbacks = [o.feedback for o in self.orders if o.feedback]
            avg_rating = round(
                sum(f.rating for f in feedbacks) / len(feedbacks) if feedbacks else 0, 2
            )
            return {
                "total_feedback": len(feedbacks),
                "average_rating": avg_rating,
                "five_star": sum(1 for f in feedbacks if f.rating == 5),
                "four_star": sum(1 for f in feedbacks if f.rating == 4),
                "three_star": sum(1 for f in feedbacks if f.rating == 3),
                "two_star": sum(1 for f in feedbacks if f.rating == 2),
                "one_star": sum(1 for f in feedbacks if f.rating == 1),
                "feedbacks": [f.to_dict() for f in feedbacks],
            }

        if report_type == "support":
            all_tickets = []
            for o in self.orders:
                all_tickets.extend(o.support_tickets)
            resolved = [t for t in all_tickets if t.status == "resolved"]
            return {
                "total_tickets": len(all_tickets),
                "resolved": len(resolved),
                "open": sum(1 for t in all_tickets if t.status == "open"),
                "in_progress": sum(1 for t in all_tickets if t.status == "in_progress"),
                "resolution_rate": round(
                    len(resolved) / len(all_tickets) * 100 if all_tickets else 0, 1
                ),
            }

        return {"report_type": report_type, "data": "N/A"}
    
    def _orders_by_status(self) -> dict:
        result = {}
        for o in self.orders:
            result[o.status] = result.get(o.status, 0) + 1
        return result

    def to_dict(self) -> dict:
        return {
            "products": len(self.products),
            "orders": len(self.orders),
            "reports": len(self.reports),
        }

    def __repr__(self):
        return "<Manager (Singleton)>"
