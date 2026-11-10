from dataclasses import dataclass, field

_DB: dict[str, "Order"] = {}


@dataclass
class Order:
    id: str
    customer_id: str
    items: list[dict]
    total: float
    status: str = "new"
    discount: float = 0.0
    charge_id: str | None = None


def validate_order(payload: dict) -> Order:
    if not payload.get("items"):
        raise ValueError("order has no items")
    total = sum(i["price"] * i["qty"] for i in payload["items"])
    return Order(id=payload["id"], customer_id=payload["customer_id"], items=payload["items"], total=total)


def save_order(order: Order) -> None:
    _DB[order.id] = order


def load_order(order_id: str) -> Order:
    return _DB[order_id]
