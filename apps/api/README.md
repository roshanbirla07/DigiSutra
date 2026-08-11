# API App

This directory is the Flask backend application for DigiSutra.

Current backend code lives under `apps/api/src/`.
The Flask app keeps the existing module boundaries while the monorepo layout
separates deployable apps from shared packages.

## Notes

- Backend source of truth remains the Flask app and PostgreSQL models.
- Frontend should not introduce business logic that belongs to the API.
- Apply schema changes with `alembic upgrade head` from the repository root.
- `db.create_all()` remains available for local bootstrap only; production
  deployments must run migrations before starting the API.

## Runtime Dependencies

The backend container uses Python 3.13. Runtime dependencies are pinned in
`requirements.txt` so local, CI, and deployment installs resolve the same
Flask, SQLAlchemy, Alembic, psycopg2, Razorpay-adjacent, and AWS client
behavior.

Upgrade dependencies deliberately in a dedicated change:

```bash
python -m pip install --upgrade -r requirements.txt
python -m pip freeze
```

After changing database, auth, payment, or storage dependencies, run the
focused backend tests plus a clean PostgreSQL migration smoke test before
deploying.

## Database Configuration

`POSTGRES_DB_URI` takes precedence when set. If it is omitted, the API builds a
PostgreSQL URL from `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`,
`POSTGRES_HOST`, `POSTGRES_DB_PORT`, and optional `POSTGRES_SSLMODE`.

Local Docker example:

```bash
POSTGRES_DB=digisutra
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=postgres
POSTGRES_DB_PORT=5432
```

Staging example with a full URL:

```bash
POSTGRES_DB_URI=postgresql+psycopg2://digisutra_app:<password>@staging-db.example.internal:5432/digisutra
```

RDS example with SSL required:

```bash
POSTGRES_DB=digisutra
POSTGRES_USER=digisutra_app
POSTGRES_PASSWORD=<password>
POSTGRES_HOST=<rds-private-endpoint>
POSTGRES_DB_PORT=5432
POSTGRES_SSLMODE=require
```

Use a private RDS endpoint, keep the `digisutra` database created before
startup, and verify the security group allows the API runtime to connect before
running migrations.
