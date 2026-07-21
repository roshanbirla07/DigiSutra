# Web App

This is the DigiSutra frontend workspace.

Current UI is a static client that talks to the existing Flask API:

- `POST /v1/users/`
- `POST /v1/users/login/`
- `GET /v1/users/`
- `GET /v1/products/`
- `POST /v1/products/`

Open `index.html` in a browser or serve this directory with any static server.
In Docker Compose, the web app runs on `http://localhost:3000` and the API runs on `http://localhost:5000`.

Rules:

- UI stays minimal and content-first.
- Business logic stays on the backend.
- Role and permission checks remain server-enforced.
