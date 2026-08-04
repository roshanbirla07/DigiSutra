import json
import logging

from flask import Response, request
from flask.views import View

from serializers.payoutSerializers import PayoutSerializer
from utils.user import schema_validation


class PayoutCollection(View):
    methods = ["GET", "POST"]

    @schema_validation("PayoutCreate", methods=["POST"])
    def dispatch_request(self, *args, **kwargs):
        if request.method == "POST":
            payload = request.get_json(silent=True) or {}
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
        payouts = serializer.list_payouts()
        return Response(
            response=json.dumps([serializer.serialize_payout(payout) for payout in payouts]),
            status=200,
            mimetype="application/json",
        )


class PayoutBatch(View):
    methods = ["POST"]

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
