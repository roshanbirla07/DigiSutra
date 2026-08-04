from controllers.payout import PayoutCollection


class PayoutRoutes(object):
    @staticmethod
    def router():
        from v1.routers.routes import v1

        v1.add_url_rule(
            "payouts/",
            view_func=PayoutCollection.as_view("payout_collection"),
            methods=["GET", "POST"],
            endpoint="should_be_v1_only_payout_collection",
        )
