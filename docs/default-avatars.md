# Default profile avatars

Account headers, account settings, product cards and product detail bylines reuse `apps/web/src/views/avatar.js`. The helper renders original inline vector portraits, with a username-seeded hash providing stable, random-looking variation. Public creator bylines and signed-in account views use the same username identity. UUID/id provide fallback identities when a username is missing; missing identities share a generic portrait. Display-name, email and role changes do not affect a username's portrait. Changing the username changes its default portrait.

The browser does not persist an avatar choice or call external image services. No user identifiers, email or token appear in SVG markup. Avatars are decorative beside text identity, and account links retain their accessible name. Artwork is independent of the brand palette so the component can also be used in the proposed Indigo + Cloud theme.

The current user API has no photo-upload field. This PR supplies defaults; photo upload and the wider Indigo + Cloud redesign are separate work. No backend, schema, permissions, dependencies or account data change.

Validation:
- `npm test` in apps/web: all 29 tests pass, including three avatar regression tests for identity consistency, missing identity, and malicious input/privacy.
- `python -m unittest discover -s tests -p '*_test.py'` in apps/web: route-serving test passes.
- Chromium with synthetic session/product fixtures: Home, account settings and product detail at 1440, 390 and 320px. Matching account/creator portraits, 31px header geometry, no document overflow, no uncaught page errors and no external avatar requests.
- DESIGN.md lint: 0 errors, 7 existing unused-token warnings.
- Strict full-project UI audit: 16 findings before and after, no new rule/file/message findings. Existing unrelated form and markup findings remain outside this focused change.
- `git diff --check` passes. This static frontend has no configured build or lint command.

Browser fixtures do not verify live sign-in, production API connectivity, payments or downloads. No deployment performed.
