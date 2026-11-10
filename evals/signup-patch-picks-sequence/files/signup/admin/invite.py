from api import db
from api.signup import render_welcome
from lib import mailer


def resend_welcome(email):
    """Admin console button."""
    user = db.find_user(email)
    if user:
        mailer.send(user["email"], "Welcome", render_welcome(user))
