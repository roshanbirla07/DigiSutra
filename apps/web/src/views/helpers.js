import { APP } from "../constants/app.js";

export const escapeHtml = (value) => String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");
export const initials = (value) => (String(value || "U").trim().split(/\s+/).map((part) => part[0]).join("").slice(0, 2) || "U").toUpperCase();
export const money = (currency, value) => `${currency || APP.defaultCurrency} ${value ?? "0.00"}`;
export const date = (value) => value ? new Intl.DateTimeFormat("en-IN", { dateStyle: "medium" }).format(new Date(value)) : "—";
export const statusLabel = (value) => String(value || "pending").replaceAll("_", " ");

export function productCover(product, compact = false) {
  const alt = escapeHtml(product.image_alt || product.title || "Product cover");
  return product.image_uri
    ? `<img class="product-cover-image ${compact ? "compact" : ""}" src="${escapeHtml(product.image_uri)}" alt="${alt}" />`
    : `<div class="product-cover ${compact ? "compact" : ""}"><small>${escapeHtml(product.category || "Digital work")}</small><span>${escapeHtml(product.title || "A good find")}</span><i aria-hidden="true">✳</i></div>`;
}

export function renderProductCard(product) {
  return `<article class="product-card">
    <a class="product-card-link" href="/products/${encodeURIComponent(product.uuid)}" data-link>
      <div class="product-card-media">${productCover(product)}<span class="preview-tag">See product ↗</span></div>
      <div class="product-card-body"><span class="eyebrow">${escapeHtml(product.category || "Digital product")}</span><h3>${escapeHtml(product.title)}</h3><p>${escapeHtml(product.description || "A useful digital resource from an independent creator.")}</p><div class="product-card-footer"><span>By ${escapeHtml(product.owner_username || "Independent creator")}</span><strong>${escapeHtml(money(product.currency, product.price))}</strong></div></div>
    </a>
  </article>`;
}

export function emptyState(title, body, action = "") { return `<div class="empty-state"><div class="empty-mark">DS</div><h3>${escapeHtml(title)}</h3><p>${escapeHtml(body)}</p>${action}</div>`; }
