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

The backend has several marketplace foundations implemented in code, including
seller applications, protected asset delivery, upload verification, refund
provider reconciliation, seller suspension/readiness, scoped product and payout
APIs, invoice foundations, and operations summaries. This is not yet production
ready. The current local database also contains manual schema fixes that must
be converted into Alembic migrations before the product can be shipped.

## Production Reality Check

The product should not ship to real users until these gaps are closed:

- Seller onboarding is currently an application/review flow, not a real KYC
  flow. It does not yet verify identity, business details, bank account
  ownership, tax details, or seller risk.
- Docker PostgreSQL is acceptable for local development only. Production should
  use managed PostgreSQL, preferably AWS RDS with backups, point-in-time
  recovery, restricted network access, and migration-controlled schema changes.
- Payment collection exists, but production needs live/test separation,
  webhook replay protection, reconciliation jobs, refund reconciliation, and
  checkout failure/retry states tested end to end.
- Payouts are tracked internally, but there is no complete provider-backed
  payout execution, bank/KYC verification, settlement schedule, or payout
  compliance workflow.
- Secrets are currently developer-configured. Before production, move secrets
  out of code and rotate any key that has been pasted into local files, logs, or
  chat. Use AWS Secrets Manager or SSM Parameter Store for deployed services.
- The manual database changes made during local debugging need migrations and
  migration smoke tests. `db.create_all()` must not be the production schema
  management strategy.
- The admin UI needs complete queues for seller applications, KYC review,
  payouts, refunds, support, moderation, reconciliation, and audit history.

## Production Readiness Roadmap

### P0: Migration and schema control

- Create Alembic migrations for all manual schema changes:
  - product image metadata columns on `product`
  - widened UUID/external identifier columns that now need `String(100)`
  - delivery-token and download-order UUID width changes
  - any seller application/profile columns that exist in models but not in a
    fresh migrated database
- Add a migration smoke test that creates an empty PostgreSQL database and runs
  `alembic upgrade head`.
- Add an upgrade test against a copy of the current local schema so manual
  fixes are proven repeatable.
- Add downgrade decisions for each migration. If a downgrade is unsafe, leave a
  clear Alembic comment and document the backup/restore path.
- Stop relying on `db.create_all()` for production startup. Production deploys
  must run migrations before starting the API.
- Add a separate seed script for local/admin/dev data. Do not mix seed data with
  schema migrations.
- Document the deployment order: backup database, run migrations, start API,
  run smoke tests, then enable traffic.

### P0: Infrastructure and secrets

- Use AWS RDS PostgreSQL for production; keep Docker PostgreSQL for local
  development and CI only.
- Configure private networking, security groups, database backups,
  point-in-time recovery, and restore drills.
- Move Razorpay, S3, CloudFront, EdDSA, database, and webhook secrets to AWS
  Secrets Manager or SSM Parameter Store.
- Split local, test, staging, and production config. Test Razorpay keys must
  never be accepted in live mode.
- Rotate the current Razorpay, webhook, AWS, and EdDSA secrets before any public
  deployment if they were pasted into code, terminal output, screenshots, or
  chat.
- Add HTTPS, production CORS allowlists, API rate limits, structured logs,
  request IDs, and alerting for 5xx/payment/webhook/payout failures.

### P0: Seller onboarding and KYC

- Replace the basic seller application with a proper seller state machine:
  `draft`, `submitted`, `kyc_pending`, `kyc_in_review`, `kyc_verified`,
  `kyc_failed`, `approved`, `rejected`, `suspended`.
- Collect and validate seller details: legal name, business type, address,
  phone, email verification, tax identifiers, bank account, accepted terms, and
  supported product categories.
- Add document upload records for identity, address, business proof, tax proof,
  and bank proof. Store files in private S3 with restricted admin access.
- Integrate a KYC/provider verification step or create a manual admin
  verification queue with audit logs until a provider is selected.
- Block product publishing and payout readiness until KYC is verified and admin
  approval is complete.
- Add admin actions for request information, approve, reject, suspend, resume,
  payout hold, KYC override, and note history.

### P0: Payments, orders, and access

- Complete buyer checkout as: internal order -> Razorpay order -> checkout ->
  backend confirmation/webhook -> paid order -> access grant.
- Add idempotency keys for order creation, payment confirmation, refund request,
  webhook processing, and payout execution.
- Verify Razorpay webhook signatures on the raw body and reject replayed events.
- Add reconciliation jobs for provider orders/payments/refunds versus internal
  ledger state.
- Handle cancelled checkout, failed payment, delayed webhook, duplicate
  confirmation, refund pending, refund failed, and refund completed states in
  API and UI.
- Ensure downloads are granted only from paid orders and revoked or restricted
  after refunds according to policy.

### P0: Payouts and seller balances

- Keep buyer payments and seller payouts separate in code and database records.
- Add payout eligibility checks: verified KYC, verified bank account, no payout
  hold, minimum balance, settlement age, no active fraud/review hold.
- Add payout provider integration or a documented manual payout process with
  admin approval, reference IDs, failure handling, and reconciliation.
- Add immutable balance movement records so `SellerBalance` can be rebuilt and
  audited.
- Add settlement reports for pending, available, processing, paid, failed, and
  reversed amounts.

### P0: Product assets and delivery

- Keep original files in private S3. Public product images can be served
  through CloudFront; paid assets must use short-lived signed delivery.
- Verify upload completion through S3 metadata/head-object checks before a
  product can publish.
- Add malware scanning/content review for seller-uploaded files before release.
- Add download limits, expiry rules, retry behavior, and clear error states in
  the customer library.

### P1: Auth, security, and compliance

- Add email verification, password reset, password policy, account lock/rate
  limiting, and admin-created user safeguards.
- Add complete RBAC tests for customer, seller, admin, suspended seller, and
  inactive user flows.
- Add audit logs for admin approvals, seller KYC decisions, payout changes,
  refunds, moderation actions, and secret/config changes.
- Add Terms of Service, Privacy Policy, Refund Policy, seller agreement, tax
  invoice rules, data retention policy, and KYC-data handling rules.
- Keep PCI scope limited by using Razorpay-hosted checkout and never storing
  card data.

### P1: Admin and operations

- Build admin dashboards for seller requests, KYC review, payments, refunds,
  payouts, support tickets, product moderation, and reconciliation failures.
- Add filters, status tabs, detail views, notes, confirmation dialogs, and audit
  trails for all admin actions.
- Add operational runbooks for failed webhooks, stuck payouts, disputed orders,
  seller suspension, refund escalation, and database restore.

### P1: Frontend completion

- Add visible logout and account settings in all authenticated layouts.
- Add seller application status, KYC progress, request-information resubmission,
  approval/rejection messaging, and seller activation checklist.
- Add checkout success/failure/pending pages and customer library downloads.
- Add seller dashboard pages for products, sales, payouts, KYC status, and
  account readiness.
- Add admin seller/KYC review pages, payout review pages, refund pages, and
  reconciliation views.
- Add loading, empty, error, retry, forbidden, expired-session, and duplicate
  submit states on every critical screen.

### P1: Testing and release gates

- Add backend unit and integration tests for migrations, auth, seller KYC,
  checkout, webhooks, refunds, payouts, asset delivery, and admin actions.
- Add Playwright end-to-end tests for signup, login, seller application, admin
  approval, checkout, library download, refund request, and logout.
- Add CI steps for linting, backend tests, frontend syntax checks, migration
  upgrade on a clean DB, and Docker image build.
- Add staging smoke tests before production deploy: health check, login,
  product listing, checkout test order, webhook test, seller application, admin
  queue, and protected download.

## Current Priorities

0. Resolve frontend and production release blockers
- attach bearer tokens to all authenticated web API requests and clear stale
  sessions consistently on 401/403 responses
- make public signup customer-only in both the UI and API contract; remove
  creator/admin choices from public signup
- add seller application, admin review, approval/rejection, promotion, and
  suspension workflow so customers can become sellers through a controlled
  process
- replace the currently exposed CloudFront URL with a genuinely protected
  delivery response, such as a CloudFront signed URL or backend delivery
  proxy
- connect processed refunds to the Razorpay refund API and reconcile provider
  refund results with the internal ledger
- add asset upload completion and verification/status handling after the
  presigned upload target is used
- separate test/live payment configuration, add migrations, monitoring,
  reconciliation alerts, and tax/invoice foundations

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

- a stable authenticated web-client contract, including bearer-token
  attachment and 401/403 session handling
- a customer-only public signup contract with a separate seller application
  and admin approval flow
- a signed, short-lived asset delivery response
- buyer purchase-history endpoints for orders and downloads
- seller-owned product views for dashboard use
- refund/admin workflow endpoints or summary views
- payout summary endpoints for seller and admin screens
- a standard token-storage and 401/403 response contract for the web app
- an asset-upload completion/status endpoint

## Near-Term Build Order

1. Complete the authorization subtasks below and align the web auth contract
2. Add customer-to-seller application and admin approval workflow (application
   models, customer APIs, admin review APIs, atomic promotion, and customer UI
   implemented)
3. Finish purchase-to-access delivery, including genuinely protected URLs
4. Connect provider refunds and complete asset upload verification
5. Add seller payout monitoring and production operational safeguards

## Frontend Implementation Plan

The frontend will extend the existing static client under `apps/web/`. The
current authenticated shell, sidebar navigation, profile menu, settings view,
product editor, product list, seller application form, and admin seller review
queue remain the foundation. New screens should be added as focused controllers
and routes instead of turning `app.js` into a feature-specific monolith.

### FE-01: Frontend foundation and shared contracts

- Keep a single API client responsible for bearer tokens, JSON parsing, 401/403
  session clearing, and consistent error messages.
- Add shared view helpers for loading, empty, error, and success states.
- Add route-level role visibility for customer, seller, and admin navigation;
  keep all authorization enforced by the API.
- Add a small frontend test strategy for route resolution, session handling,
  form validation, and API error behavior.
- Do not calculate prices, fees, balances, refunds, or payout values in the UI.

### FE-02: Public marketplace and customer discovery

Routes:

```text
/
/catalog
/products/:uuid
```

- Build a public product catalog using active/public product responses.
- Add search, category filtering, sorting, and pagination-ready UI state.
- Add product detail with cover, title, seller, price, description, preview,
  FAQ/review placeholders, and purchase CTA.
- Design empty, loading, unavailable, and error states before connecting data.

### FE-03: Authentication and account entry

Routes:

```text
/auth
/settings
```

- Keep signup customer-only.
- Preserve the existing login/signup segmented control and session behavior.
- Show role-aware account navigation after login.
- Show “Become a seller” only for eligible customers.
- Provide clear inactive-account, invalid-credentials, expired-session, and
  forbidden responses.

### FE-04: Checkout and payment

Routes:

```text
/checkout/:productUuid
/checkout/:productUuid/success
/checkout/:productUuid/failure
```

- Create the internal order first through the backend.
- Create the provider payment order through the backend.
- Launch Razorpay checkout using server-provided values.
- Confirm payment through the backend and wait for the authoritative order
  response.
- Never mark an order paid from browser-only state.
- Handle cancellation, payment failure, retry, duplicate confirmation, and
  webhook-delay states.

### FE-05: Customer library and protected downloads

Routes:

```text
/library
/library/:orderUuid
/library/:orderUuid/invoice
```

- Render purchase history from `/v1/ledger/purchases/`.
- Show payment, refund, access, expiry, and download-limit states from the API.
- Request a short-lived delivery response only when the user selects a file.
- Use the returned protected URL and single-use delivery token.
- Provide invoice access and clear revoked/expired/download-limit states.

### FE-06: Seller workspace

Routes:

```text
/seller
/seller/products
/seller/products/new
/seller/products/:uuid
/seller/orders
/seller/payouts
/seller/settings
```

- Build seller overview from dashboard and payout summary APIs.
- List seller-owned products from `/v1/products/mine/`.
- Add product creation, draft state, asset upload, upload completion, and
  publish readiness indicators.
- Add seller order and customer views using scoped ledger responses.
- Show available balance, pending balance, payout readiness, payout holds, and
  payout history without client-side financial calculations.
- Display suspended, payout-held, and incomplete-profile states prominently.

### FE-07: Seller onboarding completion

Routes:

```text
/become-seller
/seller-application/status
```

- Keep the implemented draft, submit, withdraw, needs-information, rejected,
  and approved states.
- Add clear progress and next-action messaging.
- After approval, redirect to a seller activation checklist.
- Link profile completion, payout readiness, first product, asset verification,
  and first publish action into one checklist.

### FE-08: Admin operations

Routes:

```text
/admin
/admin/seller-applications
/admin/orders
/admin/refunds
/admin/payouts
/admin/flags
```

- Expand the existing seller application queue with detail, review history,
  approve, reject, request-information, suspend, and activate actions.
- Add reconciliation summaries for payments, refunds, uploads, and payouts.
- Add admin order/refund detail and invoice visibility.
- Add confirmation dialogs for approval, rejection, suspension, payout retry,
  and other irreversible actions.

## Frontend Implementation Status

The frontend implementation is being rebuilt around the marketplace product
flow while preserving the current static SPA and `apps/web/server.py` server.
The implementation must remain thin: the browser renders server state,
collects input, and calls the API; it must not become a second business layer.

### Frontend structure rules

- Keep runtime configuration in `apps/web/src/config/`.
- Keep route names, API paths, roles, labels, storage keys, and UI defaults in
  `apps/web/src/constants/`.
- Keep HTTP/session behavior in `apps/web/src/services/`.
- Keep screen rendering in `apps/web/src/views/` and keep `src/app.js` focused
  on orchestration, routing, and shared state.
- Do not hard-code API URLs, roles, route strings, currency defaults, or status
  labels inside controllers or templates.
- Do not calculate platform fees, taxes, balances, refunds, payouts, or order
  state in the client. Display values returned by the backend.
- Escape server-provided content before inserting it into HTML.
- Treat local storage as a session cache only; authorization remains backend
  enforced.

### FE-09: Marketplace shell and shared frontend foundation

- Replace the creator-only shell with a responsive marketplace shell that can
  render public catalog pages and authenticated workspaces.
- Add central config/constants modules and a single API client with bearer
  attachment, JSON parsing, timeout handling, and consistent 401/403 clearing.
- Add shared loading, empty, error, toast, currency, date, and escaping helpers.
- Keep the existing Python static server and ES-module browser runtime.

### FE-10: Marketplace discovery implementation

- Implement `/`, `/catalog`, and `/products/:productUuid` using the public
  product endpoint.
- Add search/category/sort UI state without assuming server-side filtering is
  available; pass query parameters only when the API supports them.
- Render product cover placeholders safely when image metadata is unavailable.
- Provide a guest-safe sign-in path and role-aware account actions.

### FE-11: Authenticated customer and seller workspace

- Implement `/library`, `/seller`, `/seller/products`, and `/seller/payouts`
  against the existing purchase, dashboard, product, and payout endpoints.
- Preserve seller onboarding and admin seller-review routes already supported by
  the backend.
- Keep product creation restricted by backend response and expose seller
  actions only as UX affordances.

### FE-12: Validation and handoff

- Validate JavaScript syntax for every module.
- Smoke-test the static server and SPA fallback routes.
- Verify that no frontend module contains a hard-coded API base URL or business
  calculation.
- Update `apps/web/README.md` with the module layout, configuration contract,
  route map, and local run instructions.

### FE-09: Responsive, accessibility, and release pass

- Support desktop sidebar, tablet condensed navigation, and mobile stacked
  layouts.
- Maintain visible keyboard focus, semantic labels, 44px touch targets, and
  WCAG AA color contrast.
- Add skeletons that preserve layout and do not shift content.
- Test browser refresh, back/forward navigation, deep links, expired sessions,
  slow API responses, duplicate submits, and offline failures.

## Frontend Style Plan

The style direction is an extension of the existing DigiSutra application, not
a visual reset. Preserve the current `DS` seal, paper-like neutral surfaces,
left navigation shell, editorial headings, IBM Plex utility typography, and
quiet operational tone from `Design.md` and the current `styles.css`.

### Visual principles

- Quiet professionalism: calm, precise, editorial, and trustworthy.
- Content first: products, purchase state, balances, and actions receive the
  strongest hierarchy.
- Borders and spacing communicate grouping; shadows remain subtle.
- Use one accent at a time and reserve status colors for meaning.
- Avoid gradients, decorative illustrations, glass panels, excessive pills,
  noisy charts, and animation that delays an action.

### Existing application references to preserve

- `DS` seal as the brand marker and avatar fallback.
- Stable sidebar and topbar shell for authenticated workspaces.
- Fraunces-style editorial display headings for page titles where already used.
- IBM Plex Sans for interface text and IBM Plex Mono for identifiers, dates,
  amounts, and operational metadata.
- Neutral background, thin borders, compact status stamps, owner chips, and
  restrained toast feedback.

### Token direction

Define shared CSS custom properties before expanding screens:

```css
--surface-canvas: #f3f1ec;
--surface-panel: #fbfaf7;
--surface-raised: #ffffff;
--ink-strong: #20221f;
--ink-muted: #70736d;
--line-subtle: #deded8;
--accent-primary: #315f8c;
--status-success: #4f7a61;
--status-warning: #a47735;
--status-danger: #a5524a;
--radius-sm: 6px;
--radius-md: 10px;
--shadow-soft: 0 8px 24px rgba(32, 34, 31, 0.07);
```

The exact values may be tuned against the existing stylesheet, but all new
screens should consume tokens rather than inventing local colors or spacing.

### Component language

- Buttons: primary, secondary, danger, and ghost variants with consistent
  height, focus, disabled, loading, and hover behavior.
- Forms: shared labels, required markers, help text, inline errors, and submit
  states.
- Cards: modest radius, thin border, clear heading, and one primary action.
- Tables/lists: readable rows, secondary metadata, status stamps, and actions
  aligned to the right.
- Status: use text plus color; never communicate state by color alone.
- Dialogs: use only for destructive or focused review/payment actions.
- Charts: only when a trend materially improves understanding; prioritize
  values and labels over decoration.

### Motion

- Use 180–220ms fade, opacity, scale, or short slide transitions.
- Prefer skeletons and immediate layout over long spinners.
- Respect `prefers-reduced-motion`.

## Frontend Definition of Done

- Every screen has loading, empty, error, and success states.
- Every authenticated request uses the shared API client.
- No client-side financial, role, ownership, or permission decisions are
  treated as authoritative.
- Desktop, tablet, and mobile layouts are usable.
- Keyboard and screen-reader paths are tested.
- Visual decisions match the style plan and existing DigiSutra shell.
- Frontend changes are committed in feature-sized, reviewable commits.

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
bound to the authenticated user and a verified, single-use delivery token.
Download counts are incremented at consumption time, and paid-order,
asset/order, expiry, and access-limit checks are enforced at that boundary.

- Keep delivery authorization tied to the authenticated buyer, paid order,
  matching product, granted access, expiry, and download limit.
- Validate download-log identity and order fields from the authenticated
  request/delivery context instead of accepting caller-provided identity data.
- Verify delivery tokens at the consumption boundary and prevent replay or
  cross-asset/cross-order use where the delivery endpoint requires it.
- Commit message: `fix(auth): bind asset downloads to verified delivery access`

### AUTH-07: Add authorization regression coverage and web contract

Status: implemented in code and focused/integration tests are checked in;
execution requires the API dependencies and a working test environment.

- Add tests for IDOR attempts across users, sellers, orders, products, assets,
  and payouts, including inactive accounts and role changes.
- Document the frontend token-storage, 401, and 403 contract and update the
  static client to clear stale sessions on authentication failure.
- Run the API test suite and verify the documented route matrix against the
  registered Flask routes. The test suite now includes the protected-route
  matrix, signup role stripping, inactive-user login, and delivery-token
  tampering/replay cases.
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
