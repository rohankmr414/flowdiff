COUPONS = {"WELCOME10": 0.10, "VIP25": 0.25}


class InvalidCoupon(Exception):
    pass


def apply_coupon(order, code: str | None):
    if not code:
        return order
    rate = COUPONS.get(code.upper())
    if rate is None:
        raise InvalidCoupon(code)
    order.discount = round(order.total * rate, 2)
    order.total = round(order.total - order.discount, 2)
    return order
