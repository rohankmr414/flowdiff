from inventory import release_stock, reserve_stock
from orders import load_order, save_order, validate_order
from payments import charge, refund
from pricing import apply_coupon


def create_order(req):
    order = validate_order(req.json)
    order = apply_coupon(order, req.json.get("coupon"))
    reserve_stock(order)
    order.charge_id = charge(order.customer_id, order.total, idempotency_key=order.id)
    save_order(order)
    return {"id": order.id, "total": order.total, "discount": order.discount}


def cancel_order(req):
    order = load_order(req.params["id"])
    release_stock(order)
    if order.charge_id:
        refund(order.charge_id)
    order.status = "cancelled"
    save_order(order)
    return {"status": order.status}
