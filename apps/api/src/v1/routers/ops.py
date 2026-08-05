from controllers.ops import OpsReconciliationSummary


class OpsRoutes(object):
    @staticmethod
    def router():
        from v1.routers.routes import v1

        v1.add_url_rule(
            "ops/reconciliation-summary/",
            view_func=OpsReconciliationSummary.as_view("ops_reconciliation_summary"),
            methods=["GET"],
            endpoint="should_be_v1_only_ops_reconciliation_summary",
        )
