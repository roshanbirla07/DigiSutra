# API App

This directory is the Flask backend application for DigiSutra.

Current backend code lives under `apps/api/src/`.
The Flask app keeps the existing module boundaries while the monorepo layout
separates deployable apps from shared packages.

## Notes

- Backend source of truth remains the Flask app and PostgreSQL models.
- Frontend should not introduce business logic that belongs to the API.
