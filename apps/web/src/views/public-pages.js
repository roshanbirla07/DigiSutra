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

function marketingHero({ label, title, summary, tone = "", illustrations = [], actions = "" }) {
  return `<section class="marketing-hero ${tone}">
    ${illustrations.map(art).join("")}
    <div class="marketing-inner">
      ${label ? `<p class="marketing-label">${escapeHtml(label)}</p>` : ""}
      <h1>${escapeHtml(title)}</h1>
      <p>${escapeHtml(summary)}</p>
      ${actions}
    </div>
  </section>`;
}

function sellAction(url) {
  return `<a class="button button-primary" href="${url}" data-link>Start selling</a>`;
}

function blog(filter) {
  const showAll = !posts.some((post) => post.category === filter);
  const [featured, ...more] = showAll ? posts : posts.filter((post) => post.category === filter);
  return `<div class="marketing-inner blog-index">
    <header class="blog-heading"><h1>The DigiSutra blog</h1><p>Practical guides for independent creators.</p></header>
    ${showAll ? "" : `<a class="back-link" href="${ROUTES.blog}" data-link>← All guides</a>`}
    <div class="blog-index-layout">
      <article class="blog-featured">
        <div class="blog-featured-art tone-${featured.tone}">${art(featured === posts[0] ? "blog-featured" : featured.art)}</div>
        ${showAll ? `<p class="marketing-label">Featured guide</p>` : ""}
        <h2>${escapeHtml(featured.title)}</h2>
        <p>${escapeHtml(featured.summary)}</p>
        <a class="button marketing-dark-button" href="${ROUTES.blogArticle(featured.slug)}" data-link aria-label="Read ${escapeHtml(featured.title)}">Read the guide</a>
      </article>
      ${more.length ? `<aside class="blog-more" aria-labelledby="moreGuides">
        <h2 id="moreGuides">More guides</h2>
        <ul>${more.map((post) => `<li><a href="${ROUTES.blogArticle(post.slug)}" data-link>${escapeHtml(post.title)} <span aria-hidden="true">→</span></a></li>`).join("")}</ul>
      </aside>` : ""}
    </div>
  </div>`;
}

function features(sellUrl) {
  const steps = [
    ["Create a listing", "workflow-list"],
    ["Upload files", "workflow-upload"],
    ["Publish", "workflow-publish"],
    ["Track earnings", "workflow-earn"],
  ];
  return `${marketingHero({ label: "Features", title: "Sell what you make.", summary: "List digital products, accept payments, and deliver files in one place." })}
    <section class="workflow-band" aria-label="How selling works">
      <ol class="marketing-inner workflow-loop">
        ${steps.map(([label, image]) => `<li>${art(image)}<span>${label}</span></li>`).join("")}
      </ol>
    </section>
    <section class="marketing-band tone-mint"><div class="marketing-inner"><h2>From checkout to download</h2><p>Buyers pay through Razorpay and find confirmed purchases in their library.</p></div></section>
    <section class="marketing-band tone-lavender"><div class="marketing-inner"><h2>See how your products sell</h2><p>Track orders, earnings, and payouts in Seller Studio.</p></div></section>
    <div class="marketing-band marketing-centered">${sellAction(sellUrl)}</div>`;
}

function pricing(sellUrl) {
  return `${marketingHero({
    label: "Pricing",
    title: "Seller pricing, made clear.",
    summary: "See how each sale turns into seller earnings.",
    tone: "marketing-yellow",
    illustrations: ["pricing-coin", "pricing-coin"],
  })}
    <div class="marketing-split pricing-panels">
      <section class="marketing-band marketing-periwinkle"><h2>10%</h2><p>Platform fee per sale</p><small>Illustrative rate</small></section>
      <section class="marketing-band marketing-teal"><h2>₹90</h2><p>Seller earnings on a ₹100 sale</p><small>Before any applicable taxes.</small></section>
    </div>
    <section class="marketing-band pricing-faq"><div class="marketing-inner">
      <h2>Frequently asked questions</h2>
      <details><summary>How is my payout calculated?</summary><p>Your seller earnings are the sale price minus the platform fee and any applicable taxes.</p></details>
      <details><summary>Where can I see my earnings?</summary><p>Open Seller Studio and select Payouts to see what’s available for payout, pending, or already paid.</p></details>
      <details><summary>How does the platform fee work?</summary><p>DigiSutra deducts a percentage from each sale. The 10% above is an example of how earnings are calculated. The final fee rate is yet to be announced.</p></details>
    </div></section>
    <section class="marketing-band marketing-centered tone-pink"><h2>Ready to sell?</h2><div class="marketing-actions"><a class="button button-secondary" href="${sellUrl}" data-link>Start selling</a></div></section>`;
}

function about(sellUrl) {
  const actions = `<div class="marketing-actions">${sellAction(sellUrl)}
    <a class="button button-secondary" href="${ROUTES.catalog}" data-link>Explore marketplace</a>
  </div>`;
  return `${marketingHero({
    title: "Give your work a place to sell.",
    summary: "DigiSutra is a marketplace for digital products made by independent creators.",
    tone: "marketing-soft-pink",
    illustrations: ["about-file", "about-coin"],
    actions,
  })}
    <div class="marketing-split about-audiences">
      <section class="marketing-band tone-yellow"><h2>For creators</h2><p>Sell the templates, guides, and tools you make.</p>${art("about-creator")}</section>
      <section class="marketing-band tone-mint"><h2>For buyers</h2><p>Find practical downloads for work, learning, and creative projects.</p>${art("about-buyer")}</section>
    </div>
    <section class="marketing-band marketing-centered"><div class="marketing-inner">
      <h2>Start with something useful.</h2>
      <p>A template you use every week could become your first listing.</p>
      <a class="marketing-text-link" href="${ROUTES.features}" data-link>See how selling works</a>
    </div></section>`;
}

export function getBlogPost(slug) {
  return posts.find((post) => post.slug === slug);
}

export function publicPageContent({ path, filter, post, sellUrl }) {
  if (path === ROUTES.blog) return blog(filter);
  if (path === ROUTES.features) return features(sellUrl);
  if (path === ROUTES.pricing) return pricing(sellUrl);
  if (path === ROUTES.about) return about(sellUrl);
  return `<a class="back-link" href="${ROUTES.blog}" data-link>← Back to the blog</a>
    ${publicHero({ ...post, illustration: post.art })}
    <article class="blog-article">
      ${post.sections.map(([title, body]) => `<section><h2>${escapeHtml(title)}</h2><p>${escapeHtml(body)}</p></section>`).join("")}
    </article>`;
}
