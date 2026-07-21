const state = {
  apiBaseUrl: localStorage.getItem("digisutra_api_base_url") || "http://localhost:5000",
  session: JSON.parse(localStorage.getItem("digisutra_session") || "null"),
  activeAuthTab: "login",
  activeView: "homeView",
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

function setError(id, message = "") {
  $(id).textContent = message;
}

function clearErrors(...ids) {
  ids.forEach((id) => setError(id, ""));
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

function formatPrice(currency, price) {
  const value = typeof price === "string" ? price : Number(price).toFixed(2);
  return `${currency || "INR"} ${value}`;
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "—"
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

async function loadContent() {
  const response = await fetch("./content.json");
  if (!response.ok) {
    throw new Error("Unable to load dashboard content");
  }
  state.content = await response.json();
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

function showScreen(screen) {
  $("authScreen").classList.toggle("hidden", screen !== "auth");
  $("dashboardScreen").classList.toggle("hidden", screen !== "dashboard");
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
  const email = session?.email || state.content?.placeholders?.emptyEmail || "—";
  const avatar = initialForName(name);

  $("profileAvatar").textContent = avatar;
  $("profileName").textContent = name;
  $("profileRole").textContent = role;
  $("profileMenuName").textContent = name;
  $("profileMenuEmail").textContent = email;
  $("ownerName").textContent = name;
  $("ownerSeal").textContent = avatar;
}

function switchAuthTab(tab) {
  state.activeAuthTab = tab;
  document.querySelectorAll(".segmented-btn").forEach((button) => {
    button.classList.toggle("active", button.dataset.authTab === tab);
  });
  $("loginForm").classList.toggle("active", tab === "login");
  $("signupForm").classList.toggle("active", tab === "signup");
}

function setActiveView(viewId) {
  state.activeView = viewId;
  document.querySelectorAll(".view").forEach((view) => {
    view.classList.toggle("active", view.id === viewId);
  });
  document.querySelectorAll(".nav-item").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === viewId);
  });

  const titles = {
    homeView: state.content?.home?.title || "Home",
    addProductView: "Add Product",
    productsView: "Product List",
    settingsView: "Settings",
  };
  $("pageTitle").textContent = titles[viewId] || "DigiSutra";
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
      const truncated = description.length > 110 ? `${description.slice(0, 110).trim()}…` : description;
      return `
        <article class="product-row" data-uuid="${escapeHtml(product.uuid)}">
          <div class="row-index">${index + 1}</div>
          <div class="row-main">
            <div class="row-title">${escapeHtml(product.title)}</div>
            <div class="row-description">${escapeHtml(truncated)}</div>
          </div>
          <div class="row-meta">
            <span>${escapeHtml(product.category || "—")}</span>
            <span class="status-stamp ${product.is_active ? "sage" : "muted"}">${product.is_active ? "Active" : "Draft"}</span>
            <span class="status-stamp ${product.is_public ? "sage" : "muted"}">${product.is_public ? "Public" : "Private"}</span>
          </div>
          <div class="row-price">${escapeHtml(formatPrice(product.currency, product.price))}</div>
          <div class="row-owner">${escapeHtml(product.owner_username || "—")}</div>
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

function validateLogin() {
  clearErrors("loginUsernameError", "loginPasswordError");
  const username = $("loginUsername").value.trim();
  const password = $("loginPassword").value;
  let valid = true;
  if (!username) {
    setError("loginUsernameError", "Username is required.");
    valid = false;
  }
  if (!password) {
    setError("loginPasswordError", "Password is required.");
    valid = false;
  }
  return valid;
}

function validateSignup() {
  clearErrors(
    "signupUsernameError",
    "signupFirstNameError",
    "signupEmailError",
    "signupPasswordError"
  );
  const username = $("signupUsername").value.trim();
  const firstName = $("signupFirstName").value.trim();
  const email = $("signupEmail").value.trim();
  const password = $("signupPassword").value;
  let valid = true;
  if (!username) {
    setError("signupUsernameError", "Username is required.");
    valid = false;
  }
  if (!firstName) {
    setError("signupFirstNameError", "First name is required.");
    valid = false;
  }
  if (!email) {
    setError("signupEmailError", "Email is required.");
    valid = false;
  }
  if (!password) {
    setError("signupPasswordError", "Password is required.");
    valid = false;
  }
  return valid;
}

function validateProduct() {
  clearErrors("productTitleError");
  const title = $("productTitle").value.trim();
  if (!title) {
    setError("productTitleError", "Title is required.");
    return false;
  }
  return true;
}

function bindAuthTabs() {
  document.querySelectorAll(".segmented-btn").forEach((button) => {
    button.addEventListener("click", () => switchAuthTab(button.dataset.authTab));
  });
}

function bindNavigation() {
  document.querySelectorAll(".nav-item").forEach((button) => {
    button.addEventListener("click", () => setActiveView(button.dataset.view));
  });
}

function bindProfileMenu() {
  $("profileButton").addEventListener("click", toggleProfileMenu);
  $("logoutAction").addEventListener("click", () => {
    setSession(null);
    closeProfileMenu();
    showScreen("auth");
    switchAuthTab("login");
    toast("Logged out");
  });
  $("accountSettingsAction").addEventListener("click", () => {
    setActiveView("settingsView");
    closeProfileMenu();
  });
  document.addEventListener("click", (event) => {
    if (!event.target.closest(".profile-wrap")) closeProfileMenu();
  });
}

function bindLogin() {
  $("loginForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!validateLogin()) return;

    try {
      const data = await api("/v1/users/login/", {
        method: "POST",
        body: JSON.stringify({
          username: $("loginUsername").value.trim(),
          password: $("loginPassword").value,
        }),
      });
      setSession(data);
      showScreen("dashboard");
      setActiveView("homeView");
      await loadProducts().catch(() => {});
      toast("Logged in");
    } catch (error) {
      setError("loginPasswordError", error.message);
    }
  });
}

function bindSignup() {
  $("signupForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!validateSignup()) return;

    try {
      await api("/v1/users/", {
        method: "POST",
        body: JSON.stringify({
          username: $("signupUsername").value.trim(),
          firstname: $("signupFirstName").value.trim(),
          lastname: $("signupLastName").value.trim(),
          email: $("signupEmail").value.trim(),
          password: $("signupPassword").value,
          user_type: $("signupUserType").value,
        }),
      });
      const session = await api("/v1/users/login/", {
        method: "POST",
        body: JSON.stringify({
          username: $("signupUsername").value.trim(),
          password: $("signupPassword").value,
        }),
      });
      setSession(session);
      showScreen("dashboard");
      setActiveView("homeView");
      await loadProducts().catch(() => {});
      toast("Account created");
    } catch (error) {
      toast(error.message);
    }
  });
}

function bindSettings() {
  $("apiBaseUrl").value = state.apiBaseUrl;
  $("settingsForm").addEventListener("submit", (event) => {
    event.preventDefault();
    clearErrors("apiBaseUrlError");
    const value = $("apiBaseUrl").value.trim();
    if (!value) {
      setError("apiBaseUrlError", "API base URL is required.");
      return;
    }
    state.apiBaseUrl = value;
    localStorage.setItem("digisutra_api_base_url", value);
    toast("Settings saved");
  });
}

function bindProductForm() {
  $("createProductAction").addEventListener("click", submitProduct);
  $("productForm").addEventListener("submit", (event) => {
    event.preventDefault();
    submitProduct();
  });
  $("emptyBackToAdd").addEventListener("click", () => setActiveView("addProductView"));
  $("refreshProductsAction").addEventListener("click", () => loadProducts().catch((error) => toast(error.message)));
}

async function submitProduct() {
  if (!validateProduct()) return;
  if (!state.session?.uuid) {
    toast("Sign in first");
    showScreen("auth");
    return;
  }

  try {
    const payload = {
      owner_uuid: state.session.uuid,
      title: $("productTitle").value.trim(),
      description: $("productDescription").value.trim(),
      price: $("productPrice").value.trim(),
      currency: $("productCurrency").value.trim() || "INR",
      category: $("productCategory").value.trim(),
      is_active: $("productActive").checked,
      is_public: $("productPublic").checked,
    };
    await api("/v1/products/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    $("productForm").reset();
    $("productCurrency").value = "INR";
    $("productActive").checked = true;
    $("productPublic").checked = true;
    setError("productTitleError", "");
    toast("Product created");
    await loadProducts();
    setActiveView("productsView");
  } catch (error) {
    toast(error.message);
  }
}

function bindProductDeletes() {
  $("productsList").addEventListener("click", async (event) => {
    const button = event.target.closest(".delete-product");
    if (!button) return;

    const uuid = button.dataset.uuid;
    button.disabled = true;
    try {
      await api(`/v1/products/${uuid}/`, { method: "DELETE" });
      toast("Product deleted");
      await loadProducts();
    } catch (error) {
      toast(error.message);
      button.disabled = false;
    }
  });
}

async function init() {
  await loadContent();
  applyContent();
  bindAuthTabs();
  bindNavigation();
  bindProfileMenu();
  bindLogin();
  bindSignup();
  bindSettings();
  bindProductForm();
  bindProductDeletes();

  setSession(state.session);
  switchAuthTab(state.activeAuthTab);

  if (state.session) {
    showScreen("dashboard");
    setActiveView(state.activeView);
    await loadProducts().catch(() => {});
  } else {
    showScreen("auth");
  }

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeProfileMenu();
  });
}

init();
