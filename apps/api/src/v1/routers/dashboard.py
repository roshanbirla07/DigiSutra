from controllers.dashboard import DashboardSummary


class DashboardRoutes(object):
    @staticmethod
    def router():
        from v1.routers.routes import v1

        v1.add_url_rule(
            "dashboard/summary/",
            view_func=DashboardSummary.as_view("dashboard_summary"),
            methods=["GET"],
            endpoint="should_be_v1_only_dashboard_summary",
        )
