# Acceptance results (http://localhost:8000)

| Check | Step | Expected | Actual | Result |
|---|---|---|---|---|
| Normal use | Tenant A creates invoice | 201 | 201 | PASS |
| Normal use | Tenant A reads own invoice | 200, same number | 200, INV-0001 | PASS |
| Normal use | Tenant A marks invoice sent | 200, status=sent | 200, sent | PASS |
| Normal use | Tenant A lists invoices | 200, 1 invoice | 200, 1 invoice(s) | PASS |
| Normal use | Tenant B creates invoice | 201 | 201 | PASS |
| Normal use | Tenant B reads own invoice | 200, same number | 200, INV-0001 | PASS |
| Normal use | Tenant B marks invoice sent | 200, status=sent | 200, sent | PASS |
| Normal use | Tenant B lists invoices | 200, 1 invoice | 200, 1 invoice(s) | PASS |
| Tenant isolation | B creates invoice | 201 | 201 | PASS |
| Tenant isolation | B reads it | 200 | 200 | PASS |
| Tenant isolation | A reads B's invoice | 404, no B data | 404, {'detail': 'invoice not found'} | PASS |
| Tenant isolation | A tries to mark B's invoice paid | 404 | 404 | PASS |
| Tenant isolation | A bills B's client id | 404 client not found | 404, {'detail': 'client not found'} | PASS |
| Tenant isolation | A's list has no B invoices | B's id absent | [1] | PASS |
| Tenant isolation | B's invoice still intact | 200, identical to before | 200, identical=True | PASS |
| Plan limit | A fills Free allowance | 3/3 | 3/3 | PASS |
| Plan limit | A creates invoice #4 | 402 plan_limit_reached | 402, plan_limit_reached | PASS |
| Plan limit | A's invoice count unchanged | 3 | 3 | PASS |
| Plan limit | B creates invoice #4 on Pro | 201 | 201, 4/10 | PASS |
