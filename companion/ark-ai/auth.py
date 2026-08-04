"""Single-user identity resolution.

Ark_AI has no login system: every request is the same implicit local user.
This module just makes sure that user exists in the database and hands back
its id, so the rest of the app (settings, conversations, usage tracking) has
something to scope storage to.
"""
import secrets

from werkzeug.security import generate_password_hash

import db

DIRECT_ENTRY_USERNAME = "default"

_user_id = None


def get_user_id():
    """Returns the id of the single local user, creating it on first call.
    Cached in-process since it never changes after creation."""
    global _user_id
    if _user_id is not None:
        return _user_id
    user = db.get_user_by_username(DIRECT_ENTRY_USERNAME)
    if user is None:
        # password_hash is unused (no login flow checks it) but the column
        # is NOT NULL, so fill it with an unusable random value.
        password_hash = generate_password_hash(secrets.token_hex(32))
        _user_id = db.create_user(DIRECT_ENTRY_USERNAME, password_hash)
    else:
        _user_id = user["id"]
    return _user_id


def reset_cache():
    """Used by tests when they reset the database between cases."""
    global _user_id
    _user_id = None
