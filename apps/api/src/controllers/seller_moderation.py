import json
import logging

from flask import Response, request
from flask.views import View

from serializers.sellerSerializers import SellerApplicationSerializer
from utils.auth import require_auth


class SellerSuspension(View):
    methods = ["POST"]
    suspended = True

    @require_auth(roles=["admin"], methods=["POST"])
    def dispatch_request(self, user_uuid, *args, **kwargs):
        try:
            profile = SellerApplicationSerializer.set_suspension(user_uuid, self.suspended, (request.get_json(silent=True) or {}).get("note"))
            return Response(response=json.dumps(SellerApplicationSerializer.serialize_profile(profile)), status=200, mimetype="application/json")
        except Exception as exc:
            logging.error("Seller suspension error :: %s", exc)
            return Response(response=json.dumps({"error": str(exc)}), status=400, mimetype="application/json")


class SellerActivate(SellerSuspension):
    suspended = False
