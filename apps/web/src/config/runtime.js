import { APP } from "../constants/app.js";

function browserDefaultApiUrl() {
  const host = window.location.hostname || "localhost";
  return `${window.location.protocol === "https:" ? "https" : "http"}://${host}:5000`;
}

export const runtimeConfig = Object.freeze({
  apiBaseUrl: window.DIGISUTRA_CONFIG?.apiBaseUrl
    || localStorage.getItem(APP.storageKeys.apiBaseUrl)
    || browserDefaultApiUrl(),
  requestTimeoutMs: Number(window.DIGISUTRA_CONFIG?.requestTimeoutMs || 12000),
});
