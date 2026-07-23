export function createAuthController(app) {
  function switchAuthTab(tab) {
    app.state.activeAuthTab = tab;
    document.querySelectorAll(".segmented-btn").forEach((button) => {
      button.classList.toggle("active", button.dataset.authTab === tab);
    });
    app.$("loginForm").classList.toggle("active", tab === "login");
    app.$("signupForm").classList.toggle("active", tab === "signup");
  }

  function validateLogin() {
    app.clearErrors("loginUsernameError", "loginPasswordError");
    const username = app.$("loginUsername").value.trim();
    const password = app.$("loginPassword").value;
    let valid = true;
    if (!username) {
      app.setError("loginUsernameError", "Username is required.");
      valid = false;
    }
    if (!password) {
      app.setError("loginPasswordError", "Password is required.");
      valid = false;
    }
    return valid;
  }

  function validateSignup() {
    app.clearErrors("signupUsernameError", "signupFirstNameError", "signupEmailError", "signupPasswordError");
    const username = app.$("signupUsername").value.trim();
    const firstName = app.$("signupFirstName").value.trim();
    const email = app.$("signupEmail").value.trim();
    const password = app.$("signupPassword").value;
    let valid = true;
    if (!username) {
      app.setError("signupUsernameError", "Username is required.");
      valid = false;
    }
    if (!firstName) {
      app.setError("signupFirstNameError", "First name is required.");
      valid = false;
    }
    if (!email) {
      app.setError("signupEmailError", "Email is required.");
      valid = false;
    }
    if (!password) {
      app.setError("signupPasswordError", "Password is required.");
      valid = false;
    }
    return valid;
  }

  function bind() {
    document.querySelectorAll(".segmented-btn").forEach((button) => {
      button.addEventListener("click", () => switchAuthTab(button.dataset.authTab));
    });

    app.$("loginForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!validateLogin()) return;
      try {
        const data = await app.api("/v1/users/login/", {
          method: "POST",
          body: JSON.stringify({
            username: app.$("loginUsername").value.trim(),
            password: app.$("loginPassword").value,
          }),
        });
        app.setSession(data);
        app.showScreen("dashboard");
        app.navigate("/dashboard");
        await app.loadProducts().catch(() => {});
        app.toast("Logged in");
      } catch (error) {
        app.setError("loginPasswordError", error.message);
      }
    });

    app.$("signupForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!validateSignup()) return;
      try {
        await app.api("/v1/users/", {
          method: "POST",
          body: JSON.stringify({
            username: app.$("signupUsername").value.trim(),
            firstname: app.$("signupFirstName").value.trim(),
            lastname: app.$("signupLastName").value.trim(),
            email: app.$("signupEmail").value.trim(),
            password: app.$("signupPassword").value,
            user_type: app.$("signupUserType").value,
          }),
        });
        const session = await app.api("/v1/users/login/", {
          method: "POST",
          body: JSON.stringify({
            username: app.$("signupUsername").value.trim(),
            password: app.$("signupPassword").value,
          }),
        });
        app.setSession(session);
        app.showScreen("dashboard");
        app.navigate("/dashboard");
        await app.loadProducts().catch(() => {});
        app.toast("Account created");
      } catch (error) {
        app.toast(error.message);
      }
    });
  }

  function enterAuth() {
    app.showScreen("auth");
    switchAuthTab(app.state.activeAuthTab);
  }

  return { bind, enterAuth };
}
