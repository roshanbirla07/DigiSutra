# DigiSutra

DigiSutra is a digital marketplace for selling downloadable or consumable digital products such as PDFs, prompts, templates, and other information products.

The product is designed around trust, payment safety, and creator monetization:
- creators can list digital products
- buyers can purchase and access content securely
- the platform tracks orders, payments, payouts, refunds, and support issues
- the dashboard will later show sales, analytics, and settlement status

## Product Plan

### Who uses the platform

#### Seller / Creator
Creators upload and sell digital products.
They will be able to:
- create product listings
- update product details
- track sales and revenue
- see pending payouts and paid payouts
- handle customer issues and refunds where allowed
- view analytics for products and transactions

#### Buyer / Customer
Buyers purchase digital content from sellers.
They will be able to:
- sign up and log in
- browse products
- pay securely
- access purchased content
- view order history
- request help for failed delivery or refund issues

#### Admin / Platform Operator
Admins manage trust and platform health.
They will be able to:
- review users and sellers
- moderate listings
- approve or block content where needed
- review disputes and refund requests
- manage seller payout issues
- monitor failed payments, webhook issues, and fraud signals

## What the platform will provide

### Payments and trust
- Razorpay-based payment collection first
- payment verification through backend logic
- order and transaction tracking in the database
- seller balance and payout tracking
- refund and dispute records
- secure handling of payment states
- audit trail for every important money-related action

### Seller dashboard
The seller dashboard will eventually show:
- total sales
- completed orders
- pending payments
- payout balance
- payout history
- refund count
- product performance
- customer issues and support status

### Analytics dashboard
The analytics surface will eventually show:
- daily and monthly sales trends
- conversion and checkout performance
- top-selling products
- refund trends
- payout summaries
- failed payment trends
- buyer activity patterns

### Support and trust tools
- order lookup
- payment status lookup
- access status lookup
- refund/dispute history
- seller suspension and moderation status
- webhook and payment failure logs

## Roadmap

### Phase 1: Core marketplace foundation
- user signup and login
- seller/customer/admin role model
- product listing model
- product ownership rules
- basic catalog and listing visibility

Phase 1 is now implemented in the current codebase through:
- `POST /v1/users/`
- `POST /v1/users/login/`
- `GET /v1/products/`
- `POST /v1/products/`
- `GET /v1/products/<product_uuid>/`

### Phase 2: Payment and transaction ledger
- Razorpay payment collection
- payment verification
- internal order records
- transaction history
- webhook-based payment confirmation
- failure and retry handling

### Phase 3: Seller earnings and payouts
- commission calculation
- seller balance tracking
- payout ledger
- payout batch workflow
- manual or semi-manual payout execution
- payout failure tracking

### Phase 4: Digital delivery and access control
- purchase-based content access
- signed download URLs
- download and re-download policy
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

## Contribution Guide

This project should be contributed to with the following rules in mind:
- payment and ledger data must be treated as source-of-truth data
- webhook events must be idempotent
- all money-related state changes must be stored in the database
- provider-specific logic must stay behind a service or adapter layer
- seller payout logic must not be mixed with buyer payment collection logic
- dashboard views must read from internal records, not from client-side assumptions
- access to digital content must be tied to an order, not just a session
- auth and role checks should be added before exposing seller or admin operations

### What should remain stable
- user model and role names
- order and transaction identifiers
- payment status transitions
- payout status transitions
- refund history
- audit trail records

### What can change later
- payment gateway providers
- payout execution method
- dashboard layout
- notification channel
- moderation workflow detail

## Operational Rules

- Razorpay is the first payment provider.
- Seller payouts start manual or semi-manual.
- The platform should maintain an internal ledger even if Razorpay is the gateway.
- Tax and invoice support should be designed early.
- Test mode and live mode must never be mixed.
- Logs should capture payment failures, webhook failures, and payout failures.
- Admin tools should be able to suspend creators and hold payouts if needed.

## Current Backend State

The current codebase includes:
- user signup
- user login
- PostgreSQL-backed Flask API
- Docker-based local development setup
- buyer/customer, seller, and admin role definitions

## Roles

Current role types in the codebase:
- `customer`
- `seller`
- `admin`

These roles are the base for future permissions:
- customers buy content
- sellers create and manage listings
- admins manage trust, disputes, and moderation

## Local Development

Run the Flask app directly only if PostgreSQL is available locally and `POSTGRES_DB_URI` or `local_config.py` points to the correct host.

Start the app:

```bash
python src/runserver.py
```

## Docker Setup

Start the full stack:

```bash
docker compose up --build
```

Start in detached mode:

```bash
docker compose up -d --build
```

Stop the stack:

```bash
docker compose down
```

## Service URLs

- API: `http://localhost:5000`
- PostgreSQL: `localhost:5432`

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

## Current Endpoints

- `POST /v1/users/` - create a user
- `POST /v1/users/login/` - login with username and password
- `GET /v1/users/` - list users
- `GET /v1/products/` - list public active products
- `POST /v1/products/` - create a product for a seller or admin owner
- `GET /v1/products/<product_uuid>/` - fetch a public active product by uuid

## Notes

- The app uses PostgreSQL and Flask-SQLAlchemy.
- Docker Compose starts `digisutra-postgres` and `digisutra-api`.
- User onboarding and login are implemented; marketplace, payments, payouts, delivery, moderation, and dashboard work are planned next.
- The README is intended to serve as a contributor-facing project guide, not only a setup note.

## TODO

- Add `image_uri` to the product model and product APIs.
- Fetch `owner_uuid` from the auth token once the authentication layer is added.
