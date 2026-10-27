import { APP, API_PATHS, ROUTES } from "./constants/app.js";
import { createApi, isSellerOrAdmin } from "./services/api.js";
import { readSession, writeSession } from "./services/storage.js";
import { authorizeAndLogDownload, uploadProductAsset, uploadProductPreview, validatePreview } from "./services/assetTransfers.js";
import * as view from "./views/marketplace.js";
import { askDialog, runOnce, validateForm, formError, safeReturnPath } from "./services/ui.js";
import { runtimeConfig } from "./config/runtime.js";
import { loadGoogleSignIn } from "./services/googleSignIn.js";

export function createApp() {
  let renderGeneration = 0;
  let productLoadGeneration = 0;
  let dirty = false;
  let previewGeneration = 0;
  let razorpayScript = null;
  let paymentInstance = null;
  let googleBusy = false;
  let historyIndex = window.history.state?.uiIndex || 0;
  let restoredHistory = null;
  window.history.replaceState({ ...window.history.state, uiIndex: historyIndex }, "");
  const uploadStages = new WeakMap();
  const root = document.getElementById("app");
  const state = {
    session: readSession(),
    products: [],
    productsLoaded: false,
    query: new URLSearchParams(window.location.search).get("q") || "",
    category: new URLSearchParams(window.location.search).get("category") || "all",
    checkout: null,
  };
  const api = createApi({
    onUnauthorized: () => {
      state.session = null;
      navigate(authUrl(), true, true);
      toast("Your session expired. Please sign in again.");
    },
  });

  function toast(message) {
    const host = document.getElementById("toastHost");
    const node = document.createElement("div");
    node.className = "toast";
    node.textContent = message;
    host.append(node);
    requestAnimationFrame(() => node.classList.add("show"));
    window.setTimeout(() => {
      node.classList.remove("show");
      window.setTimeout(() => node.remove(), 200);
    }, 2600);
  }

  function setSession(session) {
    state.session = session;
    writeSession(session);
  }

  function authUrl() {
    return `${ROUTES.auth}?returnTo=${encodeURIComponent(window.location.pathname + window.location.search)}`;
  }

  async function mountGoogleButton(generation, linking = false) {
    const target = root.querySelector("[data-google-button]");
    if (!target || !runtimeConfig.googleClientId) return;
    const errorNode = root.querySelector("[data-google-error]");
    try {
      const sdk = await loadGoogleSignIn();
      if (generation !== renderGeneration || !target.isConnected) return;
      sdk.initialize({ client_id: runtimeConfig.googleClientId, callback: async ({ credential }) => {
        if (generation !== renderGeneration || googleBusy || !credential) return;
        googleBusy = true;
        errorNode.textContent = "";
        try {
          const result = await api.request(linking ? API_PATHS.googleLink : API_PATHS.googleLogin, {
            method: "POST", body: JSON.stringify({ credential }),
          });
          if (generation !== renderGeneration) return;
          if (linking) {
            setSession({ ...state.session, google_linked: result.google_linked });
            void render();
            toast("Google sign-in linked to your account.");
          } else {
            setSession(result);
            const returnTo = safeReturnPath(new URLSearchParams(window.location.search).get("returnTo"), window.location.origin);
            navigate(returnTo || (result.user_type === APP.roles.customer ? ROUTES.settings : ROUTES.seller), true, true);
          }
        } catch (error) {
          if (errorNode.isConnected) errorNode.textContent = error.message;
        } finally { googleBusy = false; }
      } });
      sdk.renderButton(target, { theme: "outline", size: "large", width: Math.min(target.clientWidth, 360), text: linking ? "continue_with" : "signin_with" });
    } catch (error) {
      if (errorNode.isConnected) errorNode.textContent = error.message;
    }
  }

  async function navigate(path, replace = false, force = false) {
    if (dirty && !force) {
      const decision = await askDialog({ title: "Discard unsaved changes?", description: "Your unsaved input will be lost. Saved server drafts remain available.", action: "Discard changes", danger: true });
      if (!decision) return;
    }
    dirty = false;
    if (paymentInstance) { paymentInstance.close(); paymentInstance = null; }
    if (path.split("?")[0] === ROUTES.catalog) {
      const params = new URL(path, window.location.origin).searchParams;
      state.query = params.get("q") || "";
      state.category = params.get("category") || "all";
    }
    if (replace) window.history.replaceState({ uiIndex: historyIndex }, "", path);
    else window.history.pushState({ uiIndex: ++historyIndex }, "", path);
    void render();
    window.scrollTo({ top: 0, behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth" });
  }

  function catalogUrl() {
    const params = new URLSearchParams();
    if (state.query) params.set("q", state.query);
    if (state.category !== "all") params.set("category", state.category);
    return `${ROUTES.catalog}${params.size ? `?${params}` : ""}`;
  }

  function route() {
    const productMatch = window.location.pathname.match(/^\/products\/([^/]+)$/);
    if (productMatch) return { name: "detail", uuid: decodeURIComponent(productMatch[1]) };
    const checkoutMatch = window.location.pathname.match(/^\/checkout\/([^/]+)$/);
    if (checkoutMatch) return { name: "checkout", uuid: decodeURIComponent(checkoutMatch[1]) };
    return { name: window.location.pathname.replace(/\/$/, "") || ROUTES.home };
  }

  async function loadProducts() {
    if (state.productsLoaded) return;
    const generation = ++productLoadGeneration;
    const products = await api.request(API_PATHS.products);
    if (generation !== productLoadGeneration) return;
    state.products = products;
    state.productsLoaded = true;
  }

  async function render() {
    const generation = ++renderGeneration;
    const display = (html) => {
      if (generation !== renderGeneration) return;
      root.innerHTML = html;
      root.querySelector("h1")?.setAttribute("tabindex", "-1");
      root.querySelector("h1")?.focus({ preventScroll: true });
    };
    let current;
    try { current = route(); } catch { current = { name: "invalid" }; }
    const titles = {
      [ROUTES.home]: "DigiSutra — Digital goods for brighter days",
      [ROUTES.catalog]: "Discover products — DigiSutra",
      [ROUTES.auth]: "Sign in — DigiSutra",
      [ROUTES.library]: "My library — DigiSutra",
      [ROUTES.seller]: "Seller overview — DigiSutra",
      [ROUTES.sellerProducts]: "Seller products — DigiSutra",
      [ROUTES.sellerProductNew]: "Create product — DigiSutra",
      [ROUTES.sellerPayouts]: "Payouts — DigiSutra",
      [ROUTES.becomeSeller]: "Become a seller — DigiSutra",
      [ROUTES.adminSellerApplications]: "Seller applications — DigiSutra",
      [ROUTES.settings]: "Account settings — DigiSutra",
      detail: "Product details — DigiSutra",
      checkout: "Checkout — DigiSutra",
    };
    document.title = current.name === ROUTES.auth && new URLSearchParams(window.location.search).get("mode") === "signup"
      ? "Create account — DigiSutra" : titles[current.name] || "Page not found — DigiSutra";
    const known = new Set([...Object.keys(titles), "detail", "checkout"]);
    if (!known.has(current.name)) {
      display(view.pageState({ session: state.session, title: "Page not found", message: "Check the address or return to the marketplace." }));
      return;
    }
    if (current.name === ROUTES.auth) {
      display(view.auth({ mode: new URLSearchParams(window.location.search).get("mode") === "signup" ? "signup" : "login", googleEnabled: Boolean(runtimeConfig.googleClientId) }));
      void mountGoogleButton(generation);
      return;
    }
    if (current.name === ROUTES.home || current.name === ROUTES.catalog) {
      try {
        if (!state.productsLoaded) display(current.name === ROUTES.home
          ? view.home({ session: state.session, products: [], loading: true })
          : view.catalogLoading({ session: state.session }));
        await loadProducts();
      } catch (error) {
        display(view.catalog({ session: state.session, products: [], availableProducts: state.products, query: state.query, category: state.category, error: error.message }));
        return;
      }
      const products = state.products.filter((p) => (
        state.category === "all" || p.category === state.category
      ) && (
        !state.query || `${p.title} ${p.description} ${p.category}`.toLowerCase().includes(state.query.toLowerCase())
      ));
      display(current.name === ROUTES.home
        ? view.home({ session: state.session, products: state.products })
        : view.catalog({ session: state.session, products, availableProducts: state.products, query: state.query, category: state.category }));
      return;
    }
    if (current.name === "detail") {
      try {
        display(view.pageState({ session: state.session, title: "Loading product", message: "Fetching the product details…", loading: true }));
        display(view.detail({ session: state.session, product: await api.request(API_PATHS.product(current.uuid)) }));
      } catch (error) {
        display(error.status === 404 ? view.detail({ session: state.session, product: null }) : view.pageState({ session: state.session, title: "Could not load product", message: error.message, retry: true }));
      }
      return;
    }
    if (!state.session) {
      navigate(authUrl(), true, true);
      return;
    }
    const sellerRoute = [ROUTES.seller, ROUTES.sellerProducts, ROUTES.sellerProductNew, ROUTES.sellerPayouts].includes(current.name);
    if ((sellerRoute && !isSellerOrAdmin(state.session)) || (current.name === ROUTES.adminSellerApplications && state.session.user_type !== APP.roles.admin)) {
      document.title = "Access denied — DigiSutra";
      display(view.pageState({ session: state.session, title: "Access denied", message: "This account does not have permission to open this workspace." }));
      return;
    }
    display(view.pageState({ session: state.session, title: "Loading workspace", message: "Fetching the latest information…", loading: true }));
    try {
      if (current.name === "checkout") {
        const product = await api.request(API_PATHS.product(current.uuid));
        const checkout = state.checkout?.productUuid === current.uuid ? state.checkout : null;
        display(view.checkout({ session: state.session, product, checkout }));
      } else if (current.name === ROUTES.settings) {
        display(view.settings({ session: state.session, googleEnabled: Boolean(runtimeConfig.googleClientId) }));
        if (!state.session.google_linked) void mountGoogleButton(generation, true);
      } else if (current.name === ROUTES.library) {
        display(view.library({ session: state.session, purchases: await api.request(API_PATHS.purchases) }));
      } else if (current.name === ROUTES.becomeSeller && state.session.user_type === APP.roles.customer) {
        const result = await api.request(API_PATHS.sellerApplication);
        display(view.sellerApplication({ session: state.session, application: result?.application || result }));
      } else if (current.name === ROUTES.adminSellerApplications && state.session.user_type === APP.roles.admin) {
        display(view.adminSellerApplications({
          session: state.session,
          applications: await api.request(API_PATHS.adminSellerApplications),
        }));
      } else if (current.name === ROUTES.seller && isSellerOrAdmin(state.session)) {
        const [metrics, readiness, products] = await Promise.all([api.request(API_PATHS.dashboard), api.request(API_PATHS.payoutSummary), api.request(API_PATHS.ownedProducts)]);
        const summary = { ...metrics, ...readiness };
        display(view.seller({ session: state.session, summary, products }));
      } else if (current.name === ROUTES.sellerProducts && isSellerOrAdmin(state.session)) {
        display(view.sellerProducts({ session: state.session, products: await api.request(API_PATHS.ownedProducts) }));
      } else if (current.name === ROUTES.sellerProductNew && isSellerOrAdmin(state.session)) {
        const draftUuid = new URLSearchParams(window.location.search).get("draft");
        const product = draftUuid ? (await api.request(API_PATHS.ownedProducts)).find((item) => item.uuid === draftUuid && !item.is_public) : null;
        if (draftUuid && !product) throw new Error("This private draft is unavailable. Return to your products.");
        display(view.sellerProductNew({ session: state.session, product }));
      } else if (current.name === ROUTES.sellerPayouts && isSellerOrAdmin(state.session)) {
        display(view.sellerPayouts({ session: state.session, summary: await api.request(API_PATHS.payoutSummary) }));
      } else {
        display(view.home({ session: state.session, products: state.products }));
      }
    } catch (error) {
      display(view.pageState({ session: state.session, title: error.status === 403 ? "Access denied" : "Could not load this workspace", message: error.message, retry: error.status !== 403 }));
    }
  }
  async function submitAuth(form) {
    if (!validateForm(form)) return;
    const active = renderGeneration;
    const returnTo = safeReturnPath(new URLSearchParams(window.location.search).get("returnTo"), window.location.origin);
    const mode = form.dataset.mode;
    const data = Object.fromEntries(new FormData(form).entries());
    const errorNode = form.querySelector("[data-form-error]");
    errorNode.textContent = "";
    try {
      if (mode === "signup") {
        await api.request(API_PATHS.signup, {
          method: "POST",
          body: JSON.stringify({ ...data, firstname: data.first_name, lastname: data.last_name }),
        });
      }
      const session = await api.request(API_PATHS.login, {
        method: "POST",
        body: JSON.stringify({ username: data.username, password: data.password }),
      });
      if (active !== renderGeneration) return;
      setSession(session);
      dirty = false;
      navigate(returnTo || (session.user_type === APP.roles.customer ? ROUTES.settings : ROUTES.seller), true, true);
    } catch (error) {
      if (form.isConnected) formError(form, error.message);
    }
  }

  function sellerApplicationPayload(form) {
    const data = Object.fromEntries(new FormData(form).entries());
    data.terms_accepted = form.elements.terms_accepted.checked;
    return data;
  }

  async function submitSellerApplication(form, submit) {
    if (submit && !validateForm(form)) return;
    const active = renderGeneration;
    const errorNode = form.querySelector("[data-form-error]");
    errorNode.textContent = "";
    try {
      const result = await api.request(submit ? API_PATHS.sellerApplicationSubmit : API_PATHS.sellerApplication, {
        method: "POST",
        body: JSON.stringify(sellerApplicationPayload(form)),
      });
      if (active !== renderGeneration) return;
      dirty = false;
      root.innerHTML = view.sellerApplication({ session: state.session, application: result });
      toast(submit ? "Seller application submitted" : "Seller application saved");
    } catch (error) {
      if (form.isConnected) formError(form, error.message);
    }
  }

  async function reviewSellerApplication(uuid, action) {
    const active = renderGeneration;
    const application = await api.request(API_PATHS.adminSellerApplication(uuid));
    if (active !== renderGeneration) return;
    const labels = { view: "Close review", approve: "Approve seller", "verify-kyc": "Verify KYC", "fail-kyc": "Fail KYC", reject: "Reject application", "request-information": "Request information", "start-kyc-review": "Start KYC review" };
    const decision = await askDialog({
      title: application.store_name || "Seller application",
      description: action === "view" ? "Review the submitted application details." : `${labels[action]}. Review the submitted details before recording this decision. Manual review does not perform external identity or bank verification.`,
      details: view.applicationDetails(application), action: labels[action], note: action !== "view",
      required: ["reject", "request-information", "fail-kyc"].includes(action),
      danger: ["reject", "fail-kyc"].includes(action),
      onConfirm: async ({ note }) => {
        if (action === "view") return;
        if (active !== renderGeneration) throw new Error("The active page changed. Close this review and reopen the application.");
        const body = { note };
        if (action === "verify-kyc") Object.assign(body, { provider: "manual", provider_account_status: "activated", fund_account_status: "validated" });
        if (action === "fail-kyc") Object.assign(body, { provider_account_status: "needs_clarification", fund_account_status: "failed" });
        await api.request(API_PATHS.adminSellerApplicationAction(uuid, action), { method: "POST", body: JSON.stringify(body) });
      },
    });
    if (!decision || action === "view" || active !== renderGeneration) return;
    toast(action === "approve" ? "Seller approved" : "Seller request updated");
    await render();
  }

  async function startCheckout(productUuid) {
    const active = renderGeneration;
    const errorNode = root.querySelector("[data-checkout-error]");
    if (errorNode) errorNode.textContent = "";
    try {
      const product = await api.request(API_PATHS.product(productUuid));
      if (active !== renderGeneration) return;
      const existing = state.checkout?.productUuid === productUuid ? state.checkout : null;
      const order = existing?.ledger || await api.request(API_PATHS.ledgerOrders, {
        method: "POST",
        body: JSON.stringify({ product_uuid: product.uuid }),
      });
      if (active !== renderGeneration) return;
      state.checkout = { ...existing, productUuid, product, ledger: order };
      const provider = existing?.order || await api.request(API_PATHS.paymentOrders, {
        method: "POST",
        body: JSON.stringify({ order_uuid: order.uuid }),
      });
      if (active !== renderGeneration) return;
      state.checkout = { productUuid, product, ledger: order, order: provider, provider: provider.razorpay_order || null };
      root.innerHTML = view.checkout({ session: state.session, product, checkout: state.checkout });
      await openRazorpay();
    } catch (error) {
      if (active !== renderGeneration) return;
      if (errorNode?.isConnected) errorNode.textContent = error.message;
      else toast(error.message);
    }
  }

  function loadRazorpayScript() {
    if (razorpayScript) return razorpayScript;
    if (window.Razorpay) return Promise.resolve();
    razorpayScript = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      const failed = () => {
        window.clearTimeout(timeout);
        razorpayScript = null;
        script.remove();
        reject(new Error("Unable to load Razorpay Checkout. Retry opening payment."));
      };
      const timeout = window.setTimeout(failed, runtimeConfig.requestTimeoutMs);
      script.onload = () => { window.clearTimeout(timeout); resolve(); };
      script.onerror = failed;
      document.head.append(script);
    });
    return razorpayScript;
  }

  async function openRazorpay() {
    if (paymentInstance) return;
    const checkout = state.checkout;
    const active = renderGeneration;
    const showPaymentError = (message) => { if (active === renderGeneration) { const node = root.querySelector("[data-checkout-error]"); if (node) node.textContent = message; } };
    const errorNode = root.querySelector("[data-checkout-error]");
    if (!checkout?.order?.razorpay_key_id || !checkout?.order?.provider_order_id) {
      if (errorNode) errorNode.textContent = "Payment order is not ready yet.";
      return;
    }
    try {
      await loadRazorpayScript();
      if (active !== renderGeneration || !state.session) return;
      const razorpayOrder = checkout.provider || {};
      const instance = new window.Razorpay({
        key: checkout.order.razorpay_key_id,
        amount: razorpayOrder.amount,
        currency: razorpayOrder.currency || checkout.product.currency || APP.defaultCurrency,
        name: APP.name,
        description: checkout.product.title,
        order_id: checkout.order.provider_order_id,
        prefill: {
          name: `${state.session.first_name || ""} ${state.session.last_name || ""}`.trim(),
          email: state.session.email || state.session.username,
        },
        modal: { ondismiss: () => { paymentInstance = null; showPaymentError("Payment window closed. Check payment status before retrying."); } },
        handler: async (response) => {
          paymentInstance = null;
          try {
            await api.request(API_PATHS.paymentConfirm, { method: "POST", body: JSON.stringify(response) });
            if (active !== renderGeneration) return;
            toast("Payment confirmed");
            state.checkout = null;
            navigate(ROUTES.library, true);
          } catch (error) {
            showPaymentError(error.message);
          }
        },
      });
      instance.on("payment.failed", () => showPaymentError("Payment was not confirmed. Check payment status before retrying."));
      paymentInstance = instance;
      instance.open();
    } catch (error) {
      paymentInstance = null;
      showPaymentError(error.message);
    }
  }

  root.addEventListener("click", async (event) => {
    const passwordToggle = event.target.closest("[data-toggle-password]");
    if (passwordToggle) {
      const input = root.querySelector("#authPassword");
      const reveal = input.type === "password";
      input.type = reveal ? "text" : "password";
      passwordToggle.textContent = reveal ? "Hide password" : "Show password";
      passwordToggle.setAttribute("aria-pressed", String(reveal));
      return;
    }
    if (event.target.closest("[data-refresh-page]")) { state.productsLoaded = false; await navigate(window.location.pathname + window.location.search, true); return; }
    if (event.target.closest("[data-clear-input]")) {
      const input = root.querySelector("#homeSearch"); input.value = ""; input.focus();
      event.target.closest("[data-clear-input]").hidden = true; return;
    }
    if (event.target.closest("[data-remove-preview]")) {
      previewGeneration++;
      root.querySelector("[data-preview-input]").value = "";
      const output = root.querySelector("[data-preview-output]");
      output.textContent = "No preview selected"; output.classList.remove("has-image"); dirty = true; return;
    }
    const withdraw = event.target.closest("[data-withdraw-application]");
    if (withdraw) {
      await runOnce(root, async () => {
        const active = renderGeneration;
        const decision = await askDialog({ title: "Withdraw application?", description: "This ends review of this application. You cannot resubmit a withdrawn application.", action: "Withdraw application", danger: true });
        if (!decision || active !== renderGeneration) return;
        await api.request(API_PATHS.sellerApplicationWithdraw(withdraw.dataset.withdrawApplication), { method: "POST", body: "{}" });
        if (active === renderGeneration) { dirty = false; await render(); }
      }).catch((error) => toast(error.message));
      return;
    }
    if (event.target.closest("[data-check-payment]")) {
      await runOnce(root, async () => {
        const active = renderGeneration;
        const uuid = state.checkout?.ledger?.uuid;
        if (!uuid) return;
        const order = await api.request(API_PATHS.order(uuid));
        if (active !== renderGeneration) return;
        if (order.payment_status === "paid") { state.checkout = null; navigate(ROUTES.library, true, true); }
        else root.querySelector("[data-checkout-error]").textContent = `Payment status: ${order.payment_status}. Check your library before starting another payment.`;
      }).catch((error) => toast(error.message));
      return;
    }
    const link = event.target.closest("[data-link]");
    if (link) {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button > 0) return;
      event.preventDefault();
      navigate(link.getAttribute("href"));
      return;
    }
    const category = event.target.closest("[data-category]");
    if (category) {
      state.query = "";
      state.category = category.dataset.category;
      navigate(catalogUrl());
      return;
    }
    if (event.target.closest("[data-clear-search]")) {
      state.query = "";
      window.history.replaceState({ uiIndex: historyIndex }, "", catalogUrl());
      await render();
      root.querySelector("[data-catalog-form] input[name=q]")?.focus();
      return;
    }
    if (event.target.closest("[data-reset-catalog]")) {
      state.query = "";
      state.category = "all";
      navigate(ROUTES.catalog, true);
      return;
    }
    if (event.target.closest("[data-retry-products]")) {
      state.productsLoaded = false;
      await render();
      return;
    }
    const tab = event.target.closest("[data-auth-mode]");
    if (tab) {
      const params = new URLSearchParams(window.location.search);
      params.set("mode", tab.dataset.authMode);
      navigate(`${ROUTES.auth}?${params}`);
      return;
    }
    if (event.target.closest("[data-logout]")) {
      setSession(null);
      state.checkout = null;
      toast("Signed out");
      navigate(ROUTES.home, true);
      return;
    }
    const buy = event.target.closest("[data-buy-product]");
    if (buy) {
      if (!state.session) {
        navigate(`${ROUTES.auth}?returnTo=${encodeURIComponent(ROUTES.checkout(buy.dataset.buyProduct))}`);
        return;
      }
      navigate(ROUTES.checkout(buy.dataset.buyProduct));
      return;
    }
    if (event.target.closest("[data-start-checkout]")) {
      await runOnce(root, () => startCheckout(event.target.closest("[data-start-checkout]").dataset.startCheckout));
      return;
    }
    if (event.target.closest("[data-open-razorpay]")) {
      await runOnce(root, openRazorpay);
      return;
    }
    const adminAction = event.target.closest("[data-admin-seller-action]");
    if (adminAction) {
      await runOnce(root, () => reviewSellerApplication(adminAction.dataset.applicationUuid, adminAction.dataset.adminSellerAction)).catch((error) => toast(error.message));
      return;
    }
    const libraryItem = event.target.closest("[data-library-order]");
    if (libraryItem) {
      const button = libraryItem;
      button.disabled = true;
      try {
        const downloadUrl = await authorizeAndLogDownload({
          api,
          orderUuid: button.dataset.libraryOrder,
          assetUuid: button.dataset.libraryAsset,
        });
        if (button.isConnected) window.location.assign(downloadUrl);
      } catch (error) {
        button.disabled = false;
        toast(error.message);
      } finally { button.disabled = false; }
      return;
    }
    if (event.target.closest("[data-refresh-admin-sellers]")) {
      await render();
    }
  });

  root.addEventListener("submit", async (event) => {
    if (event.isComposing) { event.preventDefault(); return; }
    if (event.target.matches("[data-home-search]")) {
      event.preventDefault();
      state.query = String(new FormData(event.target).get("q") || "").trim();
      state.category = "all";
      navigate(catalogUrl());
      return;
    }
    if (event.target.matches("[data-auth-form]")) {
      event.preventDefault();
      await runOnce(event.target, () => submitAuth(event.target));
    }
    if (event.target.matches("[data-catalog-form]")) {
      event.preventDefault();
      const data = new FormData(event.target);
      state.query = String(data.get("q") || "").trim();
      state.category = String(data.get("category") || "all");
      navigate(catalogUrl(), true);
    }
  });

  root.addEventListener("submit", async (event) => {
    if (!event.target.matches("[data-product-form]")) return;
    event.preventDefault();
    if (event.isComposing) return;
    const form = event.target;
    if (!validateForm(form)) return;
    await runOnce(form, async () => {
      const active = renderGeneration;
      const errorNode = form.querySelector("[data-form-error]");
      errorNode.textContent = "";
      const formData = new FormData(form);
      const file = formData.get("asset_file");
      const previewImage = formData.get("preview_image");
      formData.delete("asset_file");
      formData.delete("preview_image");
      const data = Object.fromEntries(formData.entries());
      try {
        if (!file?.name) throw new Error("Choose a product file to upload.");
        validatePreview(previewImage);
        const product = form.dataset.productUuid ? { uuid: form.dataset.productUuid } : await api.request(API_PATHS.products, { method: "POST", body: JSON.stringify({ ...data, is_active: false, is_public: false }) });
        form.dataset.productUuid = product.uuid;
        for (const field of form.querySelectorAll("input:not([type=file]), textarea")) field.readOnly = true;
        if (active !== renderGeneration) return;
        form.querySelector("[data-upload-status]").textContent = "Draft saved. Uploading the paid file…";
        const stage = uploadStages.get(form) || {};
        uploadStages.set(form, stage);
        if (stage.file !== file) {
          await uploadProductAsset({ api, productUuid: product.uuid, file });
          stage.file = file;
        }
        if (active !== renderGeneration) return;
        form.querySelector("[data-upload-status]").textContent = "Paid file verified. Uploading the preview…";
        if (stage.preview !== previewImage) {
          await uploadProductPreview({ api, productUuid: product.uuid, file: previewImage });
          stage.preview = previewImage;
        }
        if (active !== renderGeneration) return;
        await api.request(API_PATHS.productPublish(product.uuid), { method: "POST" });
        state.productsLoaded = false;
        if (active !== renderGeneration) return;
        dirty = false;
        toast(previewImage?.name ? "Product file and preview verified" : "Product created and file verified");
        navigate(ROUTES.sellerProducts, true, true);
      } catch (error) {
        if (form.isConnected) formError(form, `${error.message}${form.dataset.productUuid ? " Your product is saved. Check Products for its current status, or retry these upload steps." : ""}`);
      }
    });
  });

  root.addEventListener("change", (event) => {
    if (event.target.closest("[data-product-form]")) dirty = true;
    if (!event.target.matches("[data-preview-input]")) return;
    const output = event.target.closest("[data-preview-section]")?.querySelector("[data-preview-output]");
    const file = event.target.files?.[0];
    const generation = ++previewGeneration;
    if (!output) return;
    if (!file) { output.textContent = "No preview selected"; output.classList.remove("has-image"); return; }
    try { validatePreview(file); } catch (error) { formError(event.target.closest("form"), error.message); event.target.value = ""; output.textContent = "No preview selected"; output.classList.remove("has-image"); return; }
    const reader = new FileReader();
    reader.addEventListener("load", () => {
      if (generation !== previewGeneration || !output.isConnected) return;
      output.innerHTML = `<img src="${reader.result}" alt="Selected product preview" />`;
      output.classList.add("has-image");
    });
    reader.readAsDataURL(file);
  });

  root.addEventListener("submit", async (event) => {
    if (!event.target.matches("[data-seller-application-form]")) return;
    event.preventDefault();
    await runOnce(event.target, () => submitSellerApplication(event.target, event.submitter?.dataset.sellerApplicationAction === "submit"));
  });

  root.addEventListener("input", (event) => {
    if (event.target.closest("[data-product-form], [data-seller-application-form], [data-auth-form]")) dirty = true;
    if (event.target.matches("input[name=q]")) {
      const clear = event.target.closest("form").querySelector("[data-clear-search], [data-clear-input]");
      if (clear) clear.hidden = !event.target.value;
    }
  });
  root.addEventListener("error", (event) => {
    if (!event.target.matches?.(".product-cover-image")) return;
    const fallback = document.createElement("div"); fallback.className = "product-cover"; fallback.textContent = event.target.alt || "Product preview unavailable";
    if (!event.target.closest("a")) {
      const retry = document.createElement("button"); retry.type = "button"; retry.className = "button button-secondary"; retry.dataset.refreshPage = ""; retry.textContent = "Reload preview"; fallback.append(retry);
    }
    event.target.replaceWith(fallback);
  }, true);
  window.addEventListener("beforeunload", (event) => { if (dirty) { event.preventDefault(); event.returnValue = ""; } });
  window.addEventListener("storage", (event) => {
    if (event.key !== APP.storageKeys.session && event.key !== null) return;
    state.session = readSession(); state.checkout = null; dirty = false;
    navigate(state.session ? window.location.pathname + window.location.search : authUrl(), true, true);
  });
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && !dirty) { state.productsLoaded = false; void render(); }
  });
  window.addEventListener("popstate", async (event) => {
    if (restoredHistory) { const resolve = restoredHistory; restoredHistory = null; resolve(); return; }
    const targetIndex = event.state?.uiIndex ?? historyIndex;
    if (dirty && targetIndex !== historyIndex) {
      const difference = targetIndex - historyIndex;
      await new Promise((resolve) => { restoredHistory = resolve; window.history.go(-difference); });
      const decision = await askDialog({ title: "Discard unsaved changes?", description: "Your unsaved input will be lost. Saved server drafts remain available.", action: "Discard changes", danger: true });
      if (decision) { dirty = false; window.history.go(difference); }
      return;
    }
    historyIndex = targetIndex;
    const params = new URLSearchParams(window.location.search);
    state.query = params.get("q") || "";
    state.category = params.get("category") || "all";
    dirty = false;
    void render();
  });
  return { init: render };
}

if (typeof document !== "undefined" && document.getElementById("app")) createApp().init();
