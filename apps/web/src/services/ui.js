import { escapeHtml } from "../views/helpers.js";

const pending = new WeakSet();
export async function runOnce(element, operation) {
  if (pending.has(element)) return;
  pending.add(element);
  const controls = element.matches("button") ? [element] : [...element.querySelectorAll("button")];
  const previous = controls.map((control) => control.disabled);
  controls.forEach((control) => { control.disabled = true; });
  element.setAttribute("aria-busy", "true");
  try { return await operation(); }
  finally {
    pending.delete(element);
    element.removeAttribute("aria-busy");
    controls.forEach((control, index) => { control.disabled = previous[index]; });
  }
}

export function formError(form, message) {
  const output = form.querySelector("[data-form-error]");
  if (!output) return;
  output.textContent = message;
  output.setAttribute("role", "alert");
  output.tabIndex = -1;
  if (message) output.focus();
}

export function validateForm(form) {
  let first;
  for (const field of form.querySelectorAll("input, textarea, select")) {
    if (field.disabled || !field.willValidate) continue;
    field.parentElement.querySelector("[data-field-error]")?.remove();
    field.removeAttribute("aria-invalid");
    field.removeAttribute("aria-describedby");
    if (field.validity.valid) continue;
    const error = document.createElement("span");
    error.id = `${form.dataset.mode || "form"}-${field.name}-error`;
    error.className = "form-error";
    error.dataset.fieldError = "";
    error.textContent = field.validity.valueMissing ? "Complete this field." : "Check the format of this value.";
    field.setAttribute("aria-invalid", "true");
    field.setAttribute("aria-describedby", error.id);
    field.parentElement.append(error);
    first ||= field;
  }
  first?.focus();
  return !first;
}

// Native dialog provides modal focus containment and inert background.
export function askDialog({ title, description, details = "", action = "Continue", note = false, required = false, danger = false, onConfirm }) {
  return new Promise((resolve) => {
    const previous = document.activeElement;
    const dialog = document.createElement("dialog");
    dialog.className = "review-dialog";
    dialog.setAttribute("aria-labelledby", "review-title");
    dialog.setAttribute("aria-describedby", "review-description");
    dialog.innerHTML = `<form method="dialog" novalidate><h2 id="review-title">${escapeHtml(title)}</h2><p id="review-description">${escapeHtml(description)}</p>${details}${note ? `<label>Review note${required ? " (required)" : " (optional)"}<textarea class="resize-none" name="note" rows="3" ${required ? "required" : ""}></textarea></label>` : ""}<p class="form-error" data-form-error role="alert"></p><div class="form-actions"><button class="button button-secondary" type="button" data-dialog-cancel autofocus>Cancel</button><button class="button ${danger ? "button-danger" : "button-primary"}" type="submit">${escapeHtml(action)}</button></div></form>`;
    const finish = (result) => {
      dialog.close(); dialog.remove();
      if (previous?.isConnected) previous.focus();
      resolve(result);
    };
    dialog.querySelector("[data-dialog-cancel]").addEventListener("click", () => finish(null));
    dialog.addEventListener("cancel", (event) => {
      event.preventDefault();
      if (dialog.querySelector("form").getAttribute("aria-busy") !== "true") finish(null);
    });
    dialog.querySelector("form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const value = dialog.querySelector("textarea")?.value.trim() || "";
      if (required && !value) { formError(dialog, "Enter a review note."); return; }
      await runOnce(event.currentTarget, async () => {
        try {
          if (onConfirm) await onConfirm({ note: value });
          finish({ note: value });
        } catch (error) { formError(dialog, error.message); }
      });
    });
    document.body.append(dialog);
    dialog.showModal();
  });
}

export function safeReturnPath(value, origin) {
  if (!value || !value.startsWith("/") || value.startsWith("//")) return null;
  try {
    const url = new URL(value, origin);
    return url.origin === origin && !url.pathname.startsWith("/auth") ? `${url.pathname}${url.search}` : null;
  } catch { return null; }
}
