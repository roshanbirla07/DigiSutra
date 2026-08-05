import json
import logging

from flask import Response, g
from flask.views import View

from serializers.dashboardSerializers import DashboardSerializer
from utils.auth import require_auth


class DashboardSummary(View):
    methods = ["GET"]

    @require_auth(roles=["seller", "admin"], methods=["GET"])
    def dispatch_request(self, *args, **kwargs):
        serializer = DashboardSerializer()
        user = getattr(g, "user", None)
        try:
            summary = serializer.admin_summary() if user.user_type == "admin" else serializer.seller_summary(user.id)
        except Exception as e:
            logging.error(f"Dashboard summary error :: {e} :: {user.uuid if user else None}")
            return Response(
                response=json.dumps({"error": f"Error loading dashboard summary {str(e)}"}),
                status=400,
                mimetype="application/json",
            )
        return Response(
            response=json.dumps(summary),
            status=200,
            mimetype="application/json",
        )
