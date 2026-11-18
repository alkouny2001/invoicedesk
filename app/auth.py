import hashlib

from fastapi import Header, HTTPException

from .db import get_conn


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def current_tenant(authorization: str | None = Header(default=None)) -> dict:
    """Resolve the tenant from the bearer token. The client never sends a tenant id."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing or malformed bearer token")
    token = authorization.removeprefix("Bearer ").strip()

    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT t.id, t.name, t.plan_code, p.name AS plan_name, p.monthly_invoice_limit
            FROM api_tokens k
            JOIN tenants t ON t.id = k.tenant_id
            JOIN plans p ON p.code = t.plan_code
            WHERE k.token_hash = ?
            """,
            (hash_token(token),),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=401, detail="invalid token")
    return dict(row)
