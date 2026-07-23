import { createAuthController } from "./controllers/authController.js";
import { createDashboardController } from "./controllers/dashboardController.js";
import { createProductController } from "./controllers/productController.js";
import { createSettingsController } from "./controllers/settingsController.js";
import { getRoutes, resolveRoute } from "./routes/index.js";

export function createApp() {
  let authController;
  let dashboardController;
  let productController;
  let settingsController;

  const state = {
    apiBaseUrl: localStorage.getItem("digisutra_api_base_url") || "http://localhost:5000",
    session: JSON.parse(localStorage.getItem("digisutra_session") || "null"),
    activeAuthTab: "login",
    profileOpen: false,
    products: [],
    content: null,
  };

  const $ = (id) => document.getElementById(id);

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function toast(message) {
    const host = $("toastHost");
    const node = document.createElement("div");
    node.className = "toast";
    node.textContent = message;
    host.appendChild(node);
    requestAnimationFrame(() => node.classList.add("show"));
    setTimeout(() => {
      node.classList.remove("show");
      setTimeout(() => node.remove(), 220);
    }, 2200);
  }

  function setError(id, message = "") {
    $(id).textContent = message;
  }

  function clearErrors(...ids) {
    ids.forEach((id) => setError(id, ""));
  }

  function formatPrice(currency, price) {
    const value = typeof price === "string" ? price : Number(price).toFixed(2);
    return `${currency || "INR"} ${value}`;
  }

  function formatDate(value) {
    if (!value) return "-";
    const date = new Date(value);
    return Number.isNaN(date.getTime())
      ? "-"
      : new Intl.DateTimeFormat("en-IN", {
          year: "numeric",
          month: "short",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        }).format(date);
  }

  function initialForName(name) {
    return (name || "U").trim().charAt(0).toUpperCase() || "U";
  }

  function api(path, options = {}) {
    return fetch(`${state.apiBaseUrl}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    }).then(async (response) => {
      const text = await response.text();
      let data = {};
      try {
        data = text ? JSON.parse(text) : {};
      } catch {
        data = { raw: text };
      }
      if (!response.ok) {
        throw new Error(data?.error || response.statusText || "Request failed");
      }
      return data;
    });
  }

  function loadContent() {
    return fetch("./content.json").then(async (response) => {
      if (!response.ok) {
        throw new Error("Unable to load dashboard content");
      }
      state.content = await response.json();
    });
  }

  function applyContent() {
    const content = state.content;
    if (!content) return;

    $("brandName").textContent = content.brand.name;
    $("authTitle").textContent = content.brand.authTitle;
    $("authLede").textContent = content.brand.authLede;
    $("authFootnote").textContent = content.brand.footnote;
    $("sidebarBrand").textContent = content.brand.name;
    $("sidebarTagline").textContent = content.brand.tagline;
    $("dashboardLabel").textContent = content.navigation.home;
    $("navAddProduct").textContent = content.navigation.addProduct;
    $("navProductList").textContent = content.navigation.productList;
    $("navSettings").textContent = content.navigation.settings;
    $("homeTitle").textContent = content.home.title;
    $("homeLede").textContent = content.home.lede;
    $("pageTitle").textContent = content.home.title;
    $("profileMenuEmail").textContent = content.placeholders.emptyEmail;

    const [card0, card1, card2] = content.home.cards;
    $("homeCardTitle0").textContent = card0.title;
    $("homeCardBody0").textContent = card0.body;
    $("homeCardTitle1").textContent = card1.title;
    $("homeCardItems1").innerHTML = (card1.items || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
    $("homeCardTitle2").textContent = card2.title;
    $("homeCardItems2").innerHTML = (card2.items || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  }

  function showScreen(screen) {
    $("authScreen").classList.toggle("hidden", screen !== "auth");
    $("dashboardScreen").classList.toggle("hidden", screen !== "dashboard");
  }

  function setActiveView(viewId) {
    document.querySelectorAll(".view").forEach((view) => {
      view.classList.toggle("active", view.id === viewId);
    });
    document.querySelectorAll(".nav-item").forEach((button) => {
      button.classList.toggle("active", button.dataset.view === viewId);
    });
  }

  function navigate(path) {
    const target = path || "/dashboard";
    if (window.location.pathname !== target) {
      window.history.pushState({}, "", target);
    }
    handleRoute();
  }

  function handleRoute() {
    const routes = getRoutes({ authController, dashboardController, productController, settingsController });
    let route = resolveRoute(window.location.pathname || "/auth", routes);
    if (!route) return;

    if (!state.session && route.path !== "/auth") {
      window.history.replaceState({}, "", "/auth");
      route = resolveRoute("/auth", routes);
    } else if (state.session && route.path === "/auth") {
      window.history.replaceState({}, "", "/dashboard");
      route = resolveRoute("/dashboard", routes);
    }

    showScreen(route.screen);
    if (route.view) setActiveView(route.view);
    if (route.title) $("pageTitle").textContent = route.title;
    route.enter?.();
  }

  function setSession(session) {
    state.session = session;
    if (session) {
      localStorage.setItem("digisutra_session", JSON.stringify(session));
    } else {
      localStorage.removeItem("digisutra_session");
    }

    const name = session?.first_name || session?.username || "Guest";
    const role = session?.user_type || "No session";
    const email = session?.email || state.content?.placeholders?.emptyEmail || "-";
    const avatar = initialForName(name);

    $("profileAvatar").textContent = avatar;
    $("profileName").textContent = name;
    $("profileRole").textContent = role;
    $("profileMenuName").textContent = name;
    $("profileMenuEmail").textContent = email;
    $("ownerName").textContent = name;
    $("ownerSeal").textContent = avatar;
  }

  function openProfileMenu() {
    state.profileOpen = true;
    $("profileMenu").classList.remove("hidden");
    $("profileButton").setAttribute("aria-expanded", "true");
  }

  function closeProfileMenu() {
    state.profileOpen = false;
    $("profileMenu").classList.add("hidden");
    $("profileButton").setAttribute("aria-expanded", "false");
  }

  function toggleProfileMenu() {
    state.profileOpen ? closeProfileMenu() : openProfileMenu();
  }

  function renderProducts() {
    const list = $("productsList");
    const empty = $("productsEmpty");
    if (!state.products.length) {
      list.innerHTML = "";
      empty.classList.remove("hidden");
      return;
    }

    empty.classList.add("hidden");
    list.innerHTML = state.products
      .map((product, index) => {
        const description = product.description ? product.description : "No description provided.";
        const truncated = description.length > 110 ? `${description.slice(0, 110).trim()}...` : description;
        return `
          <article class="product-row" data-uuid="${escapeHtml(product.uuid)}">
            <div class="row-index">${index + 1}</div>
            <div class="row-main">
              <div class="row-title">${escapeHtml(product.title)}</div>
              <div class="row-description">${escapeHtml(truncated)}</div>
            </div>
            <div class="row-meta">
              <span>${escapeHtml(product.category || "-")}</span>
              <span class="status-stamp ${product.is_active ? "sage" : "muted"}">${product.is_active ? "Active" : "Draft"}</span>
              <span class="status-stamp ${product.is_public ? "sage" : "muted"}">${product.is_public ? "Public" : "Private"}</span>
            </div>
            <div class="row-price">${escapeHtml(formatPrice(product.currency, product.price))}</div>
            <div class="row-owner">${escapeHtml(product.owner_username || "-")}</div>
            <div class="row-date">${escapeHtml(formatDate(product.created_on))}</div>
            <div class="row-actions">
              <button class="btn danger ghost delete-product" data-uuid="${escapeHtml(product.uuid)}" type="button">Delete</button>
            </div>
          </article>
        `;
      })
      .join("");
  }

  async function loadProducts() {
    state.products = await api("/v1/products/");
    renderProducts();
  }

  return {
    state,
    $,
    api,
    toast,
    setError,
    clearErrors,
    escapeHtml,
    formatPrice,
    formatDate,
    initialForName,
    loadContent,
    applyContent,
    showScreen,
    setActiveView,
    navigate,
    setSession,
    openProfileMenu,
    closeProfileMenu,
    toggleProfileMenu,
    renderProducts,
    loadProducts,
    bind() {
      authController = createAuthController(this);
      dashboardController = createDashboardController(this);
      productController = createProductController(this);
      settingsController = createSettingsController(this);

      authController.bind();
      dashboardController.bind();
      productController.bind();
      settingsController.bind();
      window.addEventListener("popstate", handleRoute);
      setSession(state.session);
      if (window.location.pathname === "/") {
        window.history.replaceState({}, "", state.session ? "/dashboard" : "/auth");
      }
      handleRoute();
    },
    async init() {
      await loadContent();
      applyContent();
      this.bind();
    },
  };
}
