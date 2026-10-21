import assert from "node:assert/strict";
import test from "node:test";
import { JSDOM } from "jsdom";
import { createApp } from "../src/app.js";
import { safeReturnPath } from "../src/services/ui.js";

const customer = { token: "customer-token", username: "buyer", user_type: "customer" };
const admin = { ...customer, token: "admin-token", user_type: "admin" };
const product = { uuid: "product::1", title: "Guide", price: "99.00", currency: "INR" };
const tick = () => new Promise((resolve) => setImmediate(resolve));
async function until(predicate) {
  for (let i = 0; i < 100; i++) { if (predicate()) return; await tick(); }
  assert.ok(predicate(), "Expected UI state was not reached");
}
function setup(path, session, respond = () => []) {
  const dom = new JSDOM('<div id="toastHost"></div><div id="app"></div>', { url: `http://localhost:3000${path}` });
  Object.assign(globalThis, { window: dom.window, document: dom.window.document, localStorage: dom.window.localStorage, FormData: dom.window.FormData, FileReader: dom.window.FileReader, requestAnimationFrame: (callback) => callback() });
  window.scrollTo = () => {};
  window.matchMedia = () => ({ matches: true });
  window.HTMLDialogElement.prototype.showModal = function () { this.setAttribute("open", ""); };
  window.HTMLDialogElement.prototype.close = function () { this.removeAttribute("open"); };
  if (session) localStorage.setItem("digisutra_session", JSON.stringify(session));
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    const call = { path: new URL(url).pathname, method: options.method || "GET", body: options.body };
    calls.push(call);
    const result = await respond(call);
    const status = typeof result?.status === "number" ? result.status : 200;
    const data = typeof result?.status === "number" ? result.data : result;
    return { ok: status < 400, status, statusText: "Error", text: async () => JSON.stringify(data) };
  };
  const app = createApp();
  const init = app.init();
  const root = document.getElementById("app");
  return { dom, calls, init, root, close: () => dom.window.close() };
}
function submit(form, submitter = form.querySelector('button[type="submit"]')) {
  form.dispatchEvent(new window.SubmitEvent("submit", { bubbles: true, cancelable: true, submitter }));
}

test("late catalog response cannot replace a newer sign-in route", async () => {
  let release;
  const env = setup("/catalog", null, () => new Promise((resolve) => { release = resolve; }));
  try {
    env.root.querySelector('a[href="/auth"]').click();
    await until(() => env.root.querySelector("[data-auth-form]"));
    release([]); await env.init;
    assert.equal(window.location.pathname, "/auth");
    assert.ok(env.root.querySelector("[data-auth-form]"));
  } finally { env.close(); }
});

test("expired library session keeps the sign-in screen and return destination", async () => {
  const env = setup("/library", customer, () => ({ status: 401, data: { error: "Expired" } }));
  try {
    await env.init;
    assert.equal(window.location.pathname, "/auth");
    assert.equal(new URLSearchParams(window.location.search).get("returnTo"), "/library");
    assert.ok(env.root.querySelector("[data-auth-form]"));
    assert.equal(localStorage.getItem("digisutra_session"), null);
  } finally { env.close(); }
});

test("admin reviews details and Cancel/Escape never write an approval", async () => {
  const application = { uuid: "application::1", status: "kyc_verified", store_name: "Store", legal_name: "Legal identity" };
  const env = setup("/admin/seller-applications", admin, ({ path }) => decodeURIComponent(path).endsWith("application::1/") ? application : [application]);
  try {
    await env.init;
    for (const escape of [false, true]) {
      env.root.querySelector('[data-admin-seller-action="approve"]').click();
      await until(() => document.querySelector("dialog[open]"));
      assert.match(document.querySelector("dialog").textContent, /Legal identity/);
      if (escape) document.querySelector("dialog").dispatchEvent(new window.Event("cancel", { cancelable: true }));
      else document.querySelector("[data-dialog-cancel]").click();
      await tick();
      assert.equal(document.querySelector("dialog"), null);
    }
    assert.equal(env.calls.filter((call) => call.method === "POST").length, 0);
  } finally { env.close(); }
});

test("rapid checkout activation creates one ledger and provider request", async () => {
  let release;
  const env = setup("/checkout/product::1", customer, ({ path }) => {
    if (path === "/v1/ledger/orders/") return new Promise((resolve) => { release = resolve; });
    if (path === "/v1/payments/orders/") return { uuid: "order::1" };
    return product;
  });
  try {
    await env.init;
    const button = env.root.querySelector("[data-start-checkout]");
    button.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
    button.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
    await until(() => release);
    release({ uuid: "order::1" });
    await until(() => env.root.querySelector("[data-open-razorpay]"));
    assert.equal(env.calls.filter((call) => call.path === "/v1/ledger/orders/").length, 1);
    assert.equal(env.calls.filter((call) => call.path === "/v1/payments/orders/").length, 1);
  } finally { env.close(); }
});

test("login restores checkout and rejects external return URLs", async () => {
  const env = setup("/auth?returnTo=%2Fcheckout%2Fproduct%3A%3A1", null, ({ path }) => path.endsWith("/login/") ? customer : product);
  try {
    await env.init;
    const form = env.root.querySelector("[data-auth-form]");
    form.elements.username.value = "buyer"; form.elements.password.value = "password";
    submit(form);
    await until(() => env.root.querySelector("[data-start-checkout]"));
    assert.equal(window.location.pathname, "/checkout/product::1");
    assert.equal(safeReturnPath("https://evil.example/", window.location.origin), null);
    assert.equal(safeReturnPath("//evil.example/", window.location.origin), null);
    assert.equal(safeReturnPath(null, window.location.origin), null);
  } finally { env.close(); }
});

test("form errors are field-associated, focused and block invalid auth requests", async () => {
  const env = setup("/auth", null);
  try {
    await env.init;
    const form = env.root.querySelector("[data-auth-form]");
    submit(form); await tick();
    const input = form.elements.username;
    assert.equal(input.getAttribute("aria-invalid"), "true");
    assert.ok(document.getElementById(input.getAttribute("aria-describedby")));
    assert.equal(document.activeElement, input);
    assert.equal(env.calls.length, 0);
    const toggle = env.root.querySelector("[data-toggle-password]"); toggle.click();
    assert.equal(form.elements.password.type, "text");
    assert.equal(toggle.getAttribute("aria-pressed"), "true");
  } finally { env.close(); }
});

test("failed upload retries the same private product instead of creating another", async () => {
  let fail = true;
  const seller = { ...customer, user_type: "seller" };
  const env = setup("/seller/products/new", seller, ({ path, method }) => {
    if (path === "/v1/products/" && method === "POST") return product;
    if (path === "/v1/assets/upload-target/") { fail = false; return { status: 503, data: { error: "Storage unavailable" } }; }
    return [];
  });
  try {
    await env.init;
    const form = env.root.querySelector("[data-product-form]");
    form.elements.title.value = "Guide"; form.elements.price.value = "99";
    const NativeFormData = globalThis.FormData;
    globalThis.FormData = class extends NativeFormData {
      constructor(value) { super(value); this.set("asset_file", new window.File(["paid"], "guide.txt")); }
      get(name) { if (name === "asset_file") return { name: "guide.txt", size: 4, type: "text/plain", arrayBuffer: async () => new ArrayBuffer(4) }; return super.get(name); }
    };
    // File validity is a browser-owned constraint; selecting it is simulated in this DOM test.
    form.elements.asset_file.removeAttribute("required");
    submit(form);
    await until(() => !fail && form.getAttribute("aria-busy") === null);
    assert.equal(form.dataset.productUuid, product.uuid);
    assert.match(form.querySelector("[data-form-error]").textContent, /product is saved/);
    submit(form); await until(() => form.getAttribute("aria-busy") === null);
    const creates = env.calls.filter((call) => call.path === "/v1/products/" && call.method === "POST");
    assert.equal(creates.length, 1);
    assert.equal(JSON.parse(creates[0].body).is_public, false);
    assert.equal(env.calls.filter((call) => call.path.endsWith("/publish/")).length, 0);
  } finally { env.close(); }
});

test("dirty form navigation can be cancelled without losing input", async () => {
  const env = setup("/auth", null);
  try {
    await env.init;
    const input = env.root.querySelector('input[name="username"]'); input.value = "kept";
    input.dispatchEvent(new window.Event("input", { bubbles: true }));
    env.root.querySelector('a[href="/"]').click();
    await until(() => document.querySelector("dialog[open]"));
    document.querySelector("[data-dialog-cancel]").click(); await tick();
    assert.equal(window.location.pathname, "/auth");
    assert.equal(env.root.querySelector('input[name="username"]').value, "kept");
  } finally { env.close(); }
});

test("forbidden and unknown routes keep navigable, honest pages", async () => {
  for (const [path, title] of [["/admin/seller-applications", "Access denied"], ["/missing", "Page not found"]]) {
    const env = setup(path, customer);
    try { await env.init; assert.equal(env.root.querySelector("h1").textContent, title); assert.ok(env.root.querySelector("header")); assert.equal(env.calls.length, 0); }
    finally { env.close(); }
  }
});

test("review failure retains the dialog and note for correction", async () => {
  const application = { uuid: "application::1", status: "kyc_verified", store_name: "Store" };
  const env = setup("/admin/seller-applications", admin, ({ path, method }) => method === "POST" ? { status: 409, data: { error: "Application changed; review again" } } : decodeURIComponent(path).endsWith("application::1/") ? application : [application]);
  try {
    await env.init;
    env.root.querySelector('[data-admin-seller-action="approve"]').click();
    await until(() => document.querySelector("dialog[open]"));
    document.querySelector("dialog textarea").value = "Reviewed supporting evidence";
    submit(document.querySelector("dialog form"));
    await until(() => document.querySelector("dialog [data-form-error]")?.textContent.includes("Application changed"));
    assert.ok(document.querySelector("dialog[open]"));
    assert.equal(document.querySelector("dialog textarea").value, "Reviewed supporting evidence");
    assert.equal(env.calls.filter((call) => call.method === "POST").length, 1);
  } finally { env.close(); }
});

test("seller lifecycle hides invalid submission and repeat-information actions", async () => {
  const { sellerApplication, adminSellerApplications } = await import("../src/views/marketplace.js");
  const env = setup("/auth", null);
  try {
    await env.init;
    for (const status of ["submitted", "under_review", "withdrawn", "approved", "kyc_pending"]) {
      env.root.innerHTML = sellerApplication({ session: customer, application: { status } });
      assert.equal(env.root.querySelector('[data-seller-application-action="submit"]'), null);
    }
    env.root.innerHTML = adminSellerApplications({ session: admin, applications: [{ uuid: "app::1", status: "needs_information" }] });
    assert.equal(env.root.querySelector('[data-admin-seller-action="request-information"]').disabled, true);
  } finally { env.close(); }
});

test("payment popup cannot be duplicated and server status restores a paid purchase", async () => {
  let opened = 0, configuration;
  const env = setup("/checkout/product::1", customer, ({ path }) => {
    if (path === "/v1/ledger/orders/") return { uuid: "order::1" };
    if (path === "/v1/payments/orders/") return { provider_order_id: "provider::1", razorpay_key_id: "test-key", razorpay_order: { amount: 9900, currency: "INR" } };
    if (path.startsWith("/v1/ledger/orders/")) return { payment_status: "paid" };
    if (path === "/v1/ledger/purchases/") return [];
    return product;
  });
  window.Razorpay = class {
    constructor(options) { configuration = options; }
    on() {}
    open() { opened++; }
    close() { configuration.modal.ondismiss(); }
  };
  try {
    await env.init;
    env.root.querySelector("[data-start-checkout]").click();
    await until(() => opened === 1 && !env.root.hasAttribute("aria-busy"));
    env.root.querySelector("[data-open-razorpay]").click(); await tick();
    assert.equal(opened, 1);
    configuration.modal.ondismiss();
    assert.match(env.root.querySelector("[data-checkout-error]").textContent, /closed/);
    env.root.querySelector("[data-check-payment]").click();
    await until(() => window.location.pathname === "/library");
    await until(() => env.root.querySelector("h1")?.textContent === "Library");
    assert.equal(env.calls.filter((call) => call.path === "/v1/ledger/orders/").length, 1);
  } finally { env.close(); }
});
