from controllers.product import ProductCollection, ProductDetail


class ProductRoutes(object):
    @staticmethod
    def router():
        from v1.routers.routes import v1

        v1.add_url_rule(
            "products/",
            view_func=ProductCollection.as_view("products_collection"),
            methods=["GET", "POST"],
            endpoint="should_be_v1_only_products_collection",
        )
        v1.add_url_rule(
            "products/<string:product_uuid>/",
            view_func=ProductDetail.as_view("product_detail"),
            methods=["GET"],
            endpoint="should_be_v1_only_product_detail",
        )
