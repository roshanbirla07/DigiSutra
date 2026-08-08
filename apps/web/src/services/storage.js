import { APP } from "../constants/app.js";

export function readSession() {
  try { return JSON.parse(localStorage.getItem(APP.storageKeys.session) || "null"); } catch { return null; }
}

export function writeSession(session) {
  if (session) localStorage.setItem(APP.storageKeys.session, JSON.stringify(session));
  else localStorage.removeItem(APP.storageKeys.session);
}
