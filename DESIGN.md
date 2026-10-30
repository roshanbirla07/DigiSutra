---
version: alpha
name: DigiSutra Indigo + Cloud
description: A resource-first marketplace with indigo actions, cloud surfaces and a focused creator workspace.
colors:
  ink: "#25243b"
  inkStrong: "#19182b"
  inkSoft: "#646278"
  paper: "#f7f8fc"
  surface: "#ffffff"
  line: "#e2e3ee"
  primary: "#5842e8"
  accent: "#5842e8"
  danger: "#a33129"
typography:
  display:
    fontFamily: "DM Sans, Inter, sans-serif"
  body:
    fontFamily: "Inter, system-ui, sans-serif"
rounded:
  DEFAULT: "16px"
  control: "10px"
spacing:
  contentMax: "1280px"
  section: "48px"
components:
  button: {}
  productCard: {}
  field: {}
  navigation: {}
---

# DigiSutra Indigo + Cloud

## Overview

### Creative North Star

A head start for a creator's next project: the home page puts search beside a real listing, then leads into categories and product cards. The signature is a resource spotlight that uses the creator’s public preview or the shared illustrated cover. An empty/loading spotlight uses clearly illustrative typography without inventing a listing. Product detail separates the preview and description from a quiet purchase panel.

DigiSutra serves customers browsing and buying digital guides, templates and prompts, and creators publishing and tracking them. The public home page may be more expressive; catalog, checkout, library, seller and admin screens emphasize task clarity. The current interface is in English, with INR values and `en-IN` dates. No dark theme or localization provider is maintained yet.

**Anti-references:** generic Bootstrap cards, glass panels, neon dashboards and decorative analytics. The approved Indigo + Cloud direction replaces Calm Toolkit green across the existing native JavaScript app; it does not introduce a second UI framework.

**Token ownership:** `apps/web/indigo-cloud.css` is the runtime owner for the values above and overrides the legacy base in `apps/web/styles.css`. This document mirrors those tokens. When changing a token, edit the CSS variable and this document in the same PR. Components use CSS variables for shared colors, type and radii. Legacy `styles.css` should not gain new design decisions.

## Colors

Cloud `#f7f8fc` and white surfaces create separation; ink `#25243b` and strong ink `#19182b` carry content. Indigo `#5842e8` belongs to commitments, links, selected navigation and focus. The accent token aliases this same indigo, keeping one action color. Soft violet surfaces support hierarchy without competing with product previews. The darker danger color is reserved for destructive actions. Product covers can use editorial colors distinct from the UI chrome.

## Typography

DM Sans is the display face for short headings and the wordmark; Inter is the reading and control face. Keep hierarchy through size and line height, with restrained bold weights. Financial figures use tabular numerals. Product titles and creator names remain visible without hover.

## Layout

The content width is 1280px. The desktop home hero pairs search with a real product spotlight. The product page uses a main content column and a 370px purchase panel, sticky on desktop and in natural flow below the preview on mobile. The catalog grid responds from four columns to two, then one on narrow phones. Seller navigation becomes a horizontal scrollable strip at tablet width; the site header uses a native disclosure menu. Avoid viewport-bound heights on forms. Image and loading placeholders reserve the same proportions as product covers.

## Elevation & Depth

Separate surfaces with line `#e2e3ee`; use subtle elevation for overlays and a soft hover lift on product covers. Reserve soft elevation for the spotlight, purchase panel and overlays. No frosted glass panels across routine application pages.

## Shapes

Cards use a 16px radius, controls at 10px (`--radius-control`), and preview frames use 10px inner corners. Focus has a visible indigo ring. Icons with operational meaning retain text labels.

## Components

| Document token | Runtime owner in `indigo-cloud.css` | Consumers |
|---|---|---|
| `colors.primary`, `colors.accent` | `--primary`, `--accent` | buttons, links, selection, focus |
| `colors.paper`, `colors.surface`, `colors.line` | `--paper`, `--surface`, `--line` | page, shared cards, panels, fields |
| `colors.ink`, `colors.inkStrong`, `colors.inkSoft` | `--ink`, `--ink-strong`, `--ink-soft` | content, headings, secondary text |
| `colors.danger` | `--danger` | destructive buttons and errors |
| `typography.display` | `--font-display` | headings and wordmark |
| `typography.body` | base `:root` in `styles.css` | body and controls |
| `rounded.DEFAULT`, `rounded.control` | `--radius`, `--radius-control` | panels, controls |


- Shared button classes define primary, secondary, ghost and danger; actions have hover, focus, active and disabled states. Primary actions use solid indigo. `--radius-control` owns button corners; `--danger` owns destructive/error color.
- Default account and creator avatars use original locally rendered vector portraits from `apps/web/src/views/avatar.js`. A deterministic username seed gives random-looking variety while keeping the same user consistent across header, account settings, product cards and product detail. Artwork colors are independent of brand tokens; there are no stock profile photos or external avatar requests. Existing accounts need no migration. The current API has no profile-photo upload field; this change does not add an upload flow.
- The shared header owns desktop and mobile navigation. Current routes expose `aria-current`; the seller sidebar uses the same state cue.
- Product cards show the verified listing preview when available, otherwise an editorial cover. A preview is public; paid files stay protected by backend authorization.
- Search keeps committed query/category in the URL, offers Clear search, and can reset to all products. Loading reserves card geometry; empty, no-results and request errors offer relevant next actions.
- Forms keep labels and inline errors. The browser owns native select popup geometry. Marketplace type and spacing adapt at small widths without hiding descriptions.
- Animation is limited to 180–220ms feedback and cover hover. Reduced-motion preference removes motion and smooth scrolling.

## Do's and Don'ts

- Do retain the real creator's preview and the marketplace's Indigo + Cloud identity.
- Do use the shared header, card, button, field and status patterns across customer and seller views.
- Don't introduce a second accent palette or a decorative chart to fill space.
- Don't put a payment, refund, role or access decision in the browser; `FRONTEND_REFERENCE.md` is the business trust boundary.
