import json
import logging

from flask import g, Response, request
from flask.views import View

from serializers.payoutSerializers import PayoutSerializer
from utils.auth import require_auth
from utils.user import schema_validation


class PayoutCollection(View):
    methods = ["GET", "POST"]

    @require_auth(roles=["seller", "admin"], methods=["GET", "POST"])
    @schema_validation("PayoutCreate", methods=["POST"])
    def dispatch_request(self, *args, **kwargs):
        if request.method == "POST":
            payload = request.get_json(silent=True) or {}
            user = getattr(g, "user", None)
            if str(user.user_type).lower() == "seller":
                payload["seller_uuid"] = user.uuid
            serializer = PayoutSerializer(payload)
            try:
                payout = serializer.create()
            except Exception as e:
                logging.error(f"Payout create error :: {e} :: {payload}")
                return Response(
                    response=json.dumps({"error": f"Error creating payout {str(e)}"}),
                    status=400,
                    mimetype="application/json",
                )

            return Response(
                response=json.dumps(serializer.serialize_payout(payout)),
                status=201,
                mimetype="application/json",
            )

        serializer = PayoutSerializer()
        user = getattr(g, "user", None)
        seller_id = None if str(user.user_type).lower() == "admin" else user.id
        payouts = serializer.list_payouts(seller_id=seller_id)
        return Response(
            response=json.dumps([serializer.serialize_payout(payout) for payout in payouts]),
            status=200,
            mimetype="application/json",
        )


class PayoutBatch(View):
    methods = ["POST"]

    @require_auth(roles=["admin"], methods=["POST"])
    @schema_validation("PayoutBatchProcess", methods=["POST"])
    def dispatch_request(self, *args, **kwargs):
        payload = request.get_json(silent=True) or {}
        serializer = PayoutSerializer(payload)
        try:
            payouts = serializer.process_batch(payload.get("batch_id"), payload.get("payout_updates") or [])
        except Exception as e:
            logging.error(f"Payout batch error :: {e} :: {payload}")
            return Response(
                response=json.dumps({"error": f"Error processing payout batch {str(e)}"}),
                status=400,
                mimetype="application/json",
            )

        return Response(
            response=json.dumps([serializer.serialize_payout(payout) for payout in payouts]),
            status=200,
            mimetype="application/json",
        )


class PayoutRetry(View):
    methods = ["POST"]

    @require_auth(roles=["admin"], methods=["POST"])
    def dispatch_request(self, payout_uuid, *args, **kwargs):
        serializer = PayoutSerializer()
        try:
            payout = serializer.retry_payout(payout_uuid)
        except Exception as e:
            logging.error(f"Payout retry error :: {e} :: {payout_uuid}")
            return Response(
                response=json.dumps({"error": f"Error retrying payout {str(e)}"}),
                status=400,
                mimetype="application/json",
            )

        return Response(
            response=json.dumps(serializer.serialize_payout(payout)),
            status=200,
            mimetype="application/json",
        )


class PayoutReconciliationSummary(View):
    methods = ["GET"]

    @require_auth(roles=["admin"], methods=["GET"])
    def dispatch_request(self, *args, **kwargs):
        serializer = PayoutSerializer()
        try:
            summary = serializer.reconciliation_summary()
        except Exception as e:
            logging.error(f"Payout reconciliation summary error :: {e}")
            return Response(
                response=json.dumps({"error": f"Error loading payout reconciliation summary {str(e)}"}),
                status=400,
                mimetype="application/json",
            )

        return Response(
            response=json.dumps(summary),
            status=200,
            mimetype="application/json",
        )
