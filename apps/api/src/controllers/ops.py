import json
import logging

from flask import Response
from flask.views import View

from serializers.opsSerializers import OpsSerializer
from utils.auth import require_auth


class OpsReconciliationSummary(View):
    methods = ["GET"]

    @require_auth(roles=["admin"], methods=["GET"])
    def dispatch_request(self, *args, **kwargs):
        serializer = OpsSerializer()
        try:
            summary = serializer.summary()
        except Exception as e:
            logging.error(f"Ops reconciliation summary error :: {e}")
            return Response(
                response=json.dumps({"error": f"Error loading reconciliation summary {str(e)}"}),
                status=400,
                mimetype="application/json",
            )
        return Response(
            response=json.dumps(summary),
            status=200,
            mimetype="application/json",
        )
