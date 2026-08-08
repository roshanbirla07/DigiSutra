export function createAdminSellerController(app) {
  function render(applications) {
    const list = app.$("adminSellerApplicationsList");
    if (!applications.length) {
      list.innerHTML = '<p class="muted">No seller applications found.</p>';
      return;
    }
    list.innerHTML = applications.map((item) => `
      <article class="product-row admin-application-row">
        <div class="row-main">
          <div class="row-title">${app.escapeHtml(item.store_name || "Unnamed store")}</div>
          <div class="row-description">${app.escapeHtml(item.applicant?.email || item.applicant?.username || "Unknown applicant")}</div>
        </div>
        <div class="row-meta"><span class="status-stamp muted">${app.escapeHtml(item.status.replaceAll("_", " "))}</span></div>
        <div class="row-date">${app.escapeHtml(app.formatDate(item.submitted_on || item.created_on))}</div>
        <div class="row-actions">
          ${["submitted", "under_review", "needs_information"].includes(item.status) ? `
            <button class="btn primary admin-approve" data-uuid="${app.escapeHtml(item.uuid)}" type="button">Approve</button>
            <button class="btn danger ghost admin-reject" data-uuid="${app.escapeHtml(item.uuid)}" type="button">Reject</button>
            <button class="btn secondary admin-request-info" data-uuid="${app.escapeHtml(item.uuid)}" type="button">Request info</button>
          ` : ""}
        </div>
      </article>
    `).join("");
    list.querySelectorAll(".admin-approve").forEach((button) => button.addEventListener("click", () => review(button.dataset.uuid, "approve")));
    list.querySelectorAll(".admin-reject").forEach((button) => button.addEventListener("click", () => review(button.dataset.uuid, "reject")));
    list.querySelectorAll(".admin-request-info").forEach((button) => button.addEventListener("click", () => review(button.dataset.uuid, "request-information")));
  }

  async function load() {
    const applications = await app.api("/v1/admin/seller-applications/");
    render(applications);
  }

  async function review(uuid, action) {
    const note = action === "reject" || action === "request-information" ? window.prompt(action === "reject" ? "Reason for rejection:" : "What information is needed:") : window.prompt("Optional review note:") || "";
    if (["reject", "request-information"].includes(action) && !note) return;
    try {
      await app.api(`/v1/admin/seller-applications/${uuid}/${action}/`, { method: "POST", body: JSON.stringify({ note }) });
      app.toast(action === "approve" ? "Seller approved" : "Application rejected");
      await load();
    } catch (error) {
      app.toast(error.message);
    }
  }

  function bind() {
    app.$("adminSellerRefresh").addEventListener("click", () => load().catch((error) => app.toast(error.message)));
  }

  async function enterAdminSellerApplications() {
    app.showScreen("dashboard");
    app.setActiveView("adminSellerApplicationsView");
    app.$("pageTitle").textContent = "Seller applications";
    try { await load(); } catch (error) { app.toast(error.message); }
  }

  return { bind, enterAdminSellerApplications };
}
