from controllers.support import (
    ProductFlagCollection,
    ProductFlagResolve,
    SupportTicketCollection,
    SupportTicketResolve,
    UserActivate,
    UserSuspend,
)


class SupportRoutes(object):
    @staticmethod
    def router():
        from v1.routers.routes import v1

        v1.add_url_rule(
            "support/tickets/",
            view_func=SupportTicketCollection.as_view("support_ticket_collection"),
            methods=["GET", "POST"],
            endpoint="should_be_v1_only_support_ticket_collection",
        )
        v1.add_url_rule(
            "support/tickets/<string:ticket_uuid>/resolve/",
            view_func=SupportTicketResolve.as_view("support_ticket_resolve"),
            methods=["POST"],
            endpoint="should_be_v1_only_support_ticket_resolve",
        )
        v1.add_url_rule(
            "moderation/products/<string:product_uuid>/flags/",
            view_func=ProductFlagCollection.as_view("product_flag_collection"),
            methods=["POST"],
            endpoint="should_be_v1_only_product_flag_collection",
        )
        v1.add_url_rule(
            "moderation/product-flags/<string:flag_uuid>/resolve/",
            view_func=ProductFlagResolve.as_view("product_flag_resolve"),
            methods=["POST"],
            endpoint="should_be_v1_only_product_flag_resolve",
        )
        v1.add_url_rule(
            "moderation/users/<string:user_uuid>/suspend/",
            view_func=UserSuspend.as_view("user_suspend"),
            methods=["POST"],
            endpoint="should_be_v1_only_user_suspend",
        )
        v1.add_url_rule(
            "moderation/users/<string:user_uuid>/activate/",
            view_func=UserActivate.as_view("user_activate"),
            methods=["POST"],
            endpoint="should_be_v1_only_user_activate",
        )
