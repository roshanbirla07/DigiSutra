export const APP = Object.freeze({
  name: "DigiSutra",
  tagline: "A considered marketplace for digital work",
  defaultCurrency: "INR",
  storageKeys: Object.freeze({ session: "digisutra_session", apiBaseUrl: "digisutra_api_base_url" }),
  roles: Object.freeze({ customer: "customer", seller: "seller", admin: "admin" }),
});

export const ROUTES = Object.freeze({
  home: "/",
  catalog: "/catalog",
  auth: "/auth",
  library: "/library",
  seller: "/seller",
  sellerProducts: "/seller/products",
  sellerProductNew: "/seller/products/new",
  sellerPayouts: "/seller/payouts",
  becomeSeller: "/become-seller",
  adminSellerApplications: "/admin/seller-applications",
  settings: "/settings",
  checkout: (uuid) => `/checkout/${encodeURIComponent(uuid)}`,
});

export const API_PATHS = Object.freeze({
  products: "/v1/products/",
  product: (uuid) => `/v1/products/${encodeURIComponent(uuid)}/`,
  ownedProducts: "/v1/products/mine/",
  signup: "/v1/users/",
  login: "/v1/users/login/",
  purchases: "/v1/ledger/purchases/",
  ledgerOrders: "/v1/ledger/orders/",
  paymentOrders: "/v1/payments/orders/",
  paymentConfirm: "/v1/payments/confirm/",
  assetUploadTarget: "/v1/assets/upload-target/",
  assetUploadComplete: (uuid) => `/v1/assets/${encodeURIComponent(uuid)}/complete/`,
  assetDeliver: (uuid) => `/v1/assets/${encodeURIComponent(uuid)}/deliver/`,
  assetDownloadLog: (uuid) => `/v1/assets/${encodeURIComponent(uuid)}/downloads/`,
  dashboard: "/v1/dashboard/summary/",
  payouts: "/v1/payouts/",
  payoutSummary: "/v1/payouts/summary/",
  sellerApplication: "/v1/seller-applications/",
  sellerApplicationSubmit: "/v1/seller-applications/submit/",
  adminSellerApplications: "/v1/admin/seller-applications/",
  adminSellerApplicationAction: (uuid, action) => `/v1/admin/seller-applications/${encodeURIComponent(uuid)}/${action}/`,
});

export const COPY = Object.freeze({
  authTitle: "A calmer way to find useful digital work.",
  authBody: "Sign in to keep your library close, or create a customer account to start exploring.",
  emptyProducts: "Nothing has been published here yet.",
  genericError: "Something went wrong. Please try again.",
});
