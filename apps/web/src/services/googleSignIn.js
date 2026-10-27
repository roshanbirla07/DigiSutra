let sdkPromise;

export function loadGoogleSignIn() {
  if (window.google?.accounts?.id) return Promise.resolve(window.google.accounts.id);
  if (!sdkPromise) {
    sdkPromise = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.onload = () => window.google?.accounts?.id ? resolve(window.google.accounts.id) : reject(new Error("Google sign-in is unavailable. Please try password sign-in."));
      script.onerror = () => reject(new Error("Google sign-in is unavailable. Please try password sign-in."));
      document.head.append(script);
    }).catch((error) => { sdkPromise = null; throw error; });
  }
  return sdkPromise;
}
