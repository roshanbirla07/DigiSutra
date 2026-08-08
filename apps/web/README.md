# Web App

This is the DigiSutra frontend workspace. It is a static ES-module SPA served
by `server.py`; it does not own marketplace or financial business logic.

Current UI is a static client that talks to the existing Flask API:

- `GET /v1/products/`
- `GET /v1/products/<product_uuid>/`
- `POST /v1/users/`
- `POST /v1/users/login/`
- `GET /v1/ledger/purchases/`
- `GET /v1/dashboard/summary/`
- `GET /v1/products/mine/`
- `GET /v1/payouts/summary/`

Serve this directory with a static server so ES modules can load correctly.
The project includes `server.py`, which serves the SPA on `http://localhost:3000`
and falls back to `index.html` for client-side routes.

In Docker Compose, the web app runs on `http://localhost:3000` and the API runs on `http://localhost:5000`.

Current frontend routes:

- `/`
- `/catalog`
- `/products/:productUuid`
- `/auth`
- `/library`
- `/seller`
- `/seller/products`
- `/seller/products/new`
- `/seller/payouts`

## Module layout

- `src/config/runtime.js` — runtime API base URL and request settings. A
  deployment may set `window.DIGISUTRA_CONFIG` before loading the app.
- `src/constants/app.js` — routes, API paths, roles, storage keys, and product
  copy/defaults.
- `src/services/api.js` — fetch wrapper, bearer token attachment, timeouts,
  JSON parsing, and 401/403 session handling.
- `src/services/storage.js` — session cache only.
- `src/views/` — escaped HTML rendering and shared presentation helpers.
- `src/app.js` — route orchestration, shared state, form events, and view calls.

The API base URL defaults to the current host on port `5000`. To override it in
a deployment, provide configuration before `src/app.js`:

```html
<script>
  window.DIGISUTRA_CONFIG = { apiBaseUrl: "https://api.example.com" };
</script>
```

Rules:

- UI stays minimal and content-first.
- Business logic stays on the backend.
- Role and permission checks remain server-enforced.
- Do not hard-code API URLs or business values in views.
- Do not calculate fees, taxes, balances, refunds, payouts, or order states in
  the browser.
- Escape API-provided values before inserting them into HTML.
