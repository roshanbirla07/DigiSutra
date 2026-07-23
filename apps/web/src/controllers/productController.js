export function createProductController(app) {
  function validateProduct() {
    app.clearErrors("productTitleError");
    const title = app.$("productTitle").value.trim();
    if (!title) {
      app.setError("productTitleError", "Title is required.");
      return false;
    }
    return true;
  }

  async function submitProduct() {
    if (!validateProduct()) return;
    if (!app.state.session?.uuid) {
      app.toast("Sign in first");
      app.showScreen("auth");
      return;
    }

    try {
      await app.api("/v1/products/", {
        method: "POST",
        body: JSON.stringify({
          owner_uuid: app.state.session.uuid,
          title: app.$("productTitle").value.trim(),
          description: app.$("productDescription").value.trim(),
          price: app.$("productPrice").value.trim(),
          currency: app.$("productCurrency").value.trim() || "INR",
          category: app.$("productCategory").value.trim(),
          is_active: app.$("productActive").checked,
          is_public: app.$("productPublic").checked,
        }),
      });
      app.$("productForm").reset();
      app.$("productCurrency").value = "INR";
      app.$("productActive").checked = true;
      app.$("productPublic").checked = true;
      app.setError("productTitleError", "");
      app.toast("Product created");
      await app.loadProducts();
      app.navigate("/product");
    } catch (error) {
      app.toast(error.message);
    }
  }

  function bind() {
    app.$("createProductAction").addEventListener("click", submitProduct);
    app.$("productForm").addEventListener("submit", (event) => {
      event.preventDefault();
      submitProduct();
    });
    app.$("emptyBackToAdd").addEventListener("click", () => {
      app.navigate("/product");
    });
    app.$("refreshProductsAction").addEventListener("click", () => app.loadProducts().catch((error) => app.toast(error.message)));
    app.$("productsList").addEventListener("click", async (event) => {
      const button = event.target.closest(".delete-product");
      if (!button) return;
      const uuid = button.dataset.uuid;
      button.disabled = true;
      try {
        await app.api(`/v1/products/${uuid}/`, { method: "DELETE" });
        app.toast("Product deleted");
        await app.loadProducts();
      } catch (error) {
        app.toast(error.message);
        button.disabled = false;
      }
    });
  }

  function enterProduct() {
    app.showScreen("dashboard");
    app.setActiveView("addProductView");
    app.$("pageTitle").textContent = "Product";
  }

  function enterProductList() {
    app.showScreen("dashboard");
    app.setActiveView("productsView");
    app.$("pageTitle").textContent = "Product List";
    app.loadProducts().catch(() => {});
  }

  return { bind, enterProduct, enterProductList };
}
