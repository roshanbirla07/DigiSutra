# Frontend Reference

This file is the source of truth for frontend implementation rules.

Use this file before making any frontend change. If a future frontend task conflicts with this file, update this file first and then implement the code.

## Point Zero

- Do not keep business logic on the client side.
- The client should render state, collect input, and call backend APIs.
- Validation that affects trust, money, roles, ownership, or permissions must live on the backend.
- The client may do only lightweight UI validation for user experience, such as required fields, format hints, and button state.
- Any computed value that changes business meaning must come from the server, not from the browser.
- Frontend role checks are only for UX gating; they are never the source of truth for access control.

## Current Rules

- Auth state must come from the backend response or token payload, not from local assumptions.
- Role checks that protect data or actions must be enforced on the server.
- Product ownership must be treated as backend source-of-truth.
- Pricing, commission, payout, refund, and order calculations must not be trusted from the client.
- The frontend may display derived values, but those values must be treated as read-only presentation.

## How To Extend This File

- Add new rules as numbered sections or short bullets.
- Keep backend-trust rules near the top.
- Add feature-specific rules only after the shared foundation rules.
- When a new frontend task needs a product decision, record it here first.

## Suggested Sections For Later

- Auth and session handling
- Product listing and product editor rules
- Checkout and payment UI rules
- Seller dashboard rules
- Buyer order history rules
- Admin moderation rules
- API error handling rules
- Form validation rules
