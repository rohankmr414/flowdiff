STOCK: dict[str, int] = {}


def reserve_stock(order) -> None:
    for item in order.items:
        if STOCK.get(item["sku"], 0) < item["qty"]:
            raise RuntimeError(f"out of stock: {item['sku']}")
        STOCK[item["sku"]] -= item["qty"]


def release_stock(order) -> None:
    for item in order.items:
        STOCK[item["sku"]] = STOCK.get(item["sku"], 0) + item["qty"]
