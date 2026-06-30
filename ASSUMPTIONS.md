# Assumptions

### 1. Authentication is outside the scope.
Every request is assumed to contain a valid JWT. The project focuses on
authorization and business logic rather than implementing an
authentication system. `scripts/generate_test_token.py` mints tokens
locally for testing since there is no `/login` endpoint.

### 2. Product catalog already exists.
Products are preloaded in `ProductRepository` at startup. The application
consumes the catalog but does not manage it (no create/update/delete).

### 3. Infinite inventory.
Inventory constraints are intentionally ignored. Adding items to a cart
or checking out never checks stock levels.

### 4. Single application instance.
The application runs as one FastAPI process. Distributed synchronization
is outside the assignment scope.

### 5. In-memory persistence.
All data is stored in memory. Restarting the application clears
everything, including generated discount codes and orders.

### 6. Sequential integer IDs.
Entities use sequential integer identifiers.
**Production note:** UUIDs would be preferred in production to avoid
predictable identifiers and improve distributed scalability.

### 7. JWT claims are trusted.
Authentication is assumed to have already happened upstream. The JWT
contains `user_id` and `is_admin`; the backend validates the signature
and trusts these claims for authorization decisions.

### 8. Admin roles remain valid for the life of the token.
Role changes are not reflected mid-token.
**Production note:** a centralized RBAC system or token revocation
mechanism would be preferred.

### 9. Product prices are always server-side truth.
The client only ever sends product IDs and quantities. Prices used in
the cart view and at checkout are always read fresh from the product
catalog, never trusted from client input.

### 10. Discount milestone (N) and percentage are global, fixed config.
`MILESTONE_INTERVAL` (default 5) and `MILESTONE_DISCOUNT_PERCENTAGE`
(default 10%) live in `src/config/settings.py`, not in the request body
of the admin generate-code call. This was a deliberate choice discussed
before implementation, to keep the discount rule centrally controlled
rather than caller-defined.

### 11. The "Nth order" milestone is store-wide, not per-user.
Milestone counting is based on the total number of orders ever placed
across all customers, not each customer's individual order count.

### 12. A generated discount code belongs to exactly one user and is single-use.
Only the customer who placed the triggering Nth order can redeem it, and
it becomes permanently unusable after one successful checkout.
