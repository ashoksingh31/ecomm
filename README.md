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
`is_admin`. The backend only ever *verifies* tokens; it never issues them.
You need a way to mint one locally, and there are two supported ways:

**Option A — CLI script (for curl / Swagger UI)**
```bash
python scripts/generate_test_token.py --user-id 1
python scripts/generate_test_token.py --user-id 99 --admin
```
Copy the printed token into curl's `-H "Authorization: Bearer <token>"`
or Swagger's "Authorize" button.

**Option B — Postman (self-signing, no copy-paste needed)**
See [Testing with Postman](#testing-with-postman) below — the provided
collection signs its own tokens automatically, including admin tokens.

Both approaches sign against the same dev-only secret in
`src/config/settings.py` (`jwt_secret_key`), so tokens from either method
are interchangeable and always valid against a locally running server.

## Running Tests

```bash
pytest -v
```
26 tests covering products, cart mutations, checkout (including
idempotency), the full milestone discount-code lifecycle, and admin
stats. **This is the authoritative, graded test suite** for this project.

## Testing with Postman

Import [`postman_collection.json`](./postman_collection.json). It's fully
self-contained — you never paste a token in manually, including for admin
endpoints. This collection is a **manual/demo smoke-test layer**, not a
replacement for `pytest`: it exists so a reviewer can click through the
actual HTTP flow (or hit "Run" for a quick pass/fail check), while
`pytest` remains the real proof of correctness.

### How admin tokens get generated

Every request in the collection has its own pre-request script that signs
a JWT client-side, using the exact same HS256 secret as
`src/config/settings.py` (`dev-only-secret-change-me`). It's JavaScript
in the Postman sandbox doing what `create_access_token()` does in Python
— same header, same claims, same signature — so the running server
accepts it as a completely normal token.

- **Regular user requests** (Products, Cart, Checkout, Orders) sign with
  `user_id` = the collection variable `user_id` (default `1`) and
  `is_admin = false`.
- **Admin requests** (`Admin` folder: Generate Discount Codes, Get Stats)
  sign with `user_id` = the collection variable `admin_user_id` (default
  `999`) and `is_admin = true` — hardcoded into that request's own
  pre-request script, so it always gets an admin token regardless of what
  the shared `user_id` variable is set to.
- **Milestone Walkthrough** requests hardcode a specific `user_id` per
  step (1 through 5, then 999 for the admin steps), so the whole
  discount-code lifecycle runs deterministically without touching any
  variables by hand.

To test as a different admin, or to double check nothing's hardcoded
against you: change the `admin_user_id` collection variable, or open any
`Admin` request's Pre-request Script tab — the last line is always
```js
pm.collectionVariables.set('bearer_token', generateJWT(<user id>, <is_admin>));
```
which you can freely edit for one-off experiments.

### Running the Milestone Walkthrough

This collection has no way to reset the running server's in-memory state
(no such endpoint exists — see ASSUMPTIONS.md #5), so:

1. Restart the server: `uvicorn src.main:app --reload`
2. In Postman, right-click **Milestone Walkthrough (run this folder in
   isolation, on a freshly restarted server)** → **Run folder**
3. All 14 requests execute in order: 5 users each place one order,
   admin generates a code (awarded to user 5, who placed the 5th order),
   user 5 redeems it, and a final stats check confirms 6 total orders and
   1 discount code generated.

Don't run this folder back-to-back without restarting the server, and
don't run the whole collection (all folders) in one go unless you've
just restarted — the standalone `Cart`/`Checkout` folders place an order
of their own, which shifts the milestone math by one.

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
   DECISIONS.md — "catch-up" generation).
4. Only that customer can redeem their code, and only once, by passing
   `discount_code` in the `POST /checkout` body.

### Example walkthrough (curl)

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

The equivalent flow is fully automated in Postman — see
[Running the Milestone Walkthrough](#running-the-milestone-walkthrough)
above.

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
├── postman_collection.json
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