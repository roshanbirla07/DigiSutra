import assert from "node:assert/strict";
import test from "node:test";

globalThis.window = {
  location: { hostname: "localhost", protocol: "http:" }, setTimeout, clearTimeout,
};
globalThis.localStorage = { getItem: () => null };
const { createApi, ApiError } = await import("../src/services/api.js");

function withBrowserMocks(status, fn) {
  const oldWindow = globalThis.window;
  const oldStorage = globalThis.localStorage;
  const oldFetch = globalThis.fetch;
  let stored = JSON.stringify({ token: "test-token" });
  globalThis.window = { setTimeout, clearTimeout };
  globalThis.localStorage = {
    getItem: () => stored,
    setItem: (_key, value) => { stored = value; },
    removeItem: () => { stored = null; },
  };
  globalThis.fetch = async () => ({ ok: false, status, statusText: "Denied", text: async () => '{"error":"Denied"}' });
  return fn(() => stored).finally(() => {
    globalThis.window = oldWindow;
    globalThis.localStorage = oldStorage;
    globalThis.fetch = oldFetch;
  });
}

test("403 preserves session while 401 invalidates it", async () => {
  for (const status of [403, 401]) {
    await withBrowserMocks(status, async (stored) => {
      let unauthorized = 0;
      const api = createApi({ onUnauthorized: () => { unauthorized++; } });
      await assert.rejects(api.request("/protected"), (error) => error instanceof ApiError && error.status === status);
      assert.equal(unauthorized, status === 401 ? 1 : 0);
      assert.equal(Boolean(stored()), status === 403);
    });
  }
});
