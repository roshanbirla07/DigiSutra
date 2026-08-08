# DigiSutra Plan

## Status

The platform already has the first working slice of the marketplace:
- Flask backend on PostgreSQL
- user signup and login
- EdDSA access tokens and request-level role guards on selected endpoints
- product catalog endpoints
- internal ledger models
- Razorpay order creation, confirmation, and webhook handling
- refund bookkeeping
- seller balance tracking
- asset upload and download tracking
- CloudFront and S3 support for product delivery
- static frontend app under `apps/web/`
- explicit ledger transition validation for order and refund state changes
- payout state transitions and batch processing

Authorization is currently partial. Authentication is present, but several
endpoints still need resource ownership, collection scoping, or privileged
role enforcement before the API is safe for multi-user production use.

## Current Priorities

1. Close authorization gaps
- protect user listing and other collection reads
- prevent public signup from assigning seller or admin roles
- enforce seller ownership for products, assets, payouts, and dashboard data
- restrict orders, refunds, and payment confirmation to the relevant buyer, seller, or admin
- bind download logging to the authorized delivery context

2. Finish purchase-to-access flow
- grant access from successful orders
- keep downloads tied to purchased orders
- revoke access on refund
- define re-download limits and expiry rules
- return a true protected delivery response for purchased assets

3. Add seller payout workflow
- track pending and available seller balances
- introduce payout batches
- support manual or semi-manual payout execution
- record payout failures and retries
- finalize payout batch reconciliation and retry handling

4. Add trust and moderation controls
- seller suspension
- listing review or flagging
- dispute and support workflow
- fraud and abuse signals

5. Build dashboard views on top of stable backend records
- seller sales summary
- payout summary
- refund summary
- product performance
- transaction reporting

6. Add operational safeguards
- separate test and live payment settings
- reconciliation reports
- logging and alerting for payment, webhook, and payout failures
- compliance and tax/invoice foundation

## Frontend Readiness Gaps

Before the frontend work is treated as fully unblocked, the backend should also have:

- a signed, short-lived asset delivery response
- buyer purchase-history endpoints for orders and downloads
- seller-owned product views for dashboard use
- refund/admin workflow endpoints or summary views
- payout summary endpoints for seller and admin screens
- a standard token-storage and 401/403 response contract for the web app

## Near-Term Build Order

1. Complete the authorization subtasks below
2. Add refund-driven access revocation and policy limits
3. Return protected delivery responses for purchased assets
4. Add seller payout workflow completion and payout monitoring

## Authorization Completion Subtasks

Each subtask is intentionally scoped to the existing controller, serializer,
model, and router layers. Add focused API tests with each implementation.

### AUTH-01: Establish the endpoint authorization matrix

Status: implemented in the plan and route documentation; runtime regression
execution remains environment-dependent.

- Inventory every v1 route and record authentication, allowed roles, and
  resource-owner rules.
- Standardize 401 responses for missing or invalid tokens and 403 responses
  for authenticated users without permission.
- Add regression coverage for every protected route and preserve the webhook
  signature path as the external-provider exception.
- Commit message: `chore(auth): define v1 endpoint authorization matrix`

### AUTH-02: Protect user administration and signup role assignment

Status: implemented in the API; regression coverage remains in AUTH-07.

- Require `admin` for `GET /v1/users/`.
- Make public signup create customers only; keep seller/admin creation or
  promotion behind an authenticated admin workflow.
- Ensure inactive users cannot log in or receive access tokens.
- Commit message: `fix(auth): restrict user listing and privileged role creation`

### AUTH-03: Enforce seller ownership for catalog and asset operations

Status: implemented in the API; regression coverage remains in AUTH-07.

- Derive the product owner from `g.user` for seller requests instead of
  trusting `owner_uuid` from the request.
- Allow sellers to delete only their own products; admins may manage all
  products according to moderation policy.
- Require the authenticated seller/admin to own the product before creating
  an asset upload target.
- Commit message: `fix(auth): enforce seller ownership for products and assets`

### AUTH-04: Scope ledger, refund, and payment operations

Status: implemented in the API; regression coverage remains in AUTH-07.

- Limit order collection reads to the authenticated buyer/seller, with full
  visibility reserved for admins.
- Allow order detail and refund requests only for the buyer or an authorized
  admin workflow; do not expose another user's order data.
- Require the payment creator and checkout confirmer to match the order buyer;
  keep Razorpay webhooks signature-authenticated and idempotent.
- Commit message: `fix(auth): scope orders refunds and payment actions`

### AUTH-05: Scope payout and dashboard data

Status: implemented in the API; regression coverage remains in AUTH-07.

- Require authentication for payout listing and return only the seller's
  payouts to sellers; admins may list all payouts.
- Derive payout ownership from the authenticated seller and prevent callers
  from selecting another seller through request data.
- Keep payout batch, retry, reconciliation, and admin dashboard operations
  restricted to admins; keep seller dashboard summaries seller-scoped.
- Commit message: `fix(auth): scope seller payouts and dashboard records`

### AUTH-06: Bind asset delivery and download logging to one access policy

Status: implemented; download identity and the download-log boundary are now
bound to the authenticated user and a verified delivery token. Replay control
remains limited to the existing access-expiry and download-count policy.

- Keep delivery authorization tied to the authenticated buyer, paid order,
  matching product, granted access, expiry, and download limit.
- Validate download-log identity and order fields from the authenticated
  request/delivery context instead of accepting caller-provided identity data.
- Verify delivery tokens at the consumption boundary and prevent replay or
  cross-asset/cross-order use where the delivery endpoint requires it.
- Commit message: `fix(auth): bind asset downloads to verified delivery access`

### AUTH-07: Add authorization regression coverage and web contract

Status: implemented; focused tests are checked in, but execution requires the
API dependencies and a working test environment.

- Add tests for IDOR attempts across users, sellers, orders, products, assets,
  and payouts, including inactive accounts and role changes.
- Document the frontend token-storage, 401, and 403 contract and update the
  static client to clear stale sessions on authentication failure.
- Run the API test suite and verify the documented route matrix against the
  registered Flask routes.
- Commit message: `test(auth): cover authorization boundaries and client errors`

## Working Rules

- Internal ledger records are the source of truth.
- Webhook handlers must be idempotent.
- Provider-specific logic stays in service layers.
- Buyer payments and seller payouts stay separate.
- UI should read from backend records, not infer financial state client-side.
- Access to content must always be tied to a paid order.
- Ledger transitions should be validated centrally before writes are committed.
- Payout transitions should be validated centrally before batch execution.
- Authorization must be enforced server-side at both route and resource level.
- Caller-supplied owner, buyer, seller, and user identifiers must not override
  the authenticated principal.

## Success Criteria

- A buyer can pay, receive access, and download purchased content.
- Duplicate payment webhooks do not create duplicate orders or balances.
- A refund reverses seller earnings and removes access when required.
- Payouts can be tracked independently from buyer payments.
- Admin and seller views can be built from the ledger without ad hoc calculations.
- Invalid order/refund state combinations are rejected before they reach persistence.
- Invalid payout state combinations are rejected before they reach persistence.
- Users cannot read or mutate another user's resources through an identifier
  supplied in the request.
- Seller and admin operations return consistent 401/403 responses.
