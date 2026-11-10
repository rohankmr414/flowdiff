_users = {}
_pending = {}


def find_user(email):
    return next((u for u in _users.values() if u["email"] == email), None)


def insert_user(email, name):
    user = {"id": len(_users) + len(_pending) + 1, "email": email, "name": name}
    _pending[user["id"]] = user
    return user


def commit():
    _users.update(_pending)
    _pending.clear()


def get_user(user_id):
    return _users.get(user_id)
