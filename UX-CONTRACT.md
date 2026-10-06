# DigiSutra UI behavior

## Product context

Customers discover and purchase digital goods and access paid files in their library. Sellers publish products and review sales and payouts. Administrators review seller applications. The maintained business trust boundary is `FRONTEND_REFERENCE.md`; backend APIs own prices, orders, delivery rights and permissions. The interface currently uses English and INR, with `en-IN` dates and WCAG 2.2 AA as its accessibility target.

## Canonical UI map

| Capability | Owner | Decision | Verification |
|---|---|---|---|
| Navigation | `apps/web/src/views/marketplace.js` `header` and `workspaceSidebar` | Links keep native semantics; current route uses `aria-current`; phone header has disclosure menu | view tests and responsive browser pass |
| Product cover | `apps/web/src/views/helpers.js` `productCover` | Verified preview if present, editorial fallback otherwise | view tests |
| Catalog search | `apps/web/src/app.js` and `marketplace.js` `catalog` | Local filter of fetched products; committed query/category in URL; clear/reset and retry actions | view tests and browser pass |
| Select | native `<select>` | Browser-owned popup is acceptable for category and business type | keyboard browser pass |
| Scrollbar | `apps/web/calm-toolkit.css` | Global visible thin scrollbar, high-contrast system colors | CSS audit |
| Toast | `apps/web/src/app.js` `toast` | One polite live region in `index.html`; inline errors remain at the correction point | browser pass |
| Forms | `marketplace.js` labels, `app.js` submit handlers | Server remains authoritative; errors stay inline; no value loss on failure | existing frontend tests |

## Flow ledger

| Flow | Pending | Success | Failure |
|---|---|---|---|
| Discover products | Cover-proportioned loading cards | Catalog/home displays listing | Inline catalog retry; retain filters |
| Search/filter | Local after initial fetch | URL records committed query and category | No-results state offers reset |
| Buy product | Payment button state | Backend order and Razorpay checkout | Inline checkout error; payment truth from backend |
| Download purchase | Button disabled during authorization | Backend-authorized delivery | Re-enable button and notify user |
| Publish product | File and preview upload | Return to seller products | Keep form and inline error |

## Responsive and visual contract

`DESIGN.md` mirrors runtime tokens in `apps/web/calm-toolkit.css`. The public grid becomes two columns on phones and one on very narrow phones. The seller sidebar becomes a scrollable navigation row without clipping forms. Product images and loading placeholders reserve aspect ratio. Keyboard focus and reduced motion apply across all routes. Native controls retain their platform popup behavior.

## Migration status

The shared shell and discovery flow use the contract above. Existing admin-review browser prompts and several legacy form submission behaviors predate it and require a separate workflow PR because they alter verification and payment-adjacent state. Do not claim those flows are migrated based on the visual shell alone.
