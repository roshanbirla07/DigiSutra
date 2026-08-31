# DigiSutra

DigiSutra is a digital marketplace for downloadable or consumable products such as PDFs, prompts, templates, and other information products.

The codebase is organized as a small monorepo:
- `apps/api/` contains the Flask backend
- `apps/web/` contains the static frontend
- `packages/shared/` is reserved for shared code

## Current State

The current backend already includes:
- user signup and login
- EdDSA-signed auth tokens with request-level authentication guards
- PostgreSQL-backed Flask API
- product listing and product fetch endpoints
- marketplace ledger models for orders, refunds, payouts, and access tracking
- Razorpay order creation, checkout verification, and webhook handling
- seller pending-balance tracking
- explicit ledger state checks for payment, delivery, and refund transitions
- payout state transitions and batch processing
- refund bookkeeping with access revocation hooks
- product image and asset metadata
- S3 presigned upload target generation
- verified private S3 uploads and short-lived signed downloads
- authenticated asset delivery authorization tied to paid orders
- configurable download limit and access-expiry enforcement
- download logging and asset status tracking
- support ticket creation and admin resolution
- product flagging and admin moderation actions

The frontend is a static client that talks to the Flask API. Sellers can create
a product and upload its file directly to private S3; paid buyers can download
verified assets from their library through single-use delivery authorization.

Authentication is implemented with EdDSA-signed bearer tokens and route-level
role guards. The main resource-ownership and collection-scoping checks are now
implemented in the API, with regression coverage for authorization, payment
integrity, payout reserves, asset delivery, and token replay prevention.

## Roles

Current role types in the codebase:
- `customer`
- `seller`
- `admin`

Role intent:
- customers buy content
- sellers create and manage listings
- admins handle moderation, disputes, and trust operations

## Current API Surface

- `POST /v1/users/` - create a user
- `POST /v1/users/login/` - login with username and password
- `GET /v1/users/` - list users (admin only)
- `GET /v1/products/` - list public active products
- `POST /v1/products/` - create a product for a seller or admin owner
- `GET /v1/products/<product_uuid>/` - fetch a public active product by uuid
- `POST /v1/assets/upload-target/` - create a product asset and return a presigned upload URL
- `POST /v1/assets/<asset_uuid>/complete/` - verify a direct S3 upload
- `POST /v1/assets/<asset_uuid>/deliver/` - authorize a download for a purchased asset and return a short-lived delivery token
- `POST /v1/assets/<asset_uuid>/downloads/` - log a product asset download (requires `X-Asset-Delivery-Token`)
- `GET /v1/ledger/orders/` - list marketplace ledger orders (buyer/seller scoped, admin all)
- `GET /v1/ledger/purchases/` - list the authenticated buyer's purchase history
- `GET /v1/dashboard/summary/` - get a seller or admin dashboard summary
- `GET /v1/ops/reconciliation-summary/` - get admin-facing reconciliation risk buckets
- `GET /v1/payouts/` - list payouts (seller-scoped, admin all)
- `GET /v1/payouts/summary/` - get seller balance, payout readiness, and payout history
- `POST /v1/payouts/` - create a payout record for a seller or admin
- `POST /v1/payouts/batch/` - process a payout batch as admin
- `POST /v1/payouts/<payout_uuid>/retry/` - retry a failed payout as admin
- `POST /v1/payouts/<payout_uuid>/cancel/` - cancel an eligible payout and release its reserve
- `GET /v1/payouts/reconciliation-summary/` - get payout reconciliation details for admin
- `GET /v1/ledger/orders/<order_uuid>/` - fetch a marketplace ledger order by uuid (buyer, seller, or admin)
- `POST /v1/ledger/orders/` - create a marketplace ledger order (authenticated buyer identity enforced)
- `POST /v1/ledger/orders/<order_uuid>/` - create a refund for an order (buyer or admin)
- `GET /v1/support/tickets/` - list support tickets for the authenticated user, or all tickets for admin
- `POST /v1/support/tickets/` - create a support ticket
- `POST /v1/support/tickets/<ticket_uuid>/resolve/` - resolve a support ticket as admin
- `POST /v1/moderation/products/<product_uuid>/flags/` - flag a product for review
- `POST /v1/moderation/product-flags/<flag_uuid>/resolve/` - resolve a product flag as admin
- `POST /v1/moderation/users/<user_uuid>/suspend/` - suspend a user as admin
- `POST /v1/moderation/users/<user_uuid>/activate/` - reactivate a user as admin
- `POST /v1/moderation/sellers/<user_uuid>/suspend/` - suspend seller operations and hold payouts
- `POST /v1/moderation/sellers/<user_uuid>/activate/` - reactivate seller operations
- `POST /v1/moderation/sellers/<user_uuid>/payout-readiness/` - set seller payout readiness as admin
- `GET /v1/products/mine/` - list the authenticated seller's products
- `GET /v1/ledger/orders/<order_uuid>/invoice/` - create or fetch an order invoice
- `GET /v1/seller-applications/` - get the authenticated customer's seller application
- `POST /v1/seller-applications/` - save a seller application draft
- `PATCH /v1/seller-applications/` - update a seller application draft
- `POST /v1/seller-applications/submit/` - submit a seller application for review
- `POST /v1/seller-applications/<application_uuid>/withdraw/` - withdraw an application
- `GET /v1/admin/seller-applications/` - list seller applications as admin
- `GET /v1/admin/seller-applications/<application_uuid>/` - view an application as admin
- `POST /v1/admin/seller-applications/<application_uuid>/request-information/` - request more information
- `POST /v1/admin/seller-applications/<application_uuid>/start-kyc-review/` - move a seller application into KYC review
- `POST /v1/admin/seller-applications/<application_uuid>/verify-kyc/` - mark KYC and fund-account validation complete
- `POST /v1/admin/seller-applications/<application_uuid>/fail-kyc/` - fail KYC with a required reason
- `POST /v1/admin/seller-applications/<application_uuid>/reject/` - reject an application
- `POST /v1/admin/seller-applications/<application_uuid>/approve/` - approve and promote a KYC-verified customer to seller
- `POST /v1/payments/orders/` - create a Razorpay order for an internal ledger order
- `POST /v1/payments/confirm/` - verify checkout signature and mark payment paid
- `POST /v1/payments/webhook/razorpay/` - process Razorpay payment webhooks idempotently

Delivery tokens are verified again at consumption, bound to the authenticated
buyer and requested asset/order, and recorded as single-use credentials.
Download counts are incremented only when a token is consumed. Authorization
regression tests cover the protected route matrix, signup role stripping,
inactive users, tampered delivery data, and replay handling. Running those
tests still requires the API dependencies and a working test environment.

Public signup is customer-only. Prices, fees, order ownership, payment state,
and payout state are derived or enforced by the server. Razorpay webhooks require
a valid signature before any event is processed.

## Local Development

Install dependencies and create the machine-specific configuration file:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp apps/api/src/configuration/instance_config.example.py \
  apps/api/src/configuration/instance_config.py
alembic upgrade head
```

Put the database, EdDSA, Razorpay, S3, application URL, and CORS values directly
in `instance_config.py`. This file overrides `local_config.py` and is ignored by
Git, so the server-specific values are not committed. The API does not read
runtime configuration through `os.getenv`.

Start the backend:

```bash
python apps/api/src/runserver.py
```

Serve the frontend:

```bash
python apps/web/server.py
```

Run verification locally:

```bash
python -m unittest discover -s apps/api/tests -p 'test_*.py'
node --test apps/web/tests/*.test.js
```

Pull requests and pushes to `main` run the same backend/frontend checks plus a
clean PostgreSQL 18.3 migration in GitHub Actions.

## Docker

Start the full stack:

```bash
cp .env.example .env
cp apps/api/src/configuration/instance_config.example.py \
  apps/api/src/configuration/instance_config.py
docker compose up --build
```

For Docker development, set `POSTGRES_HOST = "postgres"` in
`instance_config.py` and keep its database name, user, and password aligned
with the three PostgreSQL values in `.env`. Docker Compose uses `.env` only to
initialize its PostgreSQL container; the API reads `instance_config.py`.

Start in detached mode:

```bash
docker compose up -d --build
```

Stop the stack:

```bash
docker compose down
```

Service URLs:
- API: `http://localhost:5000`
- Web: `http://localhost:3000`
- PostgreSQL: `localhost:5432`

## PostgreSQL and RDS Compatibility

Production target: Amazon RDS PostgreSQL 18.3 with database name `digisutra`.
Local Docker PostgreSQL should match the production major/minor version for
schema work; PostgreSQL 17 can stay available for older local data, but it must
not be the only migration test target.

The migration chain includes the core schema and is exercised from an empty
PostgreSQL 18.3 database in CI.

Rules for every database compatibility task:
- Check current official documentation before implementation.
- List production edge cases before changing code.
- Implement one scoped task at a time.
- Run the relevant backend tests and PostgreSQL 18.3 migration smoke test when
  schema or connection behavior changes.
- Update this README with the new command, policy, or operational note.
- Commit the completed task before starting the next flow.

References used for the compatibility plan:
- AWS RDS PostgreSQL SSL guidance: RDS PostgreSQL 15 and later can require SSL
  by default through `rds.force_ssl`, so production URLs should support SSL
  mode.
- Alembic reads the database URL from the same Python configuration used by the
  application.
- SQLAlchemy guidance: PostgreSQL URLs should use the
  `postgresql+psycopg2://` driver form with explicit user, password, host,
  port, database, and optional query parameters.
- PostgreSQL 18 release notes: MD5 password authentication is deprecated, so
  production should use SCRAM-compatible users and modern clients.

Do not commit real RDS endpoints, passwords, AWS access keys, Razorpay secrets,
or private EdDSA keys. Put them only in the ignored server-side
`instance_config.py` file and restrict that file's operating-system permissions.

## Asset Storage

Original product files are stored in private S3 buckets.
Canonical asset metadata is stored in PostgreSQL.
Uploads use presigned S3 `PUT` URLs generated by the API.
Downloads use short-lived presigned S3 `GET` URLs and a single-use application
token. Downloads are logged in PostgreSQL and each asset keeps a status field.
The configured bucket must allow browser CORS for the deployed web origin.

Required `instance_config.py` values for asset delivery:
- `AWS_REGION`
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` when an IAM role is not used
- `AWS_S3_BUCKET_NAME`
- `AWS_CLOUDFRONT_DOMAIN`
- `AWS_S3_PRESIGN_EXPIRES_IN`
- `AWS_S3_UPLOAD_PREFIX`

## Payments

Razorpay is the first payment provider.
The platform keeps its own internal ledger for:
- payment verification
- order state
- seller balance tracking
- refund tracking
- webhook idempotency

Required `instance_config.py` values for payment flow integration:
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`
- `RAZORPAY_WEBHOOK_SECRET`
- `PAYMENT_MODE` (`test` or `live`)
- `PLATFORM_FEE_PERCENT`

Required `instance_config.py` values for auth tokens:
- `AUTH_EDDSA_PRIVATE_KEY_PEM`
- `AUTH_EDDSA_PUBLIC_KEY_PEM`

Optional `instance_config.py` access policy values:
- `ASSET_ACCESS_MAX_DOWNLOADS`
- `ASSET_ACCESS_EXPIRES_IN_DAYS`
- `ASSET_DELIVERY_TOKEN_TTL_SECONDS`

## Deployment dependencies

The code-level release blockers are covered, but a real deployment still needs
operator-owned configuration outside the repository:

- PostgreSQL/RDS credentials and migrations
- EdDSA signing keys
- a private S3 bucket with web-origin CORS and either an IAM role or AWS keys
- Razorpay test/live credentials and a webhook configured with the same secret
- `CORS_ALLOWED_ORIGINS` in `instance_config.py` set to the deployed frontend origin(s)
- a real KYC/fund-account provider if onboarding should be automated; the
  current workflow remains provider-neutral and supports controlled manual review

## Roadmap

### Seller onboarding workflow

Seller access is granted through a controlled application and KYC lifecycle:

```text
customer -> draft -> kyc_pending -> kyc_in_review
                              -> needs_information -> kyc_pending
                              -> kyc_failed -> kyc_pending
                              -> kyc_verified -> approved -> seller
                              -> rejected or withdrawn
```

Public signup always creates a customer. Admin approval atomically changes the
user role to `seller` and creates a seller profile only after KYC is verified
and fund-account validation is marked complete. Pending applicants cannot use
seller product, payout, or dashboard endpoints.

The current implementation is provider-neutral and records the state needed for
manual review or a future Razorpay integration:
- `kyc_status`: `not_started`, `pending`, `in_review`, `verified`, `failed`, or
  `needs_information`
- `provider`: `manual` by default, later usable for `razorpay_route`,
  `razorpayx`, or another gateway
- `provider_account_id` and `provider_account_status`
- `fund_account_status`, which must be `validated` before seller approval and
  payout readiness

Razorpay-aligned flow notes:
- Razorpay Custom Onboarding SDK supports creating client accounts, uploading
  KYC details, generating onboarding URLs, fetching merchant access tokens, and
  receiving activation webhooks.
- Razorpay Route linked accounts expose account states such as created,
  under review, needs clarification, activated, and suspended.
- RazorpayX payouts require contacts, fund accounts, fund-account validation,
  and completed account activation/KYC before payouts.

Sources:
- https://razorpay.com/docs/partners/technology-partners/onboard-businesses/onboarding-sdk/
- https://razorpay.com/docs/api/payments/route/create-linked-account/
- https://razorpay.com/docs/x/fund-account-validation/api/
- https://razorpay.com/docs/x/payouts/

### Phase 1: Core marketplace foundation
- user signup and login
- seller/customer/admin role model
- product listing model
- product ownership rules
- catalog and listing visibility

### Phase 2: Payment and transaction ledger
- Razorpay payment collection
- payment verification
- internal order records
- transaction history
- webhook-based payment confirmation
- failure and retry handling
- explicit state transition validation
- refund lifecycle clarity

### Phase 3: Seller earnings and payouts
- commission calculation
- seller balance tracking
- payout ledger
- payout batch workflow
- manual or semi-manual payout execution
- payout failure tracking
- payout state transitions

### Phase 4: Digital delivery and access control
- purchase-based content access
- signed download URLs
- private object storage for original uploads
- CloudFront delivery for public assets
- presigned upload flow for creators
- download logging and asset status tracking
- access revocation on refund
- purchase history for buyers

### Phase 5: Support, refunds, and trust
- refund requests
- dispute management
- seller moderation
- admin override tools
- support issue tracking
- fraud and abuse signals

### Phase 6: Seller dashboard and analytics
- sales overview
- payout overview
- refund overview
- product analytics
- transaction reporting
- support status

### Phase 7: Platform hardening
- test/live environment separation
- logging and alerting
- reconciliation reports
- compliance review for payouts and taxes
- operational dashboards

## Contribution Rules

- payment and ledger data must be treated as source-of-truth data
- webhook events must be idempotent
- all money-related state changes must be stored in the database
- provider-specific logic must stay behind a service or adapter layer
- seller payout logic must not be mixed with buyer payment collection logic
- dashboard views must read from internal records, not client-side assumptions
- access to digital content must be tied to an order, not just a session
- auth and role checks must be applied before exposing seller or admin operations
- resource ownership and collection scoping must be enforced server-side
- caller-supplied owner, buyer, seller, and user identifiers must not override the authenticated principal
- ledger transitions should be validated centrally, not inferred in controllers
- payout transitions should be validated centrally before batch execution

## Operational Notes

- Seller payouts start manual or semi-manual.
- The platform should maintain an internal ledger even if Razorpay is the gateway.
- Tax and invoice support should be designed early.
- Test mode and live mode must never be mixed.
- Logs should capture payment failures, webhook failures, and payout failures.
- Admin tools should be able to suspend creators and hold payouts if needed.

## Database Checks

Open a PostgreSQL shell inside the container:

```bash
docker exec -it digisutra-postgres psql -U postgres -d digisutra
```

Useful SQL checks:

```sql
\dt
SELECT * FROM "user";
SELECT count(*) FROM "user";
```

Check container status:

```bash
docker ps
```

Check app logs:

```bash
docker logs -f digisutra-api
```

Check database logs:

```bash
docker logs -f digisutra-postgres
```
