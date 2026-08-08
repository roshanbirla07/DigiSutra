import { APP } from "../constants/app.js";

export function createSettingsController(app) {
  function bind() {
    app.$("apiBaseUrl").value = app.state.apiBaseUrl;
    app.$("settingsForm").addEventListener("submit", (event) => {
      event.preventDefault();
      app.clearErrors("apiBaseUrlError");
      const value = app.$("apiBaseUrl").value.trim();
      if (!value) {
        app.setError("apiBaseUrlError", "API base URL is required.");
        return;
      }
      app.state.apiBaseUrl = value;
      localStorage.setItem(APP.storageKeys.apiBaseUrl, value);
      app.toast("Settings saved");
    });
  }

  function enterSettings() {
    app.showScreen("dashboard");
    app.setActiveView("settingsView");
    app.$("pageTitle").textContent = "Settings";
  }

  return { bind, enterSettings };
}
