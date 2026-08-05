# DigiSutra Plan

## Status

The platform already has the first working slice of the marketplace:
- Flask backend on PostgreSQL
- user signup and login
- product catalog endpoints
- internal ledger models
- Razorpay order creation, confirmation, and webhook handling
- refund bookkeeping
- seller balance tracking
- asset upload and download tracking
- CloudFront and S3 support for product delivery
- static frontend app under `apps/web/`
- explicit ledger transition validation for order and refund state changes
- payout state transitions and batch processing

## Current Priorities

1. Finish purchase-to-access flow
- grant access from successful orders
- keep downloads tied to purchased orders
- revoke access on refund
- define re-download limits and expiry rules
- return a true protected delivery response for purchased assets

2. Add seller payout workflow
- track pending and available seller balances
- introduce payout batches
- support manual or semi-manual payout execution
- record payout failures and retries
- finalize payout batch reconciliation and retry handling

3. Add trust and moderation controls
- seller suspension
- listing review or flagging
- dispute and support workflow
- fraud and abuse signals

4. Build dashboard views on top of stable backend records
- seller sales summary
- payout summary
- refund summary
- product performance
- transaction reporting

5. Add operational safeguards
- separate test and live payment settings
- reconciliation reports
- logging and alerting for payment, webhook, and payout failures
- compliance and tax/invoice foundation

## Frontend Readiness Gaps

Before the frontend work is treated as fully unblocked, the backend should also have:

- a signed, short-lived asset delivery response
- buyer purchase-history endpoints for orders and downloads
- seller-owned product views for dashboard use
- refund/admin workflow endpoints or summary views
- payout summary endpoints for seller and admin screens
- a standard token-storage and 401/403 response contract for the web app

## Near-Term Build Order

1. Add refund-driven access revocation and policy limits
2. Return protected delivery responses for purchased assets
3. Implement moderation and support tooling
4. Expose dashboard summaries
5. Add operational safeguards and reconciliation support
6. Add payout retry and reconciliation handling

## Working Rules

- Internal ledger records are the source of truth.
- Webhook handlers must be idempotent.
- Provider-specific logic stays in service layers.
- Buyer payments and seller payouts stay separate.
- UI should read from backend records, not infer financial state client-side.
- Access to content must always be tied to a paid order.
- Ledger transitions should be validated centrally before writes are committed.
- Payout transitions should be validated centrally before batch execution.

## Success Criteria

- A buyer can pay, receive access, and download purchased content.
- Duplicate payment webhooks do not create duplicate orders or balances.
- A refund reverses seller earnings and removes access when required.
- Payouts can be tracked independently from buyer payments.
- Admin and seller views can be built from the ledger without ad hoc calculations.
- Invalid order/refund state combinations are rejected before they reach persistence.
- Invalid payout state combinations are rejected before they reach persistence.
