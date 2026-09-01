from controllers.product import (
    OwnedProductCollection,
    ProductCollection,
    ProductDetail,
    ProductPreviewUploadComplete,
    ProductPreviewUploadTarget,
)


class ProductRoutes(object):
    @staticmethod
    def router():
        from v1.routers.routes import v1

        v1.add_url_rule(
            "products/mine/",
            view_func=OwnedProductCollection.as_view("owned_products_collection"),
            methods=["GET"],
            endpoint="should_be_v1_only_owned_products_collection",
        )
        v1.add_url_rule(
            "products/",
            view_func=ProductCollection.as_view("products_collection"),
            methods=["GET", "POST"],
            endpoint="should_be_v1_only_products_collection",
        )
        v1.add_url_rule(
            "products/<string:product_uuid>/",
            view_func=ProductDetail.as_view("product_detail"),
            methods=["GET", "DELETE"],
            endpoint="should_be_v1_only_product_detail",
        )
        v1.add_url_rule(
            "products/<string:product_uuid>/preview-upload-target/",
            view_func=ProductPreviewUploadTarget.as_view("product_preview_upload_target"),
            methods=["POST"],
            endpoint="should_be_v1_only_product_preview_upload_target",
        )
        v1.add_url_rule(
            "products/<string:product_uuid>/preview-complete/",
            view_func=ProductPreviewUploadComplete.as_view("product_preview_upload_complete"),
            methods=["POST"],
            endpoint="should_be_v1_only_product_preview_upload_complete",
        )
