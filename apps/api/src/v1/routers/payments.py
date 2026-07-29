from controllers.payment import PaymentConfirm, PaymentOrderCollection, PaymentWebhook


class PaymentRoutes(object):
    @staticmethod
    def router():
        from v1.routers.routes import v1

        v1.add_url_rule(
            "payments/orders/",
            view_func=PaymentOrderCollection.as_view("payment_order_collection"),
            methods=["POST"],
            endpoint="should_be_v1_only_payment_order_collection",
        )
        v1.add_url_rule(
            "payments/confirm/",
            view_func=PaymentConfirm.as_view("payment_confirm"),
            methods=["POST"],
            endpoint="should_be_v1_only_payment_confirm",
        )
        v1.add_url_rule(
            "payments/webhook/razorpay/",
            view_func=PaymentWebhook.as_view("payment_webhook"),
            methods=["POST"],
            endpoint="should_be_v1_only_payment_webhook",
        )
