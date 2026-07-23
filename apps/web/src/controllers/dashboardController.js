export function createDashboardController(app) {
  function bindNavigation() {
    document.querySelectorAll(".nav-item").forEach((button) => {
      button.addEventListener("click", () => {
        const routeByView = {
          addProductView: "/product",
          productsView: "/products",
          settingsView: "/settings",
          homeView: "/dashboard",
        };
        app.navigate(routeByView[button.dataset.view] || "/auth");
      });
    });
  }

  function bindProfileMenu() {
      app.$("profileButton").addEventListener("click", app.toggleProfileMenu);
    app.$("logoutAction").addEventListener("click", () => {
      app.setSession(null);
      app.closeProfileMenu();
      app.navigate("/auth");
      app.toast("Logged out");
    });
    app.$("accountSettingsAction").addEventListener("click", () => {
      app.navigate("/settings");
      app.closeProfileMenu();
    });
    document.addEventListener("click", (event) => {
      if (!event.target.closest(".profile-wrap")) app.closeProfileMenu();
    });
  }

  function enterDashboard() {
    app.showScreen("dashboard");
    app.setActiveView("homeView");
    app.$("pageTitle").textContent = "Dashboard";
  }

  function bind() {
    bindNavigation();
    bindProfileMenu();
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") app.closeProfileMenu();
    });
  }

  return { bind, enterDashboard, enterAuth: () => app.showScreen("auth") };
}
