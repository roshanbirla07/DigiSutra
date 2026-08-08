from controllers.ledger import BuyerPurchaseHistory, InvoiceDetail, LedgerCollection, LedgerDetail


class LedgerRoutes(object):
    @staticmethod
    def router():
        from v1.routers.routes import v1

        v1.add_url_rule(
            "ledger/orders/",
            view_func=LedgerCollection.as_view("ledger_collection"),
            methods=["GET", "POST"],
            endpoint="should_be_v1_only_ledger_collection",
        )
        v1.add_url_rule(
            "ledger/purchases/",
            view_func=BuyerPurchaseHistory.as_view("buyer_purchase_history"),
            methods=["GET"],
            endpoint="should_be_v1_only_buyer_purchase_history",
        )
        v1.add_url_rule(
            "ledger/orders/<string:order_uuid>/invoice/",
            view_func=InvoiceDetail.as_view("invoice_detail"),
            methods=["GET"],
            endpoint="should_be_v1_only_invoice_detail",
        )
        v1.add_url_rule(
            "ledger/orders/<string:order_uuid>/",
            view_func=LedgerDetail.as_view("ledger_detail"),
            methods=["GET", "POST"],
            endpoint="should_be_v1_only_ledger_detail",
        )
