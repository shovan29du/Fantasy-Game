"""
AiChat Pro — Core Security
bcrypt password hashing, login / register, password reset with security question,
session management, auto-lock.
"""
from __future__ import annotations
import hashlib
from datetime import datetime
from core.storage import get_conn, now_iso

try:
    import bcrypt
except ImportError:
    bcrypt = None


def _hash_pw(password: str) -> str:
    if bcrypt:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    return hashlib.sha256(password.encode()).hexdigest()


def _check_pw(password: str, stored: str) -> bool:
    if bcrypt:
        try:
            return bcrypt.checkpw(password.encode(), stored.encode())
        except Exception:
            return False
    return hashlib.sha256(password.encode()).hexdigest() == stored


def register_user(username: str, password: str,
                  security_q: str = "", security_a: str = "",
                  role: str = "user") -> bool:
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO app_users (username, password_hash, security_q, security_a_hash, role, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (username, _hash_pw(password), security_q,
             _hash_pw(security_a) if security_a else "", role, now_iso())
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def verify_user(username: str, password: str) -> bool:
    conn = get_conn()
    row = conn.execute("SELECT password_hash FROM app_users WHERE username=?",
                       (username,)).fetchone()
    conn.close()
    if not row:
        return False
    return _check_pw(password, row["password_hash"])


def reset_password(username: str, security_a: str, new_password: str) -> bool:
    conn = get_conn()
    row = conn.execute("SELECT security_a_hash FROM app_users WHERE username=?",
                       (username,)).fetchone()
    if not row:
        conn.close()
        return False
    if not _check_pw(security_a, row["security_a_hash"]):
        conn.close()
        return False
    conn.execute("UPDATE app_users SET password_hash=? WHERE username=?",
                 (_hash_pw(new_password), username))
    conn.commit()
    conn.close()
    return True


def user_exists() -> bool:
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) as cnt FROM app_users").fetchone()
    conn.close()
    return row["cnt"] > 0


def list_users():
    conn = get_conn()
    rows = conn.execute("SELECT username, role, created_at FROM app_users").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_user(username):
    conn = get_conn()
    r = conn.execute("SELECT COUNT(*) as c FROM app_users WHERE username=?", (username,)).fetchone()
    if not r or r["c"]==0: conn.close(); return False
    conn.execute("DELETE FROM app_users WHERE username=?", (username,)); conn.commit(); conn.close(); return True
