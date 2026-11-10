"""Thin client for the message broker. At-least-once delivery; unacked jobs are redelivered."""
import broker_sdk


def enqueue(topic, payload):
    broker_sdk.publish(topic, payload)


def consume(topic):
    yield from broker_sdk.subscribe(topic)


def ack(job):
    broker_sdk.ack(job)
