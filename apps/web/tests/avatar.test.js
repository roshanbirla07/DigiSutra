import assert from "node:assert/strict";
import test from "node:test";
import { JSDOM } from "jsdom";
import { renderAvatar } from "../src/views/avatar.js";
import { home, settings, detail } from "../src/views/marketplace.js";

test("default portraits stay consistent across account and public creator contexts", () => {
  const user = { username: "maya", uuid: "user::1", first_name: "Maya", user_type: "customer" };
  const product = { uuid: "product::1", title: "Toolkit", owner_username: "maya" };
  const document = new JSDOM(settings({ session: user })).window.document;
  const headerPortrait = document.querySelector(".avatar svg").outerHTML;
  assert.equal(document.querySelector(".profile-avatar svg").outerHTML, headerPortrait);
  for (const html of [home({ session: user, products: [product] }), detail({ session: user, product })]) {
    const view = new JSDOM(html).window.document;
    assert.equal(view.querySelector(".creator-avatar svg").outerHTML, headerPortrait);
  }
  assert.equal(renderAvatar(user), renderAvatar({ ...user, first_name: "Renamed", email: "new@example.com" }));
  assert.notEqual(renderAvatar(user), renderAvatar({ username: "another-creator" }));
});

test("portraits are decorative local SVGs and never expose identity or executable input", () => {
  const html = renderAvatar({ username: '<img src=x onerror=alert(1)>', email: "private@example.com", token: "secret-token" }, '"><script>alert(1)</script>');
  const document = new JSDOM(html).window.document;
  assert.equal(document.querySelector("svg").getAttribute("aria-hidden"), "true");
  assert.equal(document.querySelector("svg").getAttribute("focusable"), "false");
  assert.equal(document.querySelectorAll("img, image, script, foreignObject, [onerror], [href]").length, 0);
  assert.doesNotMatch(html, /private@example|secret-token|onerror|alert\(/);
  assert.doesNotMatch(renderAvatar({ username: "maya" }), /maya/);
  assert.equal(document.querySelectorAll(".avatar").length, 1);
});

test("missing identities render a stable default and anonymous navigation stays anonymous", () => {
  assert.equal(renderAvatar(), renderAvatar({}));
  assert.notEqual(renderAvatar({ uuid: "user::1" }), renderAvatar({ uuid: "user::2" }));
  const document = new JSDOM(home({ session: null, products: [] })).window.document;
  assert.equal(document.querySelector(".avatar-link"), null);
  assert.ok([...document.querySelectorAll("a")].some((link) => link.textContent === "Sign in"));
});
