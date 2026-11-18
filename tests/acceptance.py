"""Acceptance checks for InvoiceDesk. Uses only the Python standard library.

Usage:  python tests/acceptance.py [base_url]
Run `docker exec invoicedesk python -m app.seed` first so both tenants start empty.
Writes evidence/http-log.md (every request and response) and evidence/results.md.
"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
TOKEN_A = "tok_tenantA_acme_test"   # Acme Design Studio, Free plan (3 invoices/month)
TOKEN_B = "tok_tenantB_birch_test"  # Birch Plumbing Ltd, Pro plan (10 invoices/month)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence")
os.makedirs(OUT_DIR, exist_ok=True)
log_lines = []
results = []


def call(method, path, token, body=None, who=""):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            status, payload = r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        status, payload = e.code, e.read().decode()
    parsed = json.loads(payload) if payload else None

    log_lines.append(f"### {who}: {method} {path}\n")
    log_lines.append(f"Authorization: Bearer {token}\n")
    if body is not None:
        log_lines.append("```json\n" + json.dumps(body, indent=2) + "\n```\n")
    log_lines.append(f"Response: **{status}**\n")
    log_lines.append("```json\n" + json.dumps(parsed, indent=2) + "\n```\n")
    return status, parsed


def record(check, step, expected, actual, ok):
    results.append((check, step, expected, actual, "PASS" if ok else "FAIL"))
    print(f"[{'PASS' if ok else 'FAIL'}] {check}: {step} -> {actual}")


def first_client(token, who):
    _, clients = call("GET", "/clients", token, who=who)
    return clients[0]["id"]


def new_invoice(token, client_id, who, n=1):
    return call("POST", "/invoices", token, {
        "client_id": client_id,
        "due_date": "2026-12-31",
        "items": [{"description": f"Service batch {n}", "quantity": 2, "unit_price_cents": 15000}],
    }, who=who)


# ---------------- Check 1: normal use ----------------
log_lines.append("## Check 1: Normal use\n")
for token, who in ((TOKEN_A, "Tenant A"), (TOKEN_B, "Tenant B")):
    cid = first_client(token, who)
    s, inv = new_invoice(token, cid, who)
    record("Normal use", f"{who} creates invoice", "201", s, s == 201)
    s, got = call("GET", f"/invoices/{inv['id']}", token, who=who)
    record("Normal use", f"{who} reads own invoice", "200, same number", f"{s}, {got.get('number')}",
           s == 200 and got["number"] == inv["number"])
    s, upd = call("PATCH", f"/invoices/{inv['id']}/status", token, {"status": "sent"}, who=who)
    record("Normal use", f"{who} marks invoice sent", "200, status=sent", f"{s}, {upd.get('status')}",
           s == 200 and upd["status"] == "sent")
    s, lst = call("GET", "/invoices", token, who=who)
    record("Normal use", f"{who} lists invoices", "200, 1 invoice", f"{s}, {len(lst)} invoice(s)",
           s == 200 and len(lst) == 1)

# ---------------- Check 2: tenant isolation ----------------
log_lines.append("## Check 2: Tenant isolation\n")
cid_b = first_client(TOKEN_B, "Tenant B")
s, b_inv = new_invoice(TOKEN_B, cid_b, "Tenant B", n=2)
record("Tenant isolation", "B creates invoice", "201", s, s == 201)
s, b_before = call("GET", f"/invoices/{b_inv['id']}", TOKEN_B, who="Tenant B")
record("Tenant isolation", "B reads it", "200", s, s == 200)

s, body = call("GET", f"/invoices/{b_inv['id']}", TOKEN_A, who="Tenant A")
record("Tenant isolation", "A reads B's invoice", "404, no B data", f"{s}, {body}",
       s == 404 and "number" not in (body or {}))
s, body = call("PATCH", f"/invoices/{b_inv['id']}/status", TOKEN_A, {"status": "paid"}, who="Tenant A")
record("Tenant isolation", "A tries to mark B's invoice paid", "404", s, s == 404)
s, body = new_invoice(TOKEN_A, cid_b, "Tenant A", n=99)
record("Tenant isolation", "A bills B's client id", "404 client not found", f"{s}, {body}", s == 404)
s, a_list = call("GET", "/invoices", TOKEN_A, who="Tenant A")
record("Tenant isolation", "A's list has no B invoices", "B's id absent", [i["id"] for i in a_list],
       b_inv["id"] not in [i["id"] for i in a_list])

s, b_after = call("GET", f"/invoices/{b_inv['id']}", TOKEN_B, who="Tenant B")
record("Tenant isolation", "B's invoice still intact", "200, identical to before",
       f"{s}, identical={b_after == b_before}", s == 200 and b_after == b_before)

# ---------------- Check 3: plan limit ----------------
log_lines.append("## Check 3: Plan limit\n")
s, me_a = call("GET", "/me", TOKEN_A, who="Tenant A")
limit_a = me_a["monthly_invoice_limit"]
cid_a = first_client(TOKEN_A, "Tenant A")
while me_a["invoices_this_month"] < limit_a:
    s, _ = new_invoice(TOKEN_A, cid_a, "Tenant A", n=me_a["invoices_this_month"] + 1)
    s, me_a = call("GET", "/me", TOKEN_A, who="Tenant A")
record("Plan limit", f"A fills Free allowance", f"{limit_a}/{limit_a}",
       f"{me_a['invoices_this_month']}/{limit_a}", me_a["invoices_this_month"] == limit_a)

count_before = len(call("GET", "/invoices", TOKEN_A, who="Tenant A")[1])
s, body = new_invoice(TOKEN_A, cid_a, "Tenant A", n=limit_a + 1)
record("Plan limit", f"A creates invoice #{limit_a + 1}", "402 plan_limit_reached",
       f"{s}, {body.get('error')}", s == 402 and body.get("error") == "plan_limit_reached")
count_after = len(call("GET", "/invoices", TOKEN_A, who="Tenant A")[1])
record("Plan limit", "A's invoice count unchanged", f"{count_before}", count_after, count_after == count_before)

s, me_b = call("GET", "/me", TOKEN_B, who="Tenant B")
while me_b["invoices_this_month"] < limit_a + 1:
    s, last = new_invoice(TOKEN_B, cid_b, "Tenant B", n=me_b["invoices_this_month"] + 1)
    s_me, me_b = call("GET", "/me", TOKEN_B, who="Tenant B")
record("Plan limit", f"B creates invoice #{limit_a + 1} on Pro", "201",
       f"{s}, {me_b['invoices_this_month']}/{me_b['monthly_invoice_limit']}", s == 201)

# ---------------- write evidence ----------------
with open(os.path.join(OUT_DIR, "http-log.md"), "w", encoding="utf-8") as f:
    f.write(f"# HTTP log against {BASE}\n\n" + "\n".join(log_lines))

with open(os.path.join(OUT_DIR, "results.md"), "w", encoding="utf-8") as f:
    f.write(f"# Acceptance results ({BASE})\n\n")
    f.write("| Check | Step | Expected | Actual | Result |\n|---|---|---|---|---|\n")
    for row in results:
        f.write("| " + " | ".join(str(c).replace("|", "/") for c in row) + " |\n")

failed = [r for r in results if r[4] == "FAIL"]
print(f"\n{len(results) - len(failed)}/{len(results)} steps passed. Evidence in evidence/")
sys.exit(1 if failed else 0)
