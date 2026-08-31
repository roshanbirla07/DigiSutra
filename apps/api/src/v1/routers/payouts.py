from controllers.payout import (
    PayoutBatch,
    PayoutCancel,
    PayoutCollection,
    PayoutReconciliationSummary,
    PayoutRetry,
    PayoutSummary,
)


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
        v1.add_url_rule(
            "payouts/summary/",
            view_func=PayoutSummary.as_view("payout_summary"),
            methods=["GET"],
            endpoint="should_be_v1_only_payout_summary",
        )
        v1.add_url_rule(
            "payouts/batch/",
            view_func=PayoutBatch.as_view("payout_batch"),
            methods=["POST"],
            endpoint="should_be_v1_only_payout_batch",
        )
        v1.add_url_rule(
            "payouts/<string:payout_uuid>/retry/",
            view_func=PayoutRetry.as_view("payout_retry"),
            methods=["POST"],
            endpoint="should_be_v1_only_payout_retry",
        )
        v1.add_url_rule(
            "payouts/<string:payout_uuid>/cancel/",
            view_func=PayoutCancel.as_view("payout_cancel"),
            methods=["POST"],
            endpoint="should_be_v1_only_payout_cancel",
        )
        v1.add_url_rule(
            "payouts/reconciliation-summary/",
            view_func=PayoutReconciliationSummary.as_view("payout_reconciliation_summary"),
            methods=["GET"],
            endpoint="should_be_v1_only_payout_reconciliation_summary",
        )
