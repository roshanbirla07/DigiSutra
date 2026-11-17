import { ROUTES } from "../constants/app.js";
import { escapeHtml } from "./helpers.js";

const posts = [
  {
    slug: "create-your-first-digital-product", category: "selling", art: "create", tone: "mint",
    title: "Create your first digital product",
    summary: "Turn a process you already use into a file someone else can put to work.",
    sections: [
      ["Choose one outcome", "Pick a specific job your buyer wants to finish. A budget spreadsheet that helps freelancers set aside tax each month is easier to explain and test than a collection of unrelated spreadsheets."],
      ["Package the files", "Include the editable file, a short setup guide, and an example with sample data. Open every file on a clean device or account to check for missing fonts, permissions, and broken links."],
      ["Build a useful preview", "Show the finished result and one or two steps from the workflow. Tell buyers what files are included, which tools they need, and whether they can use the work commercially."],
    ],
  },
  {
    slug: "price-your-first-template", category: "selling", art: "price", tone: "pink",
    title: "Price your first template",
    summary: "Set a price based on what the template helps a buyer do.",
    sections: [
      ["Compare similar products", "Compare templates that solve the same problem and use the same tools. Check whether they include examples, documentation, or support before comparing their prices."],
      ["Set a starting price", "Consider how much time the template saves and how much work it takes to keep it current. Make the included files and licence clear so buyers can judge the offer."],
      ["Review buyer feedback", "Look for questions about what the template includes or how to use it. Improve the preview and instructions where buyers get stuck, then use sales and feedback to revisit your price."],
    ],
  },
  {
    slug: "write-a-product-page-buyers-can-trust", category: "product-guides", art: "listing", tone: "lavender",
    title: "Write a product page buyers can trust",
    summary: "Help buyers see what they’ll receive before they pay.",
    sections: [
      ["Start with the buyer's task", "Say what the product helps someone do and who it is designed for. Name any tools, accounts, or experience buyers will need to use it."],
      ["Show what’s included", "List the files, formats, and versions. Use a preview of the actual product. For a spreadsheet, show the inputs and outputs with sample data."],
      ["Explain usage and access", "Tell buyers what the licence permits, how they can access their purchase, and where they can get help. Use product-specific details that buyers can check against the files they receive."],
    ],
  },
];

const art = (name) => `<img src="/art/${name}.webp" alt="" decoding="async" />`;

export function publicHero({ title, summary, tone, illustration }) {
  return `<section class="public-hero tone-${tone}">
    <div><h1>${escapeHtml(title)}</h1>${summary ? `<p>${escapeHtml(summary)}</p>` : ""}</div>
    ${illustration ? art(illustration) : ""}
  </section>`;
}

function editorialCard({ title, summary, art: illustration, tone, action = "" }) {
  return `<article class="editorial-card">
    <div class="editorial-art tone-${tone}">${art(illustration)}</div>
    <div class="editorial-copy"><h2>${escapeHtml(title)}</h2><p>${escapeHtml(summary)}</p>${action}</div>
  </article>`;
}

function blog(filter) {
  const filters = [["all", "All posts"], ["selling", "Selling"], ["product-guides", "Product guides"]];
  const active = filters.some(([key]) => key === filter) ? filter : "all";
  return `${publicHero({ title: "The DigiSutra blog", summary: "Practical guides for buying and selling digital products.", tone: "yellow", illustration: "blog" })}
    <nav class="filter-chips editorial-filters" aria-label="Filter articles">
      ${filters.map(([key, label]) => `<a href="${ROUTES.blog}${key === "all" ? "" : `?topic=${key}`}" data-link ${active === key ? 'aria-current="true"' : ""}>${label}</a>`).join("")}
    </nav>
    <div class="editorial-grid">
      ${posts.filter((post) => active === "all" || post.category === active).map((post) => editorialCard({
        ...post,
        action: `<a class="button button-primary" href="${ROUTES.blogArticle(post.slug)}" data-link aria-label="Read ${escapeHtml(post.title)}">Read article</a>`,
      })).join("")}
    </div>`;
}

function features(sellUrl) {
  const cards = [
    { title: "List your products", summary: "Upload files, add a preview, and set a price.", art: "upload", tone: "lavender" },
    { title: "Deliver files after payment", summary: "Buyers can download purchases from their library after payment is confirmed.", art: "download", tone: "yellow" },
    { title: "Track sales and payouts", summary: "See orders, seller earnings, and payout status in your seller workspace.", art: "payout", tone: "pink" },
  ];
  return `${publicHero({ title: "From upload to download", summary: "List digital products, accept payments, and deliver files in one place.", tone: "mint", illustration: "features" })}
    <div class="editorial-grid">${cards.map(editorialCard).join("")}</div>
    <a class="button button-primary" href="${sellUrl}" data-link>Start selling</a>`;
}

function pricing() {
  return `${publicHero({ title: "Seller pricing", summary: "See how fees and payouts apply to a digital product sale.", tone: "pink", illustration: "pricing" })}
    <div class="editorial-split pricing-panels">
      <section class="editorial-panel"><h2>What affects your payout</h2>
        <dl class="payout-factors">
          <div><dt>Product price</dt><dd>The price set on your listing.</dd></div>
          <div><dt>Platform fee</dt><dd>The fee DigiSutra deducts from the sale.</dd></div>
          <div><dt>Payout availability</dt><dd>The amount currently available to withdraw in your seller workspace.</dd></div>
        </dl>
      </section>
      <section class="editorial-panel tone-yellow"><h2>Seller fees</h2><p>Rates to be announced.</p>${art("seller-fees")}</section>
    </div>
    <section class="pricing-faq" aria-label="Pricing questions">
      <details><summary>How are seller payouts calculated?</summary><p>Seller earnings reflect the sale price after the platform fee and any applicable taxes. Your Payouts page shows what is available, pending, or paid.</p></details>
      <details><summary>When will pricing be available?</summary><p>Seller fee rates are yet to be announced.</p></details>
    </section>`;
}

function about() {
  return `${publicHero({ title: "Meet DigiSutra", summary: "A marketplace for digital products made by independent creators.", tone: "lavender", illustration: "about" })}
    <div class="editorial-split">
      <section class="editorial-panel editorial-panel-illustrated tone-yellow"><div><h2>For creators</h2><p>Sell the templates, guides, and tools you make.</p></div>${art("creators")}</section>
      <section class="editorial-panel editorial-panel-illustrated tone-mint"><div><h2>For buyers</h2><p>Find practical digital products for work, learning, and creative projects.</p></div>${art("buyers")}</section>
    </div>
    <div class="section-heading editorial-cta"><h2>Built for digital downloads</h2><a class="button button-secondary" href="${ROUTES.catalog}" data-link>Explore the marketplace</a></div>`;
}

export function getBlogPost(slug) {
  return posts.find((post) => post.slug === slug);
}

export function publicPageContent({ path, filter, post, sellUrl }) {
  if (path === ROUTES.blog) return blog(filter);
  if (path === ROUTES.features) return features(sellUrl);
  if (path === ROUTES.pricing) return pricing();
  if (path === ROUTES.about) return about();
  return `<a class="back-link" href="${ROUTES.blog}" data-link>← Back to the blog</a>
    ${publicHero({ ...post, illustration: post.art })}
    <article class="blog-article">
      ${post.sections.map(([title, body]) => `<section><h2>${escapeHtml(title)}</h2><p>${escapeHtml(body)}</p></section>`).join("")}
    </article>`;
}
