from controllers.seller import (
    AdminSellerApplicationApprove,
    AdminSellerApplicationCollection,
    AdminSellerApplicationDetail,
    AdminSellerApplicationReject,
    AdminSellerApplicationRequestInformation,
    SellerApplicationCollection,
    SellerApplicationSubmit,
    SellerApplicationWithdraw,
)


class SellerRoutes(object):
    @staticmethod
    def router():
        from v1.routers.routes import v1

        v1.add_url_rule(
            "seller-applications/",
            view_func=SellerApplicationCollection.as_view("seller_application_collection"),
            methods=["GET", "POST", "PATCH"],
            endpoint="should_be_v1_only_seller_application_collection",
        )
        v1.add_url_rule(
            "seller-applications/submit/",
            view_func=SellerApplicationSubmit.as_view("seller_application_submit"),
            methods=["POST"],
            endpoint="should_be_v1_only_seller_application_submit",
        )
        v1.add_url_rule(
            "seller-applications/<string:application_uuid>/withdraw/",
            view_func=SellerApplicationWithdraw.as_view("seller_application_withdraw"),
            methods=["POST"],
            endpoint="should_be_v1_only_seller_application_withdraw",
        )
        v1.add_url_rule(
            "admin/seller-applications/",
            view_func=AdminSellerApplicationCollection.as_view("admin_seller_application_collection"),
            methods=["GET"],
            endpoint="should_be_v1_only_admin_seller_application_collection",
        )
        v1.add_url_rule(
            "admin/seller-applications/<string:application_uuid>/",
            view_func=AdminSellerApplicationDetail.as_view("admin_seller_application_detail"),
            methods=["GET"],
            endpoint="should_be_v1_only_admin_seller_application_detail",
        )
        v1.add_url_rule(
            "admin/seller-applications/<string:application_uuid>/request-information/",
            view_func=AdminSellerApplicationRequestInformation.as_view("admin_seller_application_request_information"),
            methods=["POST"],
            endpoint="should_be_v1_only_admin_seller_application_request_information",
        )
        v1.add_url_rule(
            "admin/seller-applications/<string:application_uuid>/reject/",
            view_func=AdminSellerApplicationReject.as_view("admin_seller_application_reject"),
            methods=["POST"],
            endpoint="should_be_v1_only_admin_seller_application_reject",
        )
        v1.add_url_rule(
            "admin/seller-applications/<string:application_uuid>/approve/",
            view_func=AdminSellerApplicationApprove.as_view("admin_seller_application_approve"),
            methods=["POST"],
            endpoint="should_be_v1_only_admin_seller_application_approve",
        )
