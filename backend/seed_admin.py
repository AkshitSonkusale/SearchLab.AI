import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from app.db import execute_query
from app.auth import get_password_hash

def seed():
    print("Seeding demo accounts...")
    accounts = [
        ("Demo Admin", "admin@demo.com", "admin1234", "admin"),
        ("Demo User", "user@demo.com", "user1234", "user")
    ]

    for name, email, password, role in accounts:
        existing = execute_query("SELECT id FROM users WHERE email = %s", (email.lower(),), fetch_one=True)
        if not existing:
            pwd_hash = get_password_hash(password)
            execute_query(
                """
                INSERT INTO users (name, email, password_hash, role, active, created_at, last_active_at)
                VALUES (%s, %s, %s, %s, true, now(), now())
                """,
                (name, email.lower(), pwd_hash, role)
            )
            print(f"Created account: {email} ({role})")
        else:
            print(f"Account {email} already exists.")

    print("Demo accounts ready!")

if __name__ == "__main__":
    seed()
