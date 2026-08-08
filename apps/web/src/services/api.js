import { runtimeConfig } from "../config/runtime.js";
import { APP, API_PATHS, ROUTES } from "../constants/app.js";
import { readSession, writeSession } from "./storage.js";

export class ApiError extends Error {
  constructor(message, status, data) { super(message); this.name = "ApiError"; this.status = status; this.data = data; }
}

export function createApi({ onUnauthorized } = {}) {
  async function request(path, options = {}) {
    const session = readSession();
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), runtimeConfig.requestTimeoutMs);
    try {
      const headers = { Accept: "application/json", ...(options.body ? { "Content-Type": "application/json" } : {}), ...(options.headers || {}) };
      if (session?.token) headers.Authorization = `Bearer ${session.token}`;
      const response = await fetch(`${runtimeConfig.apiBaseUrl}${path}`, { ...options, headers, signal: controller.signal });
      const raw = await response.text();
      let data = {};
      try { data = raw ? JSON.parse(raw) : {}; } catch { data = { raw }; }
      if (!response.ok) {
        if ((response.status === 401 || response.status === 403) && path !== API_PATHS.login) {
          writeSession(null); onUnauthorized?.();
        }
        throw new ApiError(data?.error || response.statusText || "Request failed", response.status, data);
      }
      return data;
    } catch (error) {
      if (error.name === "AbortError") throw new ApiError("The request timed out. Check the API connection and try again.", 408);
      throw error;
    } finally { window.clearTimeout(timeout); }
  }
  return { request };
}

export function isSellerOrAdmin(session) {
  return [APP.roles.seller, APP.roles.admin].includes(session?.user_type);
}

export { ROUTES };
