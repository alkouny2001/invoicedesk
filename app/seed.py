"""Reset the database and load two test tenants with synthetic data.

Run inside the container:  docker exec invoicedesk python -m app.seed
"""
import os

from .auth import hash_token
from .db import DB_PATH, get_conn, init_db

PLANS = [
    ("free", "Free", 3),
    ("pro", "Pro", 10),
]

TENANTS = [
    # name, plan, token, synthetic clients
    ("Acme Design Studio", "free", "tok_tenantA_acme_test",
     [("Northwind Cafe", "billing@northwind.test"), ("Lumen Books", "accounts@lumen.test")]),
    ("Birch Plumbing Ltd", "pro", "tok_tenantB_birch_test",
     [("Harbor Apartments", "office@harbor.test"), ("Greenleaf School", "finance@greenleaf.test")]),
]


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    with get_conn() as conn:
        conn.executemany("INSERT INTO plans (code, name, monthly_invoice_limit) VALUES (?, ?, ?)", PLANS)
        for name, plan, token, clients in TENANTS:
            tid = conn.execute("INSERT INTO tenants (name, plan_code) VALUES (?, ?)", (name, plan)).lastrowid
            conn.execute(
                "INSERT INTO api_tokens (token_hash, tenant_id, label) VALUES (?, ?, ?)",
                (hash_token(token), tid, "test token"),
            )
            conn.executemany(
                "INSERT INTO clients (tenant_id, name, email) VALUES (?, ?, ?)",
                [(tid, c, e) for c, e in clients],
            )
    print("Database reset. Tenants:")
    for name, plan, token, _ in TENANTS:
        print(f"  {name:<20} plan={plan:<5} token={token}")


if __name__ == "__main__":
    main()
