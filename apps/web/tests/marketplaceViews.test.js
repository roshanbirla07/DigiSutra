import assert from "node:assert/strict";
import test from "node:test";

import {
  adminSellerApplications,
  auth,
  catalog,
  catalogLoading,
  checkout,
  detail,
  home,
  library,
  seller,
  sellerApplication,
  sellerPayouts,
  sellerProductNew,
  sellerProducts,
  settings,
} from "../src/views/marketplace.js";

const customer = { username: "maya", first_name: "Maya", last_name: "Rao", email: "maya@example.com", user_type: "customer" };
const creator = { ...customer, user_type: "seller" };
const admin = { ...customer, user_type: "admin" };
const product = {
  uuid: "product::1",
  title: "Product Strategy Toolkit",
  description: "A practical toolkit for clearer product decisions.",
  category: "Templates",
  currency: "INR",
  price: "499.00",
  owner_username: "creator",
  is_active: true,
  is_public: true,
};

test("customer pages render their primary interaction hooks", () => {
  const homepage = home({ session: customer, products: [product] });
  assert.match(homepage, /Find your next <em>useful thing/);
  assert.match(homepage, /data-home-search/);
  assert.match(homepage, /class="mobile-nav"/);
  assert.doesNotMatch(homepage, />Categories<\/a>/);
  assert.match(homepage, /data-category="Templates"/);
  const catalogue = catalog({ session: customer, products: [product] });
  assert.match(catalogue, /data-catalog-form/);
  assert.match(catalogue, /product-card-media/);
  assert.match(detail({ session: customer, product }), /data-buy-product="product::1"/);
  assert.match(auth({ mode: "signup" }), /data-auth-form data-mode="signup"/);
  assert.match(settings({ session: customer }), /data-logout/);
  assert.match(checkout({ session: customer, product }), /data-start-checkout="product::1"/);
  assert.match(checkout({ session: customer, product, checkout: { order: { uuid: "order::1" } } }), /data-open-razorpay/);
});

test("catalogue retains all category choices while showing filtered products", () => {
  const other = { ...product, uuid: "product::2", title: "Writing guide", category: "Guides" };
  const html = catalog({ session: customer, products: [product], availableProducts: [product, other], category: "Templates" });
  assert.match(html, /<option value="Guides"/);
  assert.match(html, /<option value="Templates" selected>/);
  assert.doesNotMatch(html, /Writing guide/);
});

test("catalogue provides clear, reset, retry and stable loading states", () => {
  const filtered = catalog({ session: customer, products: [], query: "unknown", category: "Templates" });
  assert.match(filtered, /data-clear-search aria-label="Clear search"/);
  assert.match(filtered, /data-reset-catalog/);
  assert.match(filtered, /No matches yet/);
  const failed = catalog({ session: customer, products: [], error: "upstream failed" });
  assert.match(failed, /data-retry-products/);
  assert.doesNotMatch(failed, /upstream failed/);
  assert.match(catalogLoading({ session: customer }), /aria-busy="true"/);
  assert.match(home({ session: customer, products: [], loading: true }), /Loading featured products/);
});

test("library only enables verified paid downloads", () => {
  const ready = library({
    session: customer,
    purchases: [{
      order: { uuid: "order::1", product_title: product.title, payment_status: "paid", delivery_status: "ready" },
      assets: [{ uuid: "asset::1", asset_status: "verified" }],
      access_records: [{ access_status: "granted" }],
    }],
  });
  const pending = library({ session: customer, purchases: [{ order: { product_title: product.title, payment_status: "pending" } }] });

  assert.match(ready, /data-library-order="order::1" data-library-asset="asset::1"/);
  assert.doesNotMatch(pending, /data-library-order=/);
  assert.match(pending, /disabled>Not ready/);
});

test("seller workspace pages preserve operational forms and navigation", () => {
  const summary = { currency: "INR", gross_sales_amount: "1000", net_seller_amount: "900", available_for_payout: "500", pending_payout: "100", products_count: 1, payout_ready: true, payouts: [] };

  assert.match(seller({ session: creator, summary, products: [product] }), /class="active" aria-current="page" href="\/seller"/);
  assert.match(sellerProducts({ session: creator, products: [product] }), /Product Strategy Toolkit/);
  assert.match(sellerProductNew({ session: creator }), /data-product-form/);
  assert.match(sellerProductNew({ session: creator }), /name="asset_file"/);
  assert.match(sellerProductNew({ session: creator }), /name="preview_image"/);
  assert.match(sellerProductNew({ session: creator }), /Visible in the catalogue before payment/);
  assert.match(sellerPayouts({ session: creator, summary }), /Payout history/);
});

test("seller onboarding and admin review preserve workflow hooks", () => {
  const application = { uuid: "application::1", status: "submitted", kyc_status: "not_started", store_name: "Maya Studio", applicant: { email: customer.email } };
  const form = sellerApplication({ session: customer, application: { status: "draft" } });
  const review = adminSellerApplications({ session: admin, applications: [application] });

  assert.match(form, /data-seller-application-form/);
  assert.match(form, /data-seller-application-action="submit"/);
  assert.match(review, /data-refresh-admin-sellers/);
  assert.match(review, /data-admin-seller-action="start-kyc-review"/);
});


test("seller draft bypasses submit-only required field validation", () => {
  const html = sellerApplication({ session: customer, application: {} });
  assert.match(html, /type="submit" formnovalidate data-seller-application-action="draft"/);
  assert.match(html, /type="submit" data-seller-application-action="submit"/);
});

test("authentication mode cannot inject markup", () => {
  const html = auth({ mode: 'login"><img src=x onerror=alert(1)>' });
  assert.match(html, /data-auth-form data-mode="login"/);
  assert.doesNotMatch(html, /<img/);
  assert.doesNotMatch(html, /onerror/);
});
