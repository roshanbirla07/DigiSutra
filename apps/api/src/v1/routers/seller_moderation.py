from controllers.seller_moderation import SellerActivate, SellerSuspension


class SellerModerationRoutes(object):
    @staticmethod
    def router():
        from v1.routers.routes import v1
        v1.add_url_rule("moderation/sellers/<string:user_uuid>/suspend/", view_func=SellerSuspension.as_view("seller_suspend"), methods=["POST"], endpoint="should_be_v1_only_seller_suspend")
        v1.add_url_rule("moderation/sellers/<string:user_uuid>/activate/", view_func=SellerActivate.as_view("seller_activate"), methods=["POST"], endpoint="should_be_v1_only_seller_activate")
