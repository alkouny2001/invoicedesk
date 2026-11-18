from datetime import datetime, timezone
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .auth import current_tenant
from .db import get_conn, init_db

app = FastAPI(title="InvoiceDesk", version="1.0.0")


@app.on_event("startup")
def startup():
    init_db()


# ---------- request models ----------

class ClientIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: str | None = None


class ItemIn(BaseModel):
    description: str = Field(min_length=1, max_length=300)
    quantity: int = Field(ge=1)
    unit_price_cents: int = Field(ge=0)


class InvoiceIn(BaseModel):
    client_id: int
    due_date: str | None = None
    items: list[ItemIn] = Field(min_length=1)


class StatusIn(BaseModel):
    status: Literal["draft", "sent", "paid"]


# ---------- helpers ----------

def month_start_utc() -> str:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()


def invoices_this_month(conn, tenant_id: int) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM invoices WHERE tenant_id = ? AND created_at >= ?",
        (tenant_id, month_start_utc()),
    ).fetchone()[0]


def load_invoice(conn, tenant_id: int, invoice_id: int) -> dict:
    # tenant_id is part of the WHERE clause, so another tenant's invoice is simply not found
    inv = conn.execute(
        "SELECT * FROM invoices WHERE id = ? AND tenant_id = ?",
        (invoice_id, tenant_id),
    ).fetchone()
    if inv is None:
        raise HTTPException(status_code=404, detail="invoice not found")
    items = conn.execute(
        "SELECT description, quantity, unit_price_cents FROM invoice_items WHERE invoice_id = ? ORDER BY id",
        (invoice_id,),
    ).fetchall()
    out = dict(inv)
    out.pop("tenant_id")
    out["items"] = [dict(i) for i in items]
    return out


# ---------- routes ----------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/me")
def me(tenant: dict = Depends(current_tenant)):
    with get_conn() as conn:
        used = invoices_this_month(conn, tenant["id"])
    return {
        "tenant": tenant["name"],
        "plan": tenant["plan_name"],
        "invoices_this_month": used,
        "monthly_invoice_limit": tenant["monthly_invoice_limit"],
    }


@app.post("/clients", status_code=201)
def create_client(body: ClientIn, tenant: dict = Depends(current_tenant)):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO clients (tenant_id, name, email) VALUES (?, ?, ?)",
            (tenant["id"], body.name, body.email),
        )
        return {"id": cur.lastrowid, "name": body.name, "email": body.email}


@app.get("/clients")
def list_clients(tenant: dict = Depends(current_tenant)):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, name, email FROM clients WHERE tenant_id = ? ORDER BY id",
            (tenant["id"],),
        ).fetchall()
    return [dict(r) for r in rows]


@app.post("/invoices", status_code=201)
def create_invoice(body: InvoiceIn, tenant: dict = Depends(current_tenant)):
    with get_conn() as conn:
        # lock the db for this transaction so two parallel requests can't both pass the limit check
        conn.execute("BEGIN IMMEDIATE")

        client = conn.execute(
            "SELECT id FROM clients WHERE id = ? AND tenant_id = ?",
            (body.client_id, tenant["id"]),
        ).fetchone()
        if client is None:
            raise HTTPException(status_code=404, detail="client not found")

        used = invoices_this_month(conn, tenant["id"])
        limit = tenant["monthly_invoice_limit"]
        if used >= limit:
            return JSONResponse(
                status_code=402,
                content={
                    "error": "plan_limit_reached",
                    "detail": f"{tenant['plan_name']} plan allows {limit} invoices per month",
                    "used": used,
                    "limit": limit,
                },
            )

        total = sum(i.quantity * i.unit_price_cents for i in body.items)
        number = f"INV-{used + 1:04d}"
        created = datetime.now(timezone.utc).isoformat()
        cur = conn.execute(
            """INSERT INTO invoices (tenant_id, client_id, number, status, due_date, total_cents, created_at)
               VALUES (?, ?, ?, 'draft', ?, ?, ?)""",
            (tenant["id"], body.client_id, number, body.due_date, total, created),
        )
        inv_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO invoice_items (invoice_id, description, quantity, unit_price_cents) VALUES (?, ?, ?, ?)",
            [(inv_id, i.description, i.quantity, i.unit_price_cents) for i in body.items],
        )
        return load_invoice(conn, tenant["id"], inv_id)


@app.get("/invoices")
def list_invoices(tenant: dict = Depends(current_tenant)):
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT id, client_id, number, status, due_date, total_cents, created_at
               FROM invoices WHERE tenant_id = ? ORDER BY id""",
            (tenant["id"],),
        ).fetchall()
    return [dict(r) for r in rows]


@app.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: int, tenant: dict = Depends(current_tenant)):
    with get_conn() as conn:
        return load_invoice(conn, tenant["id"], invoice_id)


@app.patch("/invoices/{invoice_id}/status")
def update_status(invoice_id: int, body: StatusIn, tenant: dict = Depends(current_tenant)):
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE invoices SET status = ? WHERE id = ? AND tenant_id = ?",
            (body.status, invoice_id, tenant["id"]),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="invoice not found")
        return load_invoice(conn, tenant["id"], invoice_id)
