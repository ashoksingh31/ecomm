# E-Commerce Cart & Checkout Backend

A backend service for cart, checkout, and milestone-based discount codes,
built to demonstrate backend design, clean architecture, and engineering
decision-making rather than to be a complete e-commerce platform.

See [ASSUMPTIONS.md](./ASSUMPTIONS.md) and [DECISIONS.md](./DECISIONS.md)
for the reasoning behind every non-obvious choice in this codebase.

## Tech Stack
- Python 3.12+
- FastAPI + Pydantic v2
- Uvicorn
- Pytest + httpx (TestClient)
- In-memory storage (no database)
- JWT via `python-jose`

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn src.main:app --reload
```

The API is now at `http://localhost:8000`. Interactive docs (Swagger UI)
are at `http://localhost:8000/docs`.

## Authentication (read this first)

There is no login endpoint — authentication is explicitly out of scope
(see ASSUMPTIONS.md #1). Every route except `/health` requires
`Authorization: Bearer <jwt>`, where the JWT carries `user_id` and
`is_admin`. Generate a test token locally:

```bash
python scripts/generate_test_token.py --user-id 1
python scripts/generate_test_token.py --user-id 99 --admin
```

Use the printed token as the Bearer token in requests or in Swagger's
"Authorize" button.

## Running Tests

```bash
pytest -v
```

26 tests covering products, cart mutations, checkout (including
idempotency), the full milestone discount-code lifecycle, and admin
stats.

## API Overview

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | none | Liveness check |
| GET | `/products` | user | List catalog |
| GET | `/products/{id}` | user | Get one product |
| GET | `/cart` | user | View current cart |
| POST | `/cart/items` | user | Add item to cart |
| PATCH | `/cart/items/{product_id}` | user | Update quantity |
| DELETE | `/cart/items/{product_id}` | user | Remove item |
| POST | `/checkout` | user | Create order from cart (idempotent) |
| GET | `/orders` | user | List own orders |
| GET | `/orders/{id}` | user | Get one order (owner or admin only) |
| POST | `/admin/discount-codes/generate` | admin | Award codes for any newly-reached Nth-order milestones |
| GET | `/admin/stats` | admin | Store-wide stats: orders, items sold, revenue, discount codes |

## The Milestone Discount System, End to End

1. Every successful checkout increments the store-wide order count.
2. When total orders crosses a multiple of `MILESTONE_INTERVAL`
   (default **5**, see `src/config/settings.py`), that milestone becomes
   "reachable."
3. An admin calls `POST /admin/discount-codes/generate`. This awards one
   single-use code, at `MILESTONE_DISCOUNT_PERCENTAGE` (default **10%**)
   off, to **whichever customer placed that exact Nth order** — and to
   any other customers whose milestone was reached but not yet claimed,
   if the admin hasn't called this endpoint in a while (see
   DECISIONS.md — Decision 8).
4. Only that customer can redeem their code, and only once, by passing
   `discount_code` in the `POST /checkout` body.

### Example walkthrough

```bash
# 1. Place 5 orders as 5 different users to reach the first milestone
for i in 1 2 3 4 5; do
  TOKEN=$(python scripts/generate_test_token.py --user-id $i)
  curl -s -X POST localhost:8000/cart/items \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d '{"product_id": 1, "quantity": 1}' > /dev/null
  curl -s -X POST localhost:8000/checkout \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d "{\"idempotency_key\": \"order-$i\"}" > /dev/null
done

# 2. Admin generates the code (user 5 placed the 5th order, so they get it)
ADMIN_TOKEN=$(python scripts/generate_test_token.py --user-id 99 --admin)
curl -s -X POST localhost:8000/admin/discount-codes/generate \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 3. User 5 redeems it
USER5_TOKEN=$(python scripts/generate_test_token.py --user-id 5)
curl -s -X POST localhost:8000/cart/items \
  -H "Authorization: Bearer $USER5_TOKEN" -H "Content-Type: application/json" \
  -d '{"product_id": 2, "quantity": 1}'
curl -s -X POST localhost:8000/checkout \
  -H "Authorization: Bearer $USER5_TOKEN" -H "Content-Type: application/json" \
  -d '{"idempotency_key": "order-5-redeem", "discount_code": "<code from step 2>"}'

# 4. Check the numbers
curl -s localhost:8000/admin/stats -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Project Structure

```text
ecom-backend/
├── src/
│   ├── api/
│   │   ├── deps.py            # auth deps + repository/service wiring
│   │   ├── error_handlers.py  # domain error -> HTTP status mapping
│   │   └── routes/             # one module per resource
│   ├── config/settings.py      # all config in one place
│   ├── core/
│   │   ├── exceptions.py       # domain-level exceptions
│   │   └── security.py         # JWT encode/decode
│   ├── models/                 # domain models (dataclasses)
│   ├── repositories/           # in-memory storage, one per entity
│   ├── schemas/                # Pydantic request/response models
│   ├── services/                # business logic
│   └── main.py                 # FastAPI app + router registration
├── scripts/generate_test_token.py
├── tests/
├── ASSUMPTIONS.md
├── DECISIONS.md
├── requirements.txt
└── .gitignore
```

## Architecture

```text
                Client
                   │
                   ▼
             FastAPI Routes  (src/api/routes)
                   │
                   ▼
             Service Layer   (src/services)
                   │
                   ▼
           Repository Layer  (src/repositories)
                   │
                   ▼
          In-Memory Storage  (one dict per repository)
```
