import { APP } from "../constants/app.js";

let memorySession = null;
let memoryOnly = false;
export function readPreference(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}
export function readSession() {
  if (memoryOnly) return memorySession;
  try { return JSON.parse(localStorage.getItem(APP.storageKeys.session) || "null"); }
  catch { return memorySession; }
}
export function writeSession(session) {
  memorySession = session;
  try {
    if (session) localStorage.setItem(APP.storageKeys.session, JSON.stringify(session));
    else localStorage.removeItem(APP.storageKeys.session);
    memoryOnly = false;
  } catch { memoryOnly = true; /* This tab keeps its session in memory only. */ }
}
