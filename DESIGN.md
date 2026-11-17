---
version: alpha
name: DigiSutra Marketplace
description: A cream marketplace with black navigation, pink actions, and illustrated page heroes.
colors:
  ink: "#151412"
  inkStrong: "#111110"
  inkSoft: "#514b46"
  paper: "#faf6ef"
  surface: "#ffffff"
  line: "#d6cbc2"
  primary: "#7a175d"
  accent: "#ff90e8"
  action: "#ff63dd"
  mint: "#c6f8d1"
  yellow: "#fff098"
  lavender: "#dfbef8"
  danger: "#a33129"
typography:
  display:
    fontFamily: "DM Sans, Inter, sans-serif"
  body:
    fontFamily: "Inter, system-ui, sans-serif"
rounded:
  DEFAULT: "4px"
  control: "2px"
spacing:
  contentMax: "1536px"
components:
  button: {}
  productCard: {}
  field: {}
  navigation: {}
---

# DigiSutra Marketplace

## Overview

DigiSutra helps buyers find practical digital products and gives independent creators a place to list and sell them. Large, illustrated page headings and heavy outlines define the public pages. The product grid shows the real listing art and the most useful information for comparing products. Keep titles, prices, and creator names visible without hovering.

The interface uses English and INR, with `en-IN` dates and WCAG 2.2 AA as its accessibility target. `FRONTEND_REFERENCE.md` describes the business trust boundary. Server responses own prices, orders, access, permissions, and seller payout calculations.

## Colors

Warm cream is the default canvas. Black lines and white panels separate headings, cards, and controls. Use pink for primary actions and price chips, and dark plum for links and focus on light surfaces. Yellow, mint, and lavender distinguish public page headers and decorative illustrations. Status and error colors retain their own meanings in the workspace.

`apps/web/theme.css` owns runtime design tokens. `apps/web/styles.css` holds the legacy structural base. Keep the token table and runtime values in sync.

| Design role | Runtime token | Consumers |
|---|---|---|
| Ink, paper, surface, neutral lines | `--ink`, `--ink-strong`, `--ink-soft`, `--paper`, `--surface`, `--line` | Page, cards, panels, fields |
| Links and focus | `--primary` | Text links and controls on light backgrounds |
| Pink accent and action | `--pink`, `--hot-pink` | Price tags, Discover hero, primary buttons |
| Illustration tones | `--yellow`, `--mint`, `--lavender` | Public hero and cover art |
| Errors | `--danger` | Destructive actions and validation |
| Corners | `--radius`, `--radius-control` | Shared panels and controls |

## Typography

Use DM Sans for headings and the wordmark, and Inter for copy and controls. Hero headings are bold and compact. Use tabular numerals for prices and financial figures.

## Layout

Discover, Blog, Features, Pricing and About share a black navbar. The active public destination uses a white pill. On smaller screens, the native disclosure reveals the links and keeps the sign-in/account and seller action accessible. Product search sits with discovery controls. The catalog retains its URL-backed filters.

The storefront is at most 1536px wide. The grid reflows for phones and uses real listing previews when available. Product detail keeps the preview and description separate from the purchase panel. On smaller screens the panel follows the content in document order. Seller navigation becomes a horizontal scrollable row at tablet width.

## Elevation & Depth

The public hero uses a hard offset shadow. Lightweight workspace panels, menus, and dialogs use neutral outlines with limited elevation. Motion respects reduced-motion preferences.

## Shapes

Use square product cards and outlined page sections. Reserve full pills for the active navbar destination. Keep visible keyboard focus and labelled native controls.

## Components

- The shared header marks the active route with `aria-current` and retains wording and destinations for signed-in routes.
- Product cards reserve cover proportions. They use the creator's verified public preview when it exists and an editorial fallback otherwise. Paid files remain protected.
- Blog cards have complete article destinations. Topic filters are URL-backed. The Pricing FAQ uses native disclosures.
- Forms preserve inline errors and validation. The browser owns native selects and dialog focus.
- Default avatars are local illustrations seeded by username. No external avatar requests are needed.

## Do's and Don'ts

- Use the real catalog and preserve actual creator previews. Use original decorative art only for page and article illustrations.
- Keep public page content usable without authentication. Seller actions lead to the existing application or workspace.
- Keep unannounced fee rates out of public copy. The browser presents pricing and payout information supplied by the server.
