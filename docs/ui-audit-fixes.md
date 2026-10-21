# UI audit fixes — issue #18

This change hardens the current vanilla JavaScript client without replacing its Calm Toolkit identity. The work follows `FRONTEND_REFERENCE.md`, `DESIGN.md`, `UX-CONTRACT.md`, the existing seller lifecycle and backend authorization rules.

## Implemented

- Root-relative application assets and 404 responses for missing static resources; nested URL refresh is covered by HTTP regression tests.
- Async route generations, navigable loading/error/403/404 states and authenticated return paths.
- Shared native-dialog review/confirmation with application details, Cancel/Escape handling, retained notes on server error and explicit action labels.
- Duplicate-operation guards and busy semantics for auth, seller submissions, checkout, review and upload.
- Private product drafts, retry by product UUID, owned-list resume links and an authenticated publish endpoint that checks ownership, seller readiness and verified paid assets. No migration is needed; deploy the API before the updated client.
- Correct backend-derived payout readiness and paid payout totals.
- App-owned required/format feedback, field associations, focus, password reveal and correct signup autocomplete.
- Onboarding locked/withdrawable states, invalid-action prevention and a truthful re-login instruction after approval.
- Payment dismissal/failure feedback, single popup/script, bounded script/upload waits (uploads use the existing server-issued signed-URL lifetime) and current-order status check.
- Download controls recover after handoff; all verified assets are offered; order references, unavailable-state reasons and refresh are visible.
- Immediate search clearing, preview reset/stale-read protection, failed-image fallback and visibility-return refresh.
- Storage-restricted in-memory sessions and cross-tab logout handling; unsaved-input guards without storing credentials, bank/KYC details or files as local drafts.
- Honest single-form section labels and account/product-list wording; control-radius and danger-token ownership reconciled.

## Validation

Run:

```bash
npm ci --prefix apps/web
node --test apps/web/tests/*.test.js
python -m unittest discover -s apps/web/tests -p '*_test.py'
python -m unittest discover -s apps/api/tests -p 'test_*.py'
node --check apps/web/src/app.js
git diff --check
```

DOM tests use development-only jsdom with native dialog methods shimmed. They exercise actual DOM events, forms and routing with mocked API responses; they do not prove native modal focus trapping or Razorpay integration. Backend publication tests cover missing/unverified assets, ownership, seller readiness and role protection.

The premium static auditor was run. Its actionless-button candidates are false positives from event delegation across `views/marketplace.js` and `app.js`, plus unused legacy controllers. The shared dialog textarea uses the global resize-none rule. Do not present the strict scanner exit as a clean runtime/accessibility sign-off.

## Still tracked by issue #18

- Real desktop/mobile browser checks, native dialog keyboard/focus restoration, contrast and automated accessibility verification. The known deployed URL returned a certificate error in the audit environment; no security warning was bypassed.
- Real configured S3 and Razorpay sandbox success/failure/reconciliation checks. No live payment or production data mutation was performed.
- Provider-order recovery after a full page refresh, tab closure or uncertain order creation still requires server-backed reconciliation/idempotency. Current guards prevent concurrent requests within the active page and reuse a known order; they do not guarantee deduplication across tabs/devices or an unknown server outcome.
- Non-sensitive form drafts are retained on ordinary validation/mutation failures but are not restored through forced session expiry, a cross-tab logout or a full reload. Files and sensitive seller identity data are deliberately not persisted locally.
- Existing product creation integrations can still choose their original public flags. The hardened web upload workflow uses private drafts; this PR does not silently change all backend callers' lifecycle contract.
- Complete published-product editing/unpublishing/deletion, provider-backed KYC, payout execution and a user-facing support/refund workflow remain product capabilities beyond the current UI. Current labels and order-help text avoid claiming they exist.
- Previously interrupted uploads can be resumed by selecting files again; this is stage retry, not byte-range resumable transfer. An earlier verified file can remain alongside a newly selected one after a full refresh; backend delivery still authorizes every download.

Keep issue #18 open until the remaining runtime checks and provider recovery work are complete.
