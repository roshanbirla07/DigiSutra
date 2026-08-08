export function createSellerApplicationController(app) {
  function payload() {
    return {
      store_name: app.$("sellerStoreName").value.trim(),
      store_description: app.$("sellerStoreDescription").value.trim(),
      category: app.$("sellerCategory").value.trim(),
      product_types: app.$("sellerProductTypes").value.trim(),
      website_url: app.$("sellerWebsiteUrl").value.trim(),
      portfolio_url: app.$("sellerPortfolioUrl").value.trim(),
      legal_name: app.$("sellerLegalName").value.trim(),
      country: app.$("sellerCountry").value.trim(),
      phone_number: app.$("sellerPhoneNumber").value.trim(),
      terms_accepted: app.$("sellerTermsAccepted").checked,
    };
  }

  function setStatus(application) {
    const status = application?.status || "not_started";
    app.state.sellerApplicationUuid = application?.uuid || null;
    app.$("sellerApplicationStatus").textContent = status.replaceAll("_", " ");
    app.$("sellerApplicationMessage").textContent = application?.review_note || "Complete the form to apply to become a seller.";
    const locked = ["submitted", "under_review", "approved", "withdrawn"].includes(status);
    app.$("sellerApplicationForm").classList.toggle("hidden", locked);
    app.$("sellerApplicationSubmit").classList.toggle("hidden", locked);
    app.$("sellerApplicationWithdraw").classList.toggle("hidden", !["submitted", "under_review", "needs_information"].includes(status));
    app.$("sellerApplicationStatusBadge").className = `status-stamp ${status === "approved" ? "sage" : "muted"}`;
  }

  function fill(application) {
    if (!application) {
      setStatus(null);
      return;
    }
    const mapping = {
      sellerStoreName: application.store_name,
      sellerStoreDescription: application.store_description,
      sellerCategory: application.category,
      sellerProductTypes: application.product_types,
      sellerWebsiteUrl: application.website_url,
      sellerPortfolioUrl: application.portfolio_url,
      sellerLegalName: application.legal_name,
      sellerCountry: application.country,
      sellerPhoneNumber: application.phone_number,
    };
    Object.entries(mapping).forEach(([id, value]) => { app.$(id).value = value || ""; });
    app.$("sellerTermsAccepted").checked = Boolean(application.terms_accepted);
    setStatus(application);
  }

  async function load() {
    const result = await app.api("/v1/seller-applications/");
    fill(result?.application || result);
  }

  async function save(submit = false) {
    app.clearErrors("sellerApplicationError");
    const data = payload();
    const required = ["store_name", "store_description", "category", "product_types", "legal_name", "country", "phone_number"];
    if (submit && required.some((field) => !data[field])) {
      app.setError("sellerApplicationError", "Complete all required fields before submitting.");
      return;
    }
    if (submit && !data.terms_accepted) {
      app.setError("sellerApplicationError", "Accept the seller terms before submitting.");
      return;
    }
    const result = await app.api(submit ? "/v1/seller-applications/submit/" : "/v1/seller-applications/", {
      method: submit ? "POST" : "PATCH",
      body: JSON.stringify(data),
    });
    fill(result);
    app.toast(submit ? "Application submitted" : "Draft saved");
  }

  async function withdraw() {
    const result = await app.api(`/v1/seller-applications/${app.state.sellerApplicationUuid}/withdraw/`, { method: "POST", body: JSON.stringify({}) });
    fill(result);
    app.toast("Application withdrawn");
  }

  function bind() {
    app.$("sellerApplicationForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      try { await save(false); } catch (error) { app.setError("sellerApplicationError", error.message); }
    });
    app.$("sellerApplicationSubmit").addEventListener("click", async () => {
      try { await save(true); } catch (error) { app.setError("sellerApplicationError", error.message); }
    });
    app.$("sellerApplicationWithdraw").addEventListener("click", async () => {
      try { await withdraw(); } catch (error) { app.setError("sellerApplicationError", error.message); }
    });
  }

  async function enterSellerApplication() {
    app.showScreen("dashboard");
    app.setActiveView("sellerApplicationView");
    app.$("pageTitle").textContent = "Become a seller";
    try { await load(); } catch (error) { app.setError("sellerApplicationError", error.message); }
  }

  return { bind, enterSellerApplication };
}
