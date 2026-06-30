# Design Decisions (ADRs)

## Decision 1 — Single Logical Cart Per User
**Choice:** One cart per authenticated user (not per session/device).
**Why:** Consistent shopping experience across sessions. Concurrent
multi-device synchronization would need optimistic locking in a
production system with a real DB; out of scope for an in-memory,
single-instance app.

## Decision 2 — JWT-Based Authorization Using Claims
**Choice:** Trust `user_id` and `is_admin` from the JWT rather than
querying a database on every request.
**Why:** Stateless, avoids unnecessary lookups. **Production note:** a
centralized RBAC system with token revocation would be preferred where
permissions change frequently.

## Decision 3 — Read-Only Product Catalog
**Choice:** Preloaded, in-memory catalog with no CRUD endpoints.
**Why:** Keeps the project focused on cart/checkout/discount logic, which
is what's actually being evaluated.

## Decision 4 — Reserve Inventory Only At Checkout (N/A here — see note)
Inventory is intentionally unlimited (Assumption 3), so there is no
reservation step. This decision is kept in the doc for context since it
shaped Decision 5 below (recompute everything at checkout, not earlier).

## Decision 5 — Coupon Validation at Checkout, Not in the Cart
**Choice:** The cart view shows an *estimated* subtotal from live prices;
checkout recomputes everything from scratch and is the only place a
discount code is validated/applied.
**Why:** Prevents stale pricing or a stale discount eligibility check
from leaking into what's actually charged.

## Decision 6 — Immutable Order Snapshots
**Choice:** `OrderLine` stores product name, unit price, and quantity at
time of purchase — not just a product_id.
**Why:** Historical orders stay accurate even if the catalog changes or
a product is later removed.

## Decision 7 — Idempotent Checkout
**Choice:** Every checkout call includes a client-generated
`idempotency_key`. `OrderRepository` maps key → order; a repeated key
returns the original order untouched instead of creating a duplicate.
**Why:** Clients may retry after timeouts/network failures; this makes
retries safe by construction.

## Decision 8 — Milestone-Based Discount Codes (Store-Wide, "Nth Order")
**Context:** The assignment requires that every Nth order unlocks a
discount code, with generation triggered by an admin call rather than
happening automatically inside checkout.

**Choice:**
- The milestone counter is derived from `OrderRepository.count()`
  (`total_orders // N`), not tracked as a separate mutable variable —
  one source of truth, no drift risk.
- `POST /admin/discount-codes/generate` compares milestones *reached*
  against milestones *already awarded* and generates one code per
  unclaimed milestone in a single call ("catch-up" generation). If the
  admin hasn't called the endpoint in a while and multiple milestones
  passed, every eligible customer still gets their code — nobody's
  earned discount is silently dropped because of an admin call cadence.
- The code is owned by whichever user placed the exact Nth order
  (`order_at_sequence(milestone * N)`), is redeemable only by that user,
  and is single-use (invalidated the moment checkout succeeds — not at
  validation time, so a failed/retried checkout can't burn a code
  without producing an order; this composes directly with Decision 7).
- N and the discount percentage are fixed server-side config
  (`src/config/settings.py`), not caller-supplied parameters.

**Why:** These specifics (global vs per-user, ownership, single-use,
fixed config) were explicitly decided with the project owner before
implementation rather than inferred, since the assignment brief doesn't
spell them out and guessing wrong here would misrepresent the intended
business rule.

## Decision 9 — Domain Errors, Not HTTPException, in the Service Layer
**Choice:** Services raise typed exceptions from `src/core/exceptions.py`
(e.g. `EmptyCartError`, `DiscountCodeAlreadyUsedError`). A single
exception handler (`src/api/error_handlers.py`) maps these to HTTP status
codes.
**Why:** Keeps the service layer framework-agnostic and testable without
spinning up FastAPI, and keeps route handlers free of repetitive
try/except blocks.

## Decision 10 — Each Repository Owns Its Own Storage
**Choice:** `ProductRepository`, `CartRepository`, `OrderRepository`, and
`CouponRepository` each hold a private dict, rather than sharing one
generic `memory_store.py` object.
**Why:** Cleaner separation of responsibility; each repository's
invalidation/query logic (e.g. milestone lookups, idempotency index) is
local to the entity it concerns.
