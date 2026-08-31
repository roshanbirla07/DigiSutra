import { APP, API_PATHS, ROUTES } from "./constants/app.js";
import { createApi, isSellerOrAdmin } from "./services/api.js";
import { readSession, writeSession } from "./services/storage.js";
import { authorizeAndLogDownload, uploadProductAsset } from "./services/assetTransfers.js";
import * as view from "./views/marketplace.js";

export function createApp() {
  const root = document.getElementById("app");
  const state = {
    session: readSession(),
    products: [],
    query: "",
    category: "all",
    checkout: null,
  };
  const api = createApi({
    onUnauthorized: () => {
      state.session = null;
      navigate(ROUTES.auth, true);
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

  function navigate(path, replace = false) {
    if (replace) window.history.replaceState({}, "", path);
    else window.history.pushState({}, "", path);
    render();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function route() {
    const productMatch = window.location.pathname.match(/^\/products\/([^/]+)$/);
    if (productMatch) return { name: "detail", uuid: decodeURIComponent(productMatch[1]) };
    const checkoutMatch = window.location.pathname.match(/^\/checkout\/([^/]+)$/);
    if (checkoutMatch) return { name: "checkout", uuid: decodeURIComponent(checkoutMatch[1]) };
    return { name: window.location.pathname.replace(/\/$/, "") || ROUTES.home };
  }

  async function loadProducts() {
    state.products = await api.request(API_PATHS.products);
  }

  async function render() {
    const current = route();
    if (current.name === ROUTES.auth) {
      root.innerHTML = view.auth({ mode: new URLSearchParams(window.location.search).get("mode") || "login" });
      return;
    }
    if (current.name === ROUTES.home || current.name === ROUTES.catalog) {
      try {
        await loadProducts();
      } catch (error) {
        root.innerHTML = view.catalog({ session: state.session, products: [], query: state.query, category: state.category });
        toast(error.message);
        return;
      }
      const products = state.products.filter((p) => (
        state.category === "all" || p.category === state.category
      ) && (
        !state.query || `${p.title} ${p.description} ${p.category}`.toLowerCase().includes(state.query.toLowerCase())
      ));
      root.innerHTML = current.name === ROUTES.home
        ? view.home({ session: state.session, products })
        : view.catalog({ session: state.session, products, query: state.query, category: state.category });
      return;
    }
    if (current.name === "detail") {
      try {
        root.innerHTML = view.detail({ session: state.session, product: await api.request(API_PATHS.product(current.uuid)) });
      } catch {
        root.innerHTML = view.detail({ session: state.session, product: null });
      }
      return;
    }
    if (!state.session) {
      navigate(ROUTES.auth, true);
      return;
    }
    try {
      if (current.name === "checkout") {
        const product = await api.request(API_PATHS.product(current.uuid));
        const checkout = state.checkout?.productUuid === current.uuid ? state.checkout : null;
        root.innerHTML = view.checkout({ session: state.session, product, checkout });
      } else if (current.name === ROUTES.settings) {
        root.innerHTML = view.settings({ session: state.session });
      } else if (current.name === ROUTES.library) {
        root.innerHTML = view.library({ session: state.session, purchases: await api.request(API_PATHS.purchases) });
      } else if (current.name === ROUTES.becomeSeller && state.session.user_type === APP.roles.customer) {
        const result = await api.request(API_PATHS.sellerApplication);
        root.innerHTML = view.sellerApplication({ session: state.session, application: result?.application || result });
      } else if (current.name === ROUTES.adminSellerApplications && state.session.user_type === APP.roles.admin) {
        root.innerHTML = view.adminSellerApplications({
          session: state.session,
          applications: await api.request(API_PATHS.adminSellerApplications),
        });
      } else if (current.name === ROUTES.seller && isSellerOrAdmin(state.session)) {
        const [summary, products] = await Promise.all([api.request(API_PATHS.dashboard), api.request(API_PATHS.ownedProducts)]);
        root.innerHTML = view.seller({ session: state.session, summary, products });
      } else if (current.name === ROUTES.sellerProducts && isSellerOrAdmin(state.session)) {
        root.innerHTML = view.sellerProducts({ session: state.session, products: await api.request(API_PATHS.ownedProducts) });
      } else if (current.name === ROUTES.sellerProductNew && isSellerOrAdmin(state.session)) {
        root.innerHTML = view.sellerProductNew({ session: state.session });
      } else if (current.name === ROUTES.sellerPayouts && isSellerOrAdmin(state.session)) {
        root.innerHTML = view.sellerPayouts({ session: state.session, summary: await api.request(API_PATHS.payoutSummary) });
      } else {
        root.innerHTML = view.home({ session: state.session, products: state.products });
      }
    } catch (error) {
      root.innerHTML = `<main class="page"><div class="not-found"><h1>Could not load this workspace.</h1><p>${error.message}</p><a class="button button-primary" href="${ROUTES.home}" data-link>Go home</a></div></main>`;
    }
  }

  async function submitAuth(form) {
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
      setSession(session);
      navigate(session.user_type === APP.roles.customer ? ROUTES.settings : ROUTES.seller, true);
    } catch (error) {
      errorNode.textContent = error.message;
    }
  }

  function sellerApplicationPayload(form) {
    const data = Object.fromEntries(new FormData(form).entries());
    data.terms_accepted = form.elements.terms_accepted.checked;
    return data;
  }

  async function submitSellerApplication(form, submit) {
    const errorNode = form.querySelector("[data-form-error]");
    errorNode.textContent = "";
    try {
      const result = await api.request(submit ? API_PATHS.sellerApplicationSubmit : API_PATHS.sellerApplication, {
        method: "POST",
        body: JSON.stringify(sellerApplicationPayload(form)),
      });
      root.innerHTML = view.sellerApplication({ session: state.session, application: result });
      toast(submit ? "Seller application submitted" : "Seller application saved");
    } catch (error) {
      errorNode.textContent = error.message;
    }
  }

  async function reviewSellerApplication(uuid, action) {
    const needsNote = action === "reject" || action === "request-information" || action === "fail-kyc";
    const note = window.prompt(
      action === "approve"
        ? "Optional seller approval note:"
        : action === "verify-kyc"
          ? "Optional KYC verification note:"
          : action === "start-kyc-review"
            ? "Optional KYC review note:"
            : action === "fail-kyc"
              ? "Reason KYC failed:"
              : action === "reject"
          ? "Reason for rejection:"
          : "What information is needed:"
    ) || "";
    if (needsNote && !note.trim()) return;
    const body = { note };
    if (action === "verify-kyc") {
      body.provider = "manual";
      body.provider_account_status = "activated";
      body.fund_account_status = "validated";
    }
    if (action === "fail-kyc") {
      body.provider_account_status = "needs_clarification";
      body.fund_account_status = "failed";
    }
    try {
      await api.request(API_PATHS.adminSellerApplicationAction(uuid, action), {
        method: "POST",
        body: JSON.stringify(body),
      });
      toast(action === "approve" ? "Seller approved" : "Seller request updated");
      const applications = await api.request(API_PATHS.adminSellerApplications);
      root.innerHTML = view.adminSellerApplications({ session: state.session, applications });
    } catch (error) {
      toast(error.message);
    }
  }

  async function startCheckout(productUuid) {
    const errorNode = root.querySelector("[data-checkout-error]");
    if (errorNode) errorNode.textContent = "";
    try {
      const product = await api.request(API_PATHS.product(productUuid));
      const order = await api.request(API_PATHS.ledgerOrders, {
        method: "POST",
        body: JSON.stringify({ product_uuid: product.uuid }),
      });
      const provider = await api.request(API_PATHS.paymentOrders, {
        method: "POST",
        body: JSON.stringify({ order_uuid: order.uuid }),
      });
      state.checkout = { productUuid, product, order: provider, provider: provider.razorpay_order || null };
      root.innerHTML = view.checkout({ session: state.session, product, checkout: state.checkout });
      await openRazorpay();
    } catch (error) {
      if (errorNode) errorNode.textContent = error.message;
      else toast(error.message);
    }
  }

  function loadRazorpayScript() {
    if (window.Razorpay) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      script.onload = resolve;
      script.onerror = () => reject(new Error("Unable to load Razorpay Checkout"));
      document.head.append(script);
    });
  }

  async function openRazorpay() {
    const checkout = state.checkout;
    const errorNode = root.querySelector("[data-checkout-error]");
    if (!checkout?.order?.razorpay_key_id || !checkout?.order?.provider_order_id) {
      if (errorNode) errorNode.textContent = "Payment order is not ready yet.";
      return;
    }
    try {
      await loadRazorpayScript();
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
        handler: async (response) => {
          try {
            await api.request(API_PATHS.paymentConfirm, { method: "POST", body: JSON.stringify(response) });
            toast("Payment confirmed");
            state.checkout = null;
            navigate(ROUTES.library, true);
          } catch (error) {
            if (errorNode) errorNode.textContent = error.message;
          }
        },
      });
      instance.open();
    } catch (error) {
      if (errorNode) errorNode.textContent = error.message;
    }
  }

  root.addEventListener("click", async (event) => {
    const link = event.target.closest("[data-link]");
    if (link) {
      event.preventDefault();
      navigate(link.getAttribute("href"));
      return;
    }
    const tab = event.target.closest("[data-auth-mode]");
    if (tab) {
      navigate(`${ROUTES.auth}?mode=${tab.dataset.authMode}`);
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
        navigate(`${ROUTES.auth}?mode=login`);
        return;
      }
      navigate(ROUTES.checkout(buy.dataset.buyProduct));
      return;
    }
    if (event.target.closest("[data-start-checkout]")) {
      await startCheckout(event.target.closest("[data-start-checkout]").dataset.startCheckout);
      return;
    }
    if (event.target.closest("[data-open-razorpay]")) {
      await openRazorpay();
      return;
    }
    const adminAction = event.target.closest("[data-admin-seller-action]");
    if (adminAction) {
      await reviewSellerApplication(adminAction.dataset.applicationUuid, adminAction.dataset.adminSellerAction);
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
        window.location.assign(downloadUrl);
      } catch (error) {
        button.disabled = false;
        toast(error.message);
      }
      return;
    }
    if (event.target.closest("[data-refresh-admin-sellers]")) {
      const applications = await api.request(API_PATHS.adminSellerApplications);
      root.innerHTML = view.adminSellerApplications({ session: state.session, applications });
    }
  });

  root.addEventListener("submit", async (event) => {
    if (event.target.matches("[data-auth-form]")) {
      event.preventDefault();
      await submitAuth(event.target);
    }
    if (event.target.matches("[data-catalog-form]")) {
      event.preventDefault();
      const data = new FormData(event.target);
      state.query = String(data.get("q") || "").trim();
      state.category = String(data.get("category") || "all");
      await render();
    }
  });

  root.addEventListener("submit", async (event) => {
    if (!event.target.matches("[data-product-form]")) return;
    event.preventDefault();
    const form = event.target;
    const errorNode = form.querySelector("[data-form-error]");
    errorNode.textContent = "";
    const formData = new FormData(form);
    const file = formData.get("asset_file");
    formData.delete("asset_file");
    const data = Object.fromEntries(formData.entries());
    try {
      const product = await api.request(API_PATHS.products, { method: "POST", body: JSON.stringify(data) });
      await uploadProductAsset({ api, productUuid: product.uuid, file });
      toast("Product created and file verified");
      navigate(ROUTES.sellerProducts, true);
    } catch (error) {
      errorNode.textContent = error.message;
    }
  });

  root.addEventListener("submit", async (event) => {
    if (!event.target.matches("[data-seller-application-form]")) return;
    event.preventDefault();
    await submitSellerApplication(event.target, event.submitter?.dataset.sellerApplicationAction === "submit");
  });

  window.addEventListener("popstate", render);
  return { init: render };
}

createApp().init();
