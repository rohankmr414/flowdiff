"""Thin client for the external mail provider. send() is not idempotent."""
import provider_sdk


class SendError(Exception):
    pass


def send(to, subject, body):
    try:
        provider_sdk.deliver(to=to, subject=subject, body=body, timeout=5)
    except provider_sdk.Timeout as e:
        raise SendError(str(e))
