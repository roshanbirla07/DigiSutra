import { readPreference } from "../services/storage.js";
import { APP } from "../constants/app.js";

function browserDefaultApiUrl() {
  const host = globalThis.window?.location.hostname || "localhost";
  return `${globalThis.window?.location.protocol === "https:" ? "https" : "http"}://${host}:5000`;
}

export const runtimeConfig = Object.freeze({
  apiBaseUrl: globalThis.window?.DIGISUTRA_CONFIG?.apiBaseUrl
    || readPreference(APP.storageKeys.apiBaseUrl)
    || browserDefaultApiUrl(),
  requestTimeoutMs: Number(globalThis.window?.DIGISUTRA_CONFIG?.requestTimeoutMs || 12000),
});
