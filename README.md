# InvoiceDesk

A small multi-tenant invoicing API. Small businesses keep their clients and invoices here and track whether each invoice is draft, sent or paid. Two test organisations share one running container and one SQLite database, and each one only ever sees its own records.

Built with FastAPI and SQLite. All data is synthetic.

## Test tenants

| Tenant | Organisation | Plan | Invoices per month | API token |
|---|---|---|---|---|
| A | Acme Design Studio | Free | 3 | `tok_tenantA_acme_test` |
| B | Birch Plumbing Ltd | Pro | 10 | `tok_tenantB_birch_test` |

The server works out the tenant from the token. Requests never carry a tenant id.

## Build and run

You need Docker and Python 3 (only for the test script).

```bash
git clone <this repo>
cd invoicedesk

docker build -t invoicedesk .
docker run -d --name invoicedesk -p 8000:8000 -v invoicedesk-data:/data invoicedesk
```

Check it is up:

```bash
curl http://localhost:8000/health
```

## Initialise test data

This wipes the database and creates both tenants, their plans, tokens and two synthetic clients each.

```bash
docker exec invoicedesk python -m app.seed
```

Run it again any time you want a clean start.

## Making requests as each tenant

Every call except `/health` needs `Authorization: Bearer <token>`.

```bash
# who am I, which plan, how much of the allowance is used
curl -H "Authorization: Bearer tok_tenantA_acme_test" http://localhost:8000/me

# list my clients
curl -H "Authorization: Bearer tok_tenantA_acme_test" http://localhost:8000/clients

# create an invoice (use a client id from the list above)
curl -X POST http://localhost:8000/invoices \
  -H "Authorization: Bearer tok_tenantA_acme_test" \
  -H "Content-Type: application/json" \
  -d '{"client_id": 1, "due_date": "2026-12-31", "items": [{"description": "Logo design", "quantity": 1, "unit_price_cents": 45000}]}'

# read, list, update status
curl -H "Authorization: Bearer tok_tenantA_acme_test" http://localhost:8000/invoices/1
curl -H "Authorization: Bearer tok_tenantA_acme_test" http://localhost:8000/invoices
curl -X PATCH http://localhost:8000/invoices/1/status \
  -H "Authorization: Bearer tok_tenantA_acme_test" \
  -H "Content-Type: application/json" \
  -d '{"status": "sent"}'
```

For tenant B swap in `tok_tenantB_birch_test`. On Windows PowerShell use `curl.exe` and escape the inner quotes, or just use the interactive docs at http://localhost:8000/docs (click Authorize and paste the token).

## Endpoints

| Method | Path | What it does |
|---|---|---|
| GET | /health | Liveness check, no auth |
| GET | /me | Tenant name, plan, invoices used this month and the limit |
| POST | /clients | Add a client |
| GET | /clients | List own clients |
| POST | /invoices | Create an invoice with line items (counts against the plan) |
| GET | /invoices | List own invoices |
| GET | /invoices/{id} | Read one invoice with its items |
| PATCH | /invoices/{id}/status | Set status to draft, sent or paid |

## How isolation works

`app/auth.py` hashes the bearer token with SHA-256 and looks it up in `api_tokens`, which maps to a tenant. That tenant id is passed into every route. Every SQL query on clients and invoices has `tenant_id = ?` in its WHERE clause, including the update. When an invoice exists but belongs to someone else the query finds nothing and the API returns `404 invoice not found`, the same as for an id that doesn't exist, so tenant A can't even confirm that B's invoice is there. Creating an invoice also checks that the client id belongs to the caller.

## How the plan limit works

Creating an invoice is the action that uses the allowance. Before inserting, the server counts the tenant's invoices created since the first day of the current month (UTC) and compares it with the plan's `monthly_invoice_limit`. The check and the insert run inside one `BEGIN IMMEDIATE` transaction so two parallel requests can't both slip past the limit. At the limit the server returns:

```json
HTTP 402
{"error": "plan_limit_reached", "detail": "Free plan allows 3 invoices per month", "used": 3, "limit": 3}
```

Nothing is written in that case.

## Running the acceptance checks

With the container running and freshly seeded:

```bash
docker exec invoicedesk python -m app.seed
python tests/acceptance.py
```

The script uses only the standard library. It runs the three checks (normal use, tenant isolation, plan limit), prints PASS/FAIL per step and writes two files:

- `evidence/results.md` with expected vs actual for every step
- `evidence/http-log.md` with every request and response

## Project layout

```
app/
  main.py    routes, plan limit check
  auth.py    token -> tenant
  db.py      SQLite schema and connection
  seed.py    resets DB and loads test tenants
tests/
  acceptance.py
Dockerfile
requirements.txt
```
