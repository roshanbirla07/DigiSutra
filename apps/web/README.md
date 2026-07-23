# Web App

This is the DigiSutra frontend workspace.

Current UI is a static client that talks to the existing Flask API:

- `POST /v1/users/`
- `POST /v1/users/login/`
- `GET /v1/users/`
- `GET /v1/products/`
- `POST /v1/products/`

Serve this directory with a static server so ES modules can load correctly.
The project includes `server.py`, which serves the SPA on `http://localhost:3000`
and falls back to `index.html` for client-side routes like `/product`,
`/products`, and `/settings`.

In Docker Compose, the web app runs on `http://localhost:3000` and the API runs on `http://localhost:5000`.

Current frontend routes:

- `/auth`
- `/dashboard`
- `/product`
- `/products`
- `/settings`

Rules:

- UI stays minimal and content-first.
- Business logic stays on the backend.
- Role and permission checks remain server-enforced.
