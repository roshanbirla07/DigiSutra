import json

import logging

from flask import Response, request
from flask.views import View

from serializers.ledgerSerializers import LedgerSerializer
from utils.user import schema_validation


class LedgerCollection(View):
    methods = ["GET", "POST"]

    @schema_validation("LedgerOrderCreate", methods=["POST"])
    def dispatch_request(self, *args, **kwargs):
        if request.method == "POST":
            payload = request.get_json(silent=True) or {}
            serializer = LedgerSerializer(payload)
            try:
                order = serializer.create()
            except Exception as e:
                logging.error(f"Ledger order create error :: {e} :: {payload}")
                return Response(
                    response=json.dumps({"error": f"Error creating ledger order {str(e)}"}),
                    status=400,
                    mimetype="application/json",
                )

            return Response(
                response=json.dumps(serializer.serialize_order(order)),
                status=201,
                mimetype="application/json",
            )

        serializer = LedgerSerializer()
        orders = serializer.list_orders()
        return Response(
            response=json.dumps([serializer.serialize_order(order) for order in orders]),
            status=200,
            mimetype="application/json",
        )


class LedgerDetail(View):
    methods = ["GET"]

    def dispatch_request(self, order_uuid, *args, **kwargs):
        serializer = LedgerSerializer()
        try:
            order = serializer.get_by_uuid(order_uuid)
        except Exception as e:
            return Response(
                response=json.dumps({"error": str(e)}),
                status=404,
                mimetype="application/json",
            )

        return Response(
            response=json.dumps(serializer.serialize_order(order)),
            status=200,
            mimetype="application/json",
        )
