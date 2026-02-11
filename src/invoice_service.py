from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

@dataclass
class LineItem:
    sku: str
    category: str
    unit_price: float
    qty: int
    fragile: bool = False

@dataclass
class Invoice:
    invoice_id: str
    customer_id: str
    country: str
    membership: str
    coupon: Optional[str]
    items: List[LineItem]

class InvoiceService:
    def __init__(self) -> None:
        self._coupon_rate: Dict[str, float] = {
            "WELCOME10": 0.10,
            "VIP20": 0.20,
            "STUDENT5": 0.05
        }

    def _validate(self, inv: Invoice) -> List[str]:
        problems: List[str] = []
        if inv is None:
            problems.append("Invoice is missing")
            return problems
        if not inv.invoice_id:
            problems.append("Missing invoice_id")
        if not inv.customer_id:
            problems.append("Missing customer_id")
        if not inv.items:
            problems.append("Invoice must contain items")
        for it in inv.items:
            if not it.sku:
                problems.append("Item sku is missing")
            if it.qty <= 0:
                problems.append(f"Invalid qty for {it.sku}")
            if it.unit_price < 0:
                problems.append(f"Invalid price for {it.sku}")
            if it.category not in ("book", "food", "electronics", "other"):
                problems.append(f"Unknown category for {it.sku}")
        return problems

    def compute_total(self, inv: Invoice) -> Tuple[float, List[str]]:
        warnings: List[str] = []
        problems = self._validate(inv)
        if problems:
            raise ValueError("; ".join(problems))

        subtotal = sum(it.unit_price * it.qty for it in inv.items)
        fragile_fee = sum(5.0 * it.qty for it in inv.items if it.fragile)

        
        shipping_rules = {"TH": 500, "JP": 4000, "US": 100}
        threshold = shipping_rules.get(inv.country, 200)
        shipping_costs = {"TH": 60, "JP": 600, "US": 15, "DEFAULT": 25}
        
        shipping = 0.0
        if subtotal < threshold:
            shipping = shipping_costs.get(inv.country if inv.country in shipping_costs else "DEFAULT")
        
        
        discount = 0.0
        if inv.membership == "gold":
            discount = subtotal * 0.03
        elif inv.membership == "platinum":
            discount = subtotal * 0.05
        elif subtotal > 3000:
            discount = 20.0

        
        if inv.coupon and inv.coupon.strip() in self._coupon_rate:
            discount += subtotal * self._coupon_rate[inv.coupon.strip()]
        elif inv.coupon:
            warnings.append("Unknown coupon")

        
        tax_rates = {"TH": 0.07, "JP": 0.10, "US": 0.08}
        tax = (subtotal - discount) * tax_rates.get(inv.country, 0.05)

        total = max(0, subtotal + shipping + fragile_fee + tax - discount)
        
        if subtotal > 10000 and inv.membership not in ("gold", "platinum"):
            warnings.append("Consider membership upgrade")

        return total, warnings