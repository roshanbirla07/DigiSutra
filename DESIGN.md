---
version: alpha
name: DigiSutra Calm Toolkit
description: A considered marketplace for useful digital work, with tactile folio covers and a quiet creator workspace.
colors:
  ink: "#203e34"
  inkStrong: "#15392d"
  inkSoft: "#536c60"
  paper: "#f8faf6"
  surface: "#ffffff"
  line: "#dce7dc"
  primary: "#185e43"
  accent: "#dba842"
  danger: "#a33129"
typography:
  display:
    fontFamily: "DM Sans, Inter, sans-serif"
  body:
    fontFamily: "Inter, system-ui, sans-serif"
rounded:
  DEFAULT: "16px"
  control: "10px"
  folio: "8px"
spacing:
  contentMax: "1280px"
  section: "48px"
components:
  button: {}
  productCard: {}
  field: {}
  navigation: {}
---

# DigiSutra Calm Toolkit

## Overview

### Creative North Star

A maker's folio: the product cover feels like a useful little publication you can pick up, while purchasing and account work stay calm and predictable. The stacked folios in the home hero carry the expressive moment. They are original CSS artwork, never a substitute for a seller's actual preview image.

DigiSutra serves customers browsing and buying digital guides, templates and prompts, and creators publishing and tracking them. The public home page may be more expressive; catalog, checkout, library, seller and admin screens emphasize task clarity. The current interface is in English, with INR values and `en-IN` dates. No dark theme or localization provider is maintained yet.

**Anti-references:** generic Bootstrap cards, glass panels, neon dashboards and decorative analytics. The previous `Design.md` prescribed neutral blue and shadcn/Tailwind, but the shipped app uses a green CSS system and native JavaScript; this document reconciles that drift with the accepted Calm Toolkit UI.

**Token ownership:** `apps/web/calm-toolkit.css` is the runtime owner for the values above and overrides the legacy base in `apps/web/styles.css`. This document mirrors those tokens. When changing a token, edit the CSS variable and this document in the same PR. Components use CSS variables for shared colors, type and radii. Legacy `styles.css` should not gain new design decisions.

## Colors

Paper `#f8faf6` and white surfaces create calm separation; ink `#203e34` and strong ink `#15392d` carry content. Primary green `#185e43` belongs to interactive commitments and selected navigation. Gold `#dba842` is a small folio/focus accent, not a second primary button color. The darker danger color is reserved for destructive actions. Product covers can use editorial colors distinct from the UI chrome.

## Typography

DM Sans is the display face for short headings and the wordmark; Inter is the reading and control face. Keep hierarchy through size and line height, with restrained bold weights. Financial figures use tabular numerals. Product titles and creator names remain visible without hover.

## Layout

The content width is 1280px. The catalog grid responds from four columns to two, then one on narrow phones. Seller navigation becomes a horizontal scrollable strip at tablet width; the site header uses a native disclosure menu. Avoid viewport-bound heights on forms. Image and loading placeholders reserve the same proportions as product covers.

## Elevation & Depth

Separate surfaces with line `#dce7dc`; use subtle elevation for overlays and a soft hover lift on product covers. The hero's stacked folios are the only deliberately layered composition. No frosted glass panels across routine application pages.

## Shapes

Cards use a 16px radius, controls around 10px, and the overlapping folio artwork has sharper 8px corners. Focus has a visible gold ring. Icons with operational meaning retain text labels.

## Components

- Shared button classes define primary, secondary, ghost and danger; actions have hover, focus, active and disabled states. Primary actions use solid green.
- The shared header owns desktop and mobile navigation. Current routes expose `aria-current`; the seller sidebar uses the same state cue.
- Product cards show the verified listing preview when available, otherwise an editorial cover. A preview is public; paid files stay protected by backend authorization.
- Search keeps committed query/category in the URL, offers Clear search, and can reset to all products. Loading reserves card geometry; empty, no-results and request errors offer relevant next actions.
- Forms keep labels and inline errors. The browser owns native select popup geometry. Marketplace type and spacing adapt at small widths without hiding descriptions.
- Animation is limited to 180–220ms feedback and cover hover. Reduced-motion preference removes motion and smooth scrolling.

## Do's and Don'ts

- Do retain the real creator's preview and the marketplace's calm green identity.
- Do use the shared header, card, button, field and status patterns across customer and seller views.
- Don't introduce a second accent palette or a decorative chart to fill space.
- Don't put a payment, refund, role or access decision in the browser; `FRONTEND_REFERENCE.md` is the business trust boundary.
