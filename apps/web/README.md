# Web App

This is the DigiSutra frontend workspace.

Current UI is a static client that talks to the existing Flask API:

- `POST /v1/users/`
- `POST /v1/users/login/`
- `GET /v1/users/`
- `GET /v1/products/`
- `POST /v1/products/`

Serve this directory with a static server so ES modules can load correctly.
In Docker Compose, the web app runs on `http://localhost:3000` and the API runs on `http://localhost:5000`.

Rules:

- UI stays minimal and content-first.
- Business logic stays on the backend.
- Role and permission checks remain server-enforced.
