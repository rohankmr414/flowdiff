from api import db
from lib import queue


def register(email, name):
    """POST /signup"""
    if db.find_user(email):
        return 409, {"error": "exists"}
    user = db.insert_user(email, name)
    queue.enqueue("welcome_email", {"user_id": user["id"]})
    db.commit()
    return 201, {"id": user["id"]}
