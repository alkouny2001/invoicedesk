# HTTP log against http://localhost:8000

## Check 1: Normal use

### Tenant A: GET /clients

Authorization: Bearer tok_tenantA_acme_test

Response: **200**

```json
[
  {
    "id": 1,
    "name": "Northwind Cafe",
    "email": "billing@northwind.test"
  },
  {
    "id": 2,
    "name": "Lumen Books",
    "email": "accounts@lumen.test"
  }
]
```

### Tenant A: POST /invoices

Authorization: Bearer tok_tenantA_acme_test

```json
{
  "client_id": 1,
  "due_date": "2026-12-31",
  "items": [
    {
      "description": "Service batch 1",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

Response: **201**

```json
{
  "id": 1,
  "client_id": 1,
  "number": "INV-0001",
  "status": "draft",
  "due_date": "2026-12-31",
  "total_cents": 30000,
  "created_at": "2026-11-18T14:30:19.202695+00:00",
  "items": [
    {
      "description": "Service batch 1",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

### Tenant A: GET /invoices/1

Authorization: Bearer tok_tenantA_acme_test

Response: **200**

```json
{
  "id": 1,
  "client_id": 1,
  "number": "INV-0001",
  "status": "draft",
  "due_date": "2026-12-31",
  "total_cents": 30000,
  "created_at": "2026-11-18T14:30:19.202695+00:00",
  "items": [
    {
      "description": "Service batch 1",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

### Tenant A: PATCH /invoices/1/status

Authorization: Bearer tok_tenantA_acme_test

```json
{
  "status": "sent"
}
```

Response: **200**

```json
{
  "id": 1,
  "client_id": 1,
  "number": "INV-0001",
  "status": "sent",
  "due_date": "2026-12-31",
  "total_cents": 30000,
  "created_at": "2026-11-18T14:30:19.202695+00:00",
  "items": [
    {
      "description": "Service batch 1",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

### Tenant A: GET /invoices

Authorization: Bearer tok_tenantA_acme_test

Response: **200**

```json
[
  {
    "id": 1,
    "client_id": 1,
    "number": "INV-0001",
    "status": "sent",
    "due_date": "2026-12-31",
    "total_cents": 30000,
    "created_at": "2026-11-18T14:30:19.202695+00:00"
  }
]
```

### Tenant B: GET /clients

Authorization: Bearer tok_tenantB_birch_test

Response: **200**

```json
[
  {
    "id": 3,
    "name": "Harbor Apartments",
    "email": "office@harbor.test"
  },
  {
    "id": 4,
    "name": "Greenleaf School",
    "email": "finance@greenleaf.test"
  }
]
```

### Tenant B: POST /invoices

Authorization: Bearer tok_tenantB_birch_test

```json
{
  "client_id": 3,
  "due_date": "2026-12-31",
  "items": [
    {
      "description": "Service batch 1",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

Response: **201**

```json
{
  "id": 2,
  "client_id": 3,
  "number": "INV-0001",
  "status": "draft",
  "due_date": "2026-12-31",
  "total_cents": 30000,
  "created_at": "2026-11-18T14:30:19.238348+00:00",
  "items": [
    {
      "description": "Service batch 1",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

### Tenant B: GET /invoices/2

Authorization: Bearer tok_tenantB_birch_test

Response: **200**

```json
{
  "id": 2,
  "client_id": 3,
  "number": "INV-0001",
  "status": "draft",
  "due_date": "2026-12-31",
  "total_cents": 30000,
  "created_at": "2026-11-18T14:30:19.238348+00:00",
  "items": [
    {
      "description": "Service batch 1",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

### Tenant B: PATCH /invoices/2/status

Authorization: Bearer tok_tenantB_birch_test

```json
{
  "status": "sent"
}
```

Response: **200**

```json
{
  "id": 2,
  "client_id": 3,
  "number": "INV-0001",
  "status": "sent",
  "due_date": "2026-12-31",
  "total_cents": 30000,
  "created_at": "2026-11-18T14:30:19.238348+00:00",
  "items": [
    {
      "description": "Service batch 1",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

### Tenant B: GET /invoices

Authorization: Bearer tok_tenantB_birch_test

Response: **200**

```json
[
  {
    "id": 2,
    "client_id": 3,
    "number": "INV-0001",
    "status": "sent",
    "due_date": "2026-12-31",
    "total_cents": 30000,
    "created_at": "2026-11-18T14:30:19.238348+00:00"
  }
]
```

## Check 2: Tenant isolation

### Tenant B: GET /clients

Authorization: Bearer tok_tenantB_birch_test

Response: **200**

```json
[
  {
    "id": 3,
    "name": "Harbor Apartments",
    "email": "office@harbor.test"
  },
  {
    "id": 4,
    "name": "Greenleaf School",
    "email": "finance@greenleaf.test"
  }
]
```

### Tenant B: POST /invoices

Authorization: Bearer tok_tenantB_birch_test

```json
{
  "client_id": 3,
  "due_date": "2026-12-31",
  "items": [
    {
      "description": "Service batch 2",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

Response: **201**

```json
{
  "id": 3,
  "client_id": 3,
  "number": "INV-0002",
  "status": "draft",
  "due_date": "2026-12-31",
  "total_cents": 30000,
  "created_at": "2026-11-18T14:30:19.290501+00:00",
  "items": [
    {
      "description": "Service batch 2",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

### Tenant B: GET /invoices/3

Authorization: Bearer tok_tenantB_birch_test

Response: **200**

```json
{
  "id": 3,
  "client_id": 3,
  "number": "INV-0002",
  "status": "draft",
  "due_date": "2026-12-31",
  "total_cents": 30000,
  "created_at": "2026-11-18T14:30:19.290501+00:00",
  "items": [
    {
      "description": "Service batch 2",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

### Tenant A: GET /invoices/3

Authorization: Bearer tok_tenantA_acme_test

Response: **404**

```json
{
  "detail": "invoice not found"
}
```

### Tenant A: PATCH /invoices/3/status

Authorization: Bearer tok_tenantA_acme_test

```json
{
  "status": "paid"
}
```

Response: **404**

```json
{
  "detail": "invoice not found"
}
```

### Tenant A: POST /invoices

Authorization: Bearer tok_tenantA_acme_test

```json
{
  "client_id": 3,
  "due_date": "2026-12-31",
  "items": [
    {
      "description": "Service batch 99",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

Response: **404**

```json
{
  "detail": "client not found"
}
```

### Tenant A: GET /invoices

Authorization: Bearer tok_tenantA_acme_test

Response: **200**

```json
[
  {
    "id": 1,
    "client_id": 1,
    "number": "INV-0001",
    "status": "sent",
    "due_date": "2026-12-31",
    "total_cents": 30000,
    "created_at": "2026-11-18T14:30:19.202695+00:00"
  }
]
```

### Tenant B: GET /invoices/3

Authorization: Bearer tok_tenantB_birch_test

Response: **200**

```json
{
  "id": 3,
  "client_id": 3,
  "number": "INV-0002",
  "status": "draft",
  "due_date": "2026-12-31",
  "total_cents": 30000,
  "created_at": "2026-11-18T14:30:19.290501+00:00",
  "items": [
    {
      "description": "Service batch 2",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

## Check 3: Plan limit

### Tenant A: GET /me

Authorization: Bearer tok_tenantA_acme_test

Response: **200**

```json
{
  "tenant": "Acme Design Studio",
  "plan": "Free",
  "invoices_this_month": 1,
  "monthly_invoice_limit": 3
}
```

### Tenant A: GET /clients

Authorization: Bearer tok_tenantA_acme_test

Response: **200**

```json
[
  {
    "id": 1,
    "name": "Northwind Cafe",
    "email": "billing@northwind.test"
  },
  {
    "id": 2,
    "name": "Lumen Books",
    "email": "accounts@lumen.test"
  }
]
```

### Tenant A: POST /invoices

Authorization: Bearer tok_tenantA_acme_test

```json
{
  "client_id": 1,
  "due_date": "2026-12-31",
  "items": [
    {
      "description": "Service batch 2",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

Response: **201**

```json
{
  "id": 4,
  "client_id": 1,
  "number": "INV-0002",
  "status": "draft",
  "due_date": "2026-12-31",
  "total_cents": 30000,
  "created_at": "2026-11-18T14:30:19.368094+00:00",
  "items": [
    {
      "description": "Service batch 2",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

### Tenant A: GET /me

Authorization: Bearer tok_tenantA_acme_test

Response: **200**

```json
{
  "tenant": "Acme Design Studio",
  "plan": "Free",
  "invoices_this_month": 2,
  "monthly_invoice_limit": 3
}
```

### Tenant A: POST /invoices

Authorization: Bearer tok_tenantA_acme_test

```json
{
  "client_id": 1,
  "due_date": "2026-12-31",
  "items": [
    {
      "description": "Service batch 3",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

Response: **201**

```json
{
  "id": 5,
  "client_id": 1,
  "number": "INV-0003",
  "status": "draft",
  "due_date": "2026-12-31",
  "total_cents": 30000,
  "created_at": "2026-11-18T14:30:19.387838+00:00",
  "items": [
    {
      "description": "Service batch 3",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

### Tenant A: GET /me

Authorization: Bearer tok_tenantA_acme_test

Response: **200**

```json
{
  "tenant": "Acme Design Studio",
  "plan": "Free",
  "invoices_this_month": 3,
  "monthly_invoice_limit": 3
}
```

### Tenant A: GET /invoices

Authorization: Bearer tok_tenantA_acme_test

Response: **200**

```json
[
  {
    "id": 1,
    "client_id": 1,
    "number": "INV-0001",
    "status": "sent",
    "due_date": "2026-12-31",
    "total_cents": 30000,
    "created_at": "2026-11-18T14:30:19.202695+00:00"
  },
  {
    "id": 4,
    "client_id": 1,
    "number": "INV-0002",
    "status": "draft",
    "due_date": "2026-12-31",
    "total_cents": 30000,
    "created_at": "2026-11-18T14:30:19.368094+00:00"
  },
  {
    "id": 5,
    "client_id": 1,
    "number": "INV-0003",
    "status": "draft",
    "due_date": "2026-12-31",
    "total_cents": 30000,
    "created_at": "2026-11-18T14:30:19.387838+00:00"
  }
]
```

### Tenant A: POST /invoices

Authorization: Bearer tok_tenantA_acme_test

```json
{
  "client_id": 1,
  "due_date": "2026-12-31",
  "items": [
    {
      "description": "Service batch 4",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

Response: **402**

```json
{
  "error": "plan_limit_reached",
  "detail": "Free plan allows 3 invoices per month",
  "used": 3,
  "limit": 3
}
```

### Tenant A: GET /invoices

Authorization: Bearer tok_tenantA_acme_test

Response: **200**

```json
[
  {
    "id": 1,
    "client_id": 1,
    "number": "INV-0001",
    "status": "sent",
    "due_date": "2026-12-31",
    "total_cents": 30000,
    "created_at": "2026-11-18T14:30:19.202695+00:00"
  },
  {
    "id": 4,
    "client_id": 1,
    "number": "INV-0002",
    "status": "draft",
    "due_date": "2026-12-31",
    "total_cents": 30000,
    "created_at": "2026-11-18T14:30:19.368094+00:00"
  },
  {
    "id": 5,
    "client_id": 1,
    "number": "INV-0003",
    "status": "draft",
    "due_date": "2026-12-31",
    "total_cents": 30000,
    "created_at": "2026-11-18T14:30:19.387838+00:00"
  }
]
```

### Tenant B: GET /me

Authorization: Bearer tok_tenantB_birch_test

Response: **200**

```json
{
  "tenant": "Birch Plumbing Ltd",
  "plan": "Pro",
  "invoices_this_month": 2,
  "monthly_invoice_limit": 10
}
```

### Tenant B: POST /invoices

Authorization: Bearer tok_tenantB_birch_test

```json
{
  "client_id": 3,
  "due_date": "2026-12-31",
  "items": [
    {
      "description": "Service batch 3",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

Response: **201**

```json
{
  "id": 6,
  "client_id": 3,
  "number": "INV-0003",
  "status": "draft",
  "due_date": "2026-12-31",
  "total_cents": 30000,
  "created_at": "2026-11-18T14:30:19.429013+00:00",
  "items": [
    {
      "description": "Service batch 3",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

### Tenant B: GET /me

Authorization: Bearer tok_tenantB_birch_test

Response: **200**

```json
{
  "tenant": "Birch Plumbing Ltd",
  "plan": "Pro",
  "invoices_this_month": 3,
  "monthly_invoice_limit": 10
}
```

### Tenant B: POST /invoices

Authorization: Bearer tok_tenantB_birch_test

```json
{
  "client_id": 3,
  "due_date": "2026-12-31",
  "items": [
    {
      "description": "Service batch 4",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

Response: **201**

```json
{
  "id": 7,
  "client_id": 3,
  "number": "INV-0004",
  "status": "draft",
  "due_date": "2026-12-31",
  "total_cents": 30000,
  "created_at": "2026-11-18T14:30:19.449573+00:00",
  "items": [
    {
      "description": "Service batch 4",
      "quantity": 2,
      "unit_price_cents": 15000
    }
  ]
}
```

### Tenant B: GET /me

Authorization: Bearer tok_tenantB_birch_test

Response: **200**

```json
{
  "tenant": "Birch Plumbing Ltd",
  "plan": "Pro",
  "invoices_this_month": 4,
  "monthly_invoice_limit": 10
}
```
