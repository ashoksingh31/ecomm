## Decision 1: Single Logical Cart Per User

**Context:** What problem were you solving?
Users may access the application from multiple devices or distinct browser sessions, creating potential divergence across active items and shopping state.

**Options Considered:**
- Option A: Maintain separate isolated carts per individual session/device.
- Option B: Maintain one logical cart per authenticated user mapped by a centralized identifier.

**Choice:** Option B: Maintain one logical cart per authenticated user.

**Why:** A single cart provides a consistent shopping experience across sessions and devices. In a production system, concurrent cart updates would require conflict resolution (e.g., optimistic locking or versioning). Since this assignment uses in-memory storage and a single application instance, concurrent multi-device synchronization is outside the implementation scope but remains the intended design pattern.

---

## Decision 2: JWT-Based Authorization Using Claims

**Context:** What problem were you solving?
Administrative endpoints (such as coupon creation and deletion) require robust access controls, but full user authentication/session state management is outside the project scope.

**Options Considered:**
- Option A: Query a backing database storage layer for authorization permissions on every individual incoming request.
- Option B: Trust cryptographically verified stateless JWT claims containing structural role definitions after primary validation checks.

**Choice:** Option B: Use JWT claims containing `user_id` and `is_admin`.

**Why:** Avoids unnecessary database lookups and keeps authorization stateless. This simplifies the implementation while remaining representative of common microservice production systems. Administrative permissions are extracted and validated in-memory directly within the dependency injection pipeline.

---

## Decision 3: Read-Only Product Catalog

**Context:** What problem were you solving?
The service must handle cart mutations and final product pricing valuations without expanding into a heavy, sprawling product catalog content management platform.

**Options Considered:**
- Option A: Build out complete Product CRUD APIs and administrative inventory modification modules.
- Option B: Preload a fixed read-only catalog slice representing an upstream external catalog source.

**Choice:** Option B: Use a preloaded read-only product catalog.

**Why:** Keeps the project focused on checkout and cart logic while reflecting how dedicated product services commonly provide static read-optimized catalog data to downstream order services. Product prices are always obtained from the server-side catalog to ensure client requests cannot forge price points.

---

## Decision 4: Reserve Inventory During Checkout

**Context:** What problem were you solving?
Determining when to hold or deduct item stock counts so that items left in abandoned browser sessions do not lock up available warehouse supply.

**Options Considered:**
- Option A: Reserve inventory immediately when items are added to a casual browsing cart.
- Option B: Validate and reserve inventory balances only during the explicit checkout transaction window.

**Choice:** Option B: Reserve inventory only during checkout.

**Why:** Prevents abandoned carts from locking inventory and aligns with common business practices. Inventory validation occurs immediately before order creation, avoiding false out-of-stock scenarios for hot items.

---

## Decision 5: Coupon Validation at Checkout

**Context:** What problem were you solving?
Product pricing structures, specific campaign exclusions, and promotion validity periods can shift while a shopper leaves items sitting inside their active cart for extended durations.

**Options Considered:**
- Option A: Apply and lock discount totals immediately within the cart payload layer.
- Option B: Display estimates in the cart, but calculate and validate all coupon rules directly during the checkout flow.

**Choice:** Option B: Coupons are validated only during checkout.

**Why:** The cart displays estimated totals while checkout recalculates the final payable amount using the latest product prices and coupon rules. This prevents stale pricing issues and ensures expired or deleted coupons are rejected gracefully at execution time.

---

## Decision 6: Immutable Order Snapshots

**Context:** What problem were you solving?
Historical order logs must remain completely accurate for auditing and finance purposes, even if global product catalog descriptions or prices change months later.

**Options Considered:**
- Option A: Store only foreign-key references to base product IDs inside completed orders.
- Option B: Take a full snapshot of all active item values at the millisecond of order placement.

**Choice:** Option B: Orders store product name, purchase price, quantity, and applied discount explicitly.

**Why:** Storing data inline ensures historical orders remain completely accurate regardless of later catalog item modifications. This provides perfect auditing without complex temporal database version schemas.

---

## Decision 7: Idempotent Checkout

**Context:** What problem were you solving?
Network drops, rapid button clicking, or automatic frontend retry mechanisms can issue duplicate checkout payloads, resulting in accidental double-billing or multiple order creations.

**Options Considered:**
- Option A: Process every single request independently as an un-tracked separate entity.
- Option B: Enforce required unique idempotency tracking keys per transaction header.

**Choice:** Option B: Checkout requests are idempotent via an `X-Idempotency-Key` tracking system.

**Why:** Repeated requests using the same idempotency key return the original cached order creation result rather than creating duplicate orders. Combined with an asynchronous mutex lock, it guarantees complete state protection during high-concurrency race windows.

---

## Decision 8 — Milestone Discount Generation: Admin-Triggered with Catch-Up

**Context:** What problem were you solving?
The assignment's FAQ explicitly lists code generation as an admin API action ("generate a discount code if the condition above is satisfied"), which argues for a manual trigger. But a purely manual trigger has a real gap: if the admin doesn't call the endpoint promptly, a customer who legitimately earned a reward at their milestone order gets nothing until someone remembers to ask for it — and if two milestones pass before the admin's next call, calling the endpoint once would only reward the most recent milestone, silently dropping the earlier one.

**Options Considered:**
- Option A: Automatic generation the instant an order hits a milestone, with the admin endpoint reduced to an idempotent backfill/recovery path.
- Option B: Purely admin-triggered, awarding only the single most recent unclaimed milestone per call.
- Option C: Admin-triggered, but a single call awards a code for *every* unclaimed milestone since the last generation (catch-up), not just the latest.

**Choice:** Option C.

**Why:** This keeps the API surface exactly as the assignment describes it (an explicit admin action, not a checkout side-effect), while still guaranteeing no earned reward is permanently lost to admin inaction — the moment the admin does call the endpoint, every customer who ever crossed an unclaimed milestone gets their code, regardless of how many milestones elapsed in between. `CouponRepository.highest_awarded_milestone()` and `CouponService.generate_new_milestone_codes()` implement this by comparing "milestones reached" (`total_orders // MILESTONE_INTERVAL`) against "milestones already awarded" and looping over the gap.

**Trade-off acknowledged:** a customer who hits a milestone still doesn't receive their code *automatically* — they're dependent on the admin eventually calling the endpoint, same as Option B. Option A would close that gap entirely, but at the cost of code generation happening as an invisible checkout side-effect rather than the explicit, auditable admin action the assignment describes. If real-time reward delivery becomes a requirement, Option A remains the straightforward next step — the underlying eligibility logic (`generate_new_milestone_codes`) wouldn't need to change, only *where* it's called from.