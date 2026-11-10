"""Separate process: `python -m worker.email_worker`."""
import time

from api import db
from lib import mailer, queue

MAX_ATTEMPTS = 3


def render_welcome(user):
    return f"Hi {user['name']}, welcome aboard!"


def handle_welcome(job):
    user = db.get_user(job["user_id"])
    if user is None:
        return
    for attempt in range(MAX_ATTEMPTS):
        try:
            mailer.send(user["email"], "Welcome", render_welcome(user))
            return
        except mailer.SendError:
            time.sleep(2 ** attempt)


def run():
    for job in queue.consume("welcome_email"):
        handle_welcome(job)
        queue.ack(job)


if __name__ == "__main__":
    run()
