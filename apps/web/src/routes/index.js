export function getRoutes(controllers) {
  return [
    { path: "/auth", screen: "auth", title: "Sign In", enter: controllers.authController?.enterAuth },
    { path: "/dashboard", screen: "dashboard", view: "homeView", title: "Dashboard", enter: controllers.dashboardController?.enterDashboard },
    { path: "/product", screen: "dashboard", view: "addProductView", title: "Product", enter: controllers.productController?.enterProduct },
    { path: "/products", screen: "dashboard", view: "productsView", title: "Product List", enter: controllers.productController?.enterProductList },
    { path: "/settings", screen: "dashboard", view: "settingsView", title: "Settings", enter: controllers.settingsController?.enterSettings },
  ];
}

export function resolveRoute(path, routes) {
  return routes.find((route) => route.path === path) || routes.find((route) => route.path === "/dashboard");
}
