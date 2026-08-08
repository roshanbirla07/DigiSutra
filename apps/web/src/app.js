import { APP, API_PATHS, ROUTES } from "./constants/app.js";
import { createApi, isSellerOrAdmin } from "./services/api.js";
import { readSession, writeSession } from "./services/storage.js";
import * as view from "./views/marketplace.js";

export function createApp() {
  const root = document.getElementById("app");
  const state = { session: readSession(), products: [], query: "", category: "all" };
  const api = createApi({ onUnauthorized: () => { state.session = null; navigate(ROUTES.auth, true); toast("Your session expired. Please sign in again."); } });

  function toast(message) { const host = document.getElementById("toastHost"); const node = document.createElement("div"); node.className = "toast"; node.textContent = message; host.append(node); requestAnimationFrame(() => node.classList.add("show")); window.setTimeout(() => { node.classList.remove("show"); window.setTimeout(() => node.remove(), 200); }, 2600); }
  function setSession(session) { state.session = session; writeSession(session); }
  function navigate(path, replace = false) { if (replace) window.history.replaceState({}, "", path); else window.history.pushState({}, "", path); render(); window.scrollTo({ top: 0, behavior: "smooth" }); }
  function route() { const match = window.location.pathname.match(/^\/products\/([^/]+)$/); if (match) return { name: "detail", uuid: decodeURIComponent(match[1]) }; return { name: window.location.pathname.replace(/\/$/, "") || ROUTES.home }; }
  async function loadProducts() { state.products = await api.request(API_PATHS.products); }
  async function render() {
    const current = route();
    if (current.name === ROUTES.auth) { root.innerHTML = view.auth({ mode: new URLSearchParams(window.location.search).get("mode") || "login" }); return; }
    if (current.name === ROUTES.home || current.name === ROUTES.catalog) {
      try { await loadProducts(); } catch (error) { root.innerHTML = view.catalog({ session: state.session, products: [], query: state.query, category: state.category }); toast(error.message); return; }
      const products = state.products.filter((p) => (state.category === "all" || p.category === state.category) && (!state.query || `${p.title} ${p.description} ${p.category}`.toLowerCase().includes(state.query.toLowerCase())));
      root.innerHTML = current.name === ROUTES.home ? view.home({ session: state.session, products }) : view.catalog({ session: state.session, products, query: state.query, category: state.category }); return;
    }
    if (current.name === "detail") { try { root.innerHTML = view.detail({ session: state.session, product: await api.request(API_PATHS.product(current.uuid)) }); } catch { root.innerHTML = view.detail({ session: state.session, product: null }); } return; }
    if (!state.session) { navigate(ROUTES.auth, true); return; }
    try {
      if (current.name === ROUTES.library) root.innerHTML = view.library({ session: state.session, purchases: await api.request(API_PATHS.purchases) });
      else if (current.name === ROUTES.seller && isSellerOrAdmin(state.session)) { const [summary, products] = await Promise.all([api.request(API_PATHS.dashboard), api.request(API_PATHS.ownedProducts)]); root.innerHTML = view.seller({ session: state.session, summary, products }); }
      else if (current.name === ROUTES.sellerProducts && isSellerOrAdmin(state.session)) root.innerHTML = view.sellerProducts({ session: state.session, products: await api.request(API_PATHS.ownedProducts) });
      else if (current.name === ROUTES.sellerProductNew && isSellerOrAdmin(state.session)) root.innerHTML = view.sellerProductNew({ session: state.session });
      else if (current.name === ROUTES.sellerPayouts && isSellerOrAdmin(state.session)) root.innerHTML = view.sellerPayouts({ session: state.session, summary: await api.request(API_PATHS.payoutSummary) });
      else { root.innerHTML = view.home({ session: state.session, products: state.products }); }
    } catch (error) { root.innerHTML = `<main class="page"><div class="not-found"><h1>Could not load this workspace.</h1><p>${error.message}</p><a class="button button-primary" href="${ROUTES.home}" data-link>Go home</a></div></main>`; }
  }
  async function submitAuth(form) { const mode = form.dataset.mode; const data = Object.fromEntries(new FormData(form).entries()); const errorNode = form.querySelector("[data-form-error]"); errorNode.textContent = ""; try { if (mode === "signup") { await api.request(API_PATHS.signup, { method: "POST", body: JSON.stringify({ ...data, firstname: data.first_name, lastname: data.last_name }) }); } const session = await api.request(API_PATHS.login, { method: "POST", body: JSON.stringify({ username: data.username, password: data.password }) }); setSession(session); navigate(session.user_type === APP.roles.customer ? ROUTES.library : ROUTES.seller, true); } catch (error) { errorNode.textContent = error.message; } }
  root.addEventListener("click", async (event) => { const link = event.target.closest("[data-link]"); if (link) { event.preventDefault(); navigate(link.getAttribute("href")); return; } const tab = event.target.closest("[data-auth-mode]"); if (tab) { navigate(`${ROUTES.auth}?mode=${tab.dataset.authMode}`); return; } const buy = event.target.closest("[data-buy-product]"); if (buy) { if (!state.session) { navigate(`${ROUTES.auth}?mode=login`); return; } toast("Checkout is ready for the payment integration."); } });
  root.addEventListener("submit", async (event) => { if (event.target.matches("[data-auth-form]")) { event.preventDefault(); await submitAuth(event.target); } if (event.target.matches("[data-catalog-form]")) { event.preventDefault(); const data = new FormData(event.target); state.query = String(data.get("q") || "").trim(); state.category = String(data.get("category") || "all"); await render(); } });
  root.addEventListener("submit", async (event) => { if (!event.target.matches("[data-product-form]")) return; event.preventDefault(); const form = event.target; const errorNode = form.querySelector("[data-form-error]"); errorNode.textContent = ""; const data = Object.fromEntries(new FormData(form).entries()); try { await api.request(API_PATHS.products, { method: "POST", body: JSON.stringify(data) }); toast("Product created"); navigate(ROUTES.sellerProducts, true); } catch (error) { errorNode.textContent = error.message; } });
  window.addEventListener("popstate", render);
  return { init: render };
}

createApp().init();
