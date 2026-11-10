import gateway

_seen: dict[str, str] = {}


def charge(customer_id: str, amount: float, idempotency_key: str) -> str:
    if idempotency_key in _seen:
        return _seen[idempotency_key]
    charge_id = gateway.charge(customer_id, amount)
    _seen[idempotency_key] = charge_id
    return charge_id


def refund(charge_id: str) -> None:
    gateway.refund(charge_id)
