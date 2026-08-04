"""User registration / login / password reset CRUD (core/security.py)."""
from core.security import (
    register_user, verify_user, reset_password, user_exists, list_users, delete_user,
)


def test_user_lifecycle(temp_db):
    assert user_exists() is False

    assert register_user("alice", "hunter22", "pet name?", "fluffy", role="admin") is True
    assert user_exists() is True

    assert verify_user("alice", "hunter22") is True
    assert verify_user("alice", "wrong-password") is False
    assert verify_user("nobody", "whatever") is False

    users = list_users()
    assert any(u["username"] == "alice" and u["role"] == "admin" for u in users)

    assert reset_password("alice", "fluffy", "newpass123") is True
    assert verify_user("alice", "newpass123") is True
    assert verify_user("alice", "hunter22") is False

    assert reset_password("alice", "wrong-answer", "irrelevant") is False

    assert delete_user("alice") is True
    assert user_exists() is False


def test_register_duplicate_username_fails(temp_db):
    assert register_user("bob", "password1") is True
    assert register_user("bob", "password2") is False
