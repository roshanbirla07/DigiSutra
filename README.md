# DigiSutra

> A secure digital marketplace for selling and delivering downloadable products such as PDFs, templates, prompts, guides, and other digital assets.

DigiSutra is a full-stack marketplace focused on **secure payments, controlled digital delivery, seller operations, and platform trust**. The backend is built with Flask and PostgreSQL, while private product assets are delivered through S3 using short-lived signed URLs.

---

## ✨ What DigiSutra supports

- Customer signup and authentication
- Seller onboarding and approval workflow
- Product creation and public marketplace listings
- Razorpay checkout, payment verification, and webhooks
- Internal order, refund, payout, and seller-balance ledger
- Private S3 uploads through presigned URLs
- Purchase-based digital asset access
- Short-lived, single-use delivery authorization
- Buyer purchase history
- Seller dashboard and payout visibility
- Admin moderation, support, reconciliation, and seller controls

---

## 🧱 Architecture

```text
Browser
  │
  ├── Web App :3000
  │
  ▼
Flask API :5000
  │
  ├── PostgreSQL
  │     ├── users
  │     ├── products
  │     ├── orders
  │     ├── refunds
  │     ├── payouts
  │     └── access / audit records
  │
  ├── Razorpay
  │     ├── checkout
  │     ├── payment verification
  │     └── webhooks
  │
  └── Private S3
        ├── presigned uploads
        └── signed downloads
```

The application keeps its own marketplace ledger even when an external payment provider is used. Payment, refund, delivery, and payout state are validated by the backend rather than trusted from the client.

---

## 🛠 Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | PostgreSQL |
| ORM / migrations | SQLAlchemy, Alembic |
| Frontend | Static web client |
| Payments | Razorpay |
| Storage | Amazon S3 |
| Containers | Docker, Docker Compose |
| Authentication | EdDSA-signed bearer tokens |

---

## 📁 Repository structure

```text
DigiSutra/
├── apps/
│   ├── api/          # Flask backend
│   └── web/          # Web client
├── packages/
│   └── shared/       # Shared code / future common modules
├── deploy/           # Deployment assets when applicable
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## 🚀 Quick start with Docker

### 1. Clone the repository

```bash
git clone https://github.com/roshanbirla07/DigiSutra.git
cd DigiSutra
```

### 2. Create local configuration

```bash
cp .env.example .env

cp apps/api/src/configuration/instance_config.example.py \
  apps/api/src/configuration/instance_config.py
```

For Docker, set the PostgreSQL host in `instance_config.py` to:

```python
POSTGRES_HOST = "postgres"
```

Keep the database name, username, and password aligned with the PostgreSQL values in `.env`.

### 3. Start the stack

```bash
docker compose up --build
```

Run in the background:

```bash
docker compose up -d --build
```

Stop everything:

```bash
docker compose down
```

### Local services

| Service | URL |
|---|---|
| Web | http://localhost:3000 |
| API | http://localhost:5000 |
| PostgreSQL | localhost:5432 |

---

## 💻 Run locally without Docker

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
. .venv/bin/activate

pip install -r requirements.txt
```

Create the machine-specific backend configuration:

```bash
cp apps/api/src/configuration/instance_config.example.py \
  apps/api/src/configuration/instance_config.py
```

Apply database migrations:

```bash
alembic upgrade head
```

Start the API:

```bash
python apps/api/src/runserver.py
```

Start the web app in another terminal:

```bash
python apps/web/server.py
```

---

## ⚙️ Configuration

DigiSutra uses:

```text
prod_config.py
      ↓
stage_config.py
      ↓
dev_config.py
      ↓
local_config.py
      ↓
instance_config.py
```

The machine-specific `instance_config.py` is ignored by Git and should contain deployment secrets and environment-specific values.

Typical configuration includes:

- PostgreSQL connection details
- EdDSA signing keys
- Razorpay credentials
- S3 bucket and AWS region
- CORS origins
- application URLs
- digital-access limits
- payment mode and platform fee

> Never commit real database passwords, AWS credentials, Razorpay secrets, or private signing keys.

---

## 🔐 Security model

DigiSutra keeps sensitive operations server-controlled.

Key rules:

- Public signup creates a customer account only.
- Seller access is granted through the seller-application workflow.
- Authenticated identity determines buyer, seller, and owner scope.
- Client-supplied ownership identifiers do not override the authenticated principal.
- Payment and payout state are derived from backend records.
- Razorpay webhooks must pass signature verification.
- Webhook processing is idempotent.
- Product files remain private in S3.
- Downloads require valid purchase authorization.
- Delivery credentials are short-lived and single-use.
- Refunds can revoke asset access.
- Admin and seller operations use route-level role checks.

---

## 💳 Payments and marketplace ledger

Razorpay is currently the payment provider, but DigiSutra maintains its own ledger for:

- orders
- payment state
- refunds
- seller earnings
- payout reservations
- payout state
- webhook idempotency
- purchase access

This keeps marketplace state auditable and prevents the frontend or payment provider from becoming the source of truth.

---

## 📦 Digital asset delivery

Product files are stored in a private S3 bucket.

Typical flow:

```text
Seller requests upload target
        ↓
API creates asset metadata
        ↓
Browser uploads directly to S3
        ↓
API verifies upload
        ↓
Buyer purchases product
        ↓
API verifies purchase access
        ↓
Short-lived delivery authorization
        ↓
Signed S3 download
```

This avoids routing large files through the application server and keeps original assets private.

---

## 👤 Roles

### Customer

- browse products
- purchase digital content
- access purchased assets
- view purchase history
- open support tickets
- apply to become a seller

### Seller

- create and manage products
- upload digital assets
- view marketplace activity
- track balance and payouts

### Admin

- review seller applications
- moderate products and users
- resolve support and moderation cases
- manage payout operations
- inspect reconciliation risk

---

## 🧪 Tests

Run backend tests:

```bash
python -m unittest discover -s apps/api/tests -p 'test_*.py'
```

Run frontend tests:

```bash
node --test apps/web/tests/*.test.js
```

For schema or database-related changes, also verify that migrations work against a clean PostgreSQL database.

---

## 🗄 PostgreSQL

The production target is Amazon RDS PostgreSQL.

Open the local Docker database:

```bash
docker exec -it digisutra-postgres psql -U postgres -d digisutra
```

Useful commands:

```sql
\dt
SELECT count(*) FROM "user";
```

Check containers:

```bash
docker ps
```

API logs:

```bash
docker logs -f digisutra-api
```

Database logs:

```bash
docker logs -f digisutra-postgres
```

---

## 🔌 API areas

The API is organized around the following domains instead of exposing implementation details in this README:

| Area | Responsibility |
|---|---|
| Users | signup, login, roles |
| Products | marketplace listings and seller products |
| Assets | upload, verification, delivery |
| Orders | purchases and marketplace ledger |
| Payments | Razorpay order creation and confirmation |
| Refunds | refund bookkeeping and access revocation |
| Payouts | seller balances and payout lifecycle |
| Seller applications | onboarding and KYC workflow |
| Support | user support tickets |
| Moderation | product, seller, and user controls |
| Dashboard | seller/admin summaries |
| Reconciliation | operational risk visibility |

For implementation details, inspect the route modules under `apps/api/`.

---

## 🧭 Seller onboarding

Seller access follows a controlled lifecycle:

```text
customer
   ↓
draft
   ↓
kyc_pending
   ↓
kyc_in_review
   ├── needs_information → kyc_pending
   ├── kyc_failed        → kyc_pending
   ├── rejected
   └── kyc_verified
            ↓
         approved
            ↓
          seller
```

The workflow is provider-neutral so an external KYC or fund-account provider can be integrated later without coupling seller state directly to one gateway.

---

## 📌 Engineering principles

When contributing:

- keep payment and ledger data server-owned
- make webhook handling idempotent
- validate state transitions centrally
- enforce resource ownership on the backend
- keep payment collection separate from payout execution
- keep provider-specific integrations behind service boundaries
- tie digital access to actual purchases
- avoid hardcoded secrets or infrastructure values
- add regression coverage for authorization and financial-state changes
- use focused pull requests instead of pushing directly to `main`

---

## 🛣 Roadmap

DigiSutra is being developed incrementally around these areas:

- marketplace and catalog experience
- payments and transaction integrity
- seller earnings and payouts
- secure digital delivery
- seller onboarding and KYC
- support and moderation
- reconciliation and operational tooling
- seller analytics
- production hardening and observability

---

## 🤝 Contributing

1. Create a focused branch.
2. Make one scoped change.
3. Run the relevant tests.
4. Verify migrations when schema changes are involved.
5. Open a pull request against `main`.

Keep pull requests small enough to review and roll back safely.

---

## 📄 License

Add the project license here when finalized.
