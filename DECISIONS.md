
## Decision: Single Logical Cart Per User

**Context:** What problem were you solving?
Users may access the application from multiple devices or distinct browser sessions, creating potential divergence across active items and shopping state.

**Options Considered:**
- Option A: Maintain separate isolated carts per individual session/device.
- Option B: Maintain one logical cart per authenticated user mapped by a centralized identifier.

**Choice:** Option B: Maintain one logical cart per authenticated user.

**Why:** A single cart provides a consistent shopping experience across sessions and devices. In a production system, concurrent cart updates would require conflict resolution (e.g., optimistic locking or versioning). Since this assignment uses in-memory storage and a single application instance, concurrent multi-device synchronization is outside the implementation scope but remains the intended design pattern.

---

## Decision: JWT-Based Authorization Using Claims

**Context:** What problem were you solving?
Administrative endpoints (such as coupon creation and deletion) require robust access controls, but full user authentication/session state management is outside the project scope.

**Options Considered:**
- Option A: Query a backing database storage layer for authorization permissions on every individual incoming request.
- Option B: Trust cryptographically verified stateless JWT claims containing structural role definitions after primary validation checks.

**Choice:** Option B: Use JWT claims containing `user_id` and `is_admin`.

**Why:** Avoids unnecessary database lookups and keeps authorization stateless. This simplifies the implementation while remaining representative of common microservice production systems. Administrative permissions are extracted and validated in-memory directly within the dependency injection pipeline.

---

## Decision: Read-Only Product Catalog

**Context:** What problem were you solving?
The service must handle cart mutations and final product pricing valuations without expanding into a heavy, sprawling product catalog content management platform.

**Options Considered:**
- Option A: Build out complete Product CRUD APIs and administrative inventory modification modules.
- Option B: Preload a fixed read-only catalog slice representing an upstream external catalog source.

**Choice:** Option B: Use a preloaded read-only product catalog.

**Why:** Keeps the project focused on checkout and cart logic while reflecting how dedicated product services commonly provide static read-optimized catalog data to downstream order services. Product prices are always obtained from the server-side catalog to ensure client requests cannot forge price points.

---

## Decision: Reserve Inventory During Checkout

**Context:** What problem were you solving?
Determining when to hold or deduct item stock counts so that items left in abandoned browser sessions do not lock up available warehouse supply.

**Options Considered:**
- Option A: Reserve inventory immediately when items are added to a casual browsing cart.
- Option B: Validate and reserve inventory balances only during the explicit checkout transaction window.

**Choice:** Option B: Reserve inventory only during checkout.

**Why:** Prevents abandoned carts from locking inventory and aligns with common business practices. Inventory validation occurs immediately before order creation, avoiding false out-of-stock scenarios for hot items.

---

## Decision: Coupon Validation at Checkout

**Context:** What problem were you solving?
Product pricing structures, specific campaign exclusions, and promotion validity periods can shift while a shopper leaves items sitting inside their active cart for extended durations.

**Options Considered:**
- Option A: Apply and lock discount totals immediately within the cart payload layer.
- Option B: Display estimates in the cart, but calculate and validate all coupon rules directly during the checkout flow.

**Choice:** Option B: Coupons are validated only during checkout.

**Why:** The cart displays estimated totals while checkout recalculates the final payable amount using the latest product prices and coupon rules. This prevents stale pricing issues and ensures expired or deleted coupons are rejected gracefully at execution time.

---

## Decision: Immutable Order Snapshots

**Context:** What problem were you solving?
Historical order logs must remain completely accurate for auditing and finance purposes, even if global product catalog descriptions or prices change months later.

**Options Considered:**
- Option A: Store only foreign-key references to base product IDs inside completed orders.
- Option B: Take a full snapshot of all active item values at the millisecond of order placement.

**Choice:** Option B: Orders store product name, purchase price, quantity, and applied discount explicitly.

**Why:** Storing data inline ensures historical orders remain completely accurate regardless of later catalog item modifications. This provides perfect auditing without complex temporal database version schemas.

---

## Decision: Idempotent Checkout

**Context:** What problem were you solving?
Network drops, rapid button clicking, or automatic frontend retry mechanisms can issue duplicate checkout payloads, resulting in accidental double-billing or multiple order creations.

**Options Considered:**
- Option A: Process every single request independently as an un-tracked separate entity.
- Option B: Enforce required unique idempotency tracking keys per transaction header.

**Choice:** Option B: Checkout requests are idempotent via an `X-Idempotency-Key` tracking system.

**Why:** Repeated requests using the same idempotency key return the original cached order creation result rather than creating duplicate orders. Combined with an asynchronous mutex lock, it guarantees complete state protection during high-concurrency race windows.

```