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
