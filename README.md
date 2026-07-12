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

## Notes

- The app uses PostgreSQL and Flask-SQLAlchemy.
- Docker Compose starts `digisutra-postgres` and `digisutra-api`.
- User onboarding and login are implemented; marketplace, payments, payouts, delivery, moderation, and dashboard work are planned next.
